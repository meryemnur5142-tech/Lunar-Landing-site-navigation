"""
Terrain analysis product generator for LUNA-AI.

Derives secondary terrain products from LOLA DEM rasters:
- Slope map (degrees) using the Horn (1981) gradient method.
- Surface roughness map (RMS height deviation, metres).
- Composite hazard map (dimensionless, 0 = safe, 1 = hazardous).
- PSR boundary polygons extracted from ShadowCam imagery.

Design principle: *Uncertainty visible* — every output product's metadata
carries a ``quality_score`` and ``uncertainty_1sigma`` derived from the
input DEM accuracy specifications.

All products use IAU_MOON_2015 CRS.  The lunar radius used for slope
calculations is R_MOON = 1 737 400 m (IAU 2015).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

import numpy as np

from domain.crater.models import DataProductMetadata
from domain.environment.models import PSRBoundary, TerrainProduct

__all__ = ["TerrainAnalyzer"]

logger = logging.getLogger(__name__)

# IAU 2015 mean lunar radius (metres) used to convert degrees to metres
_R_MOON_M: float = 1_737_400.0
_PROCESSING_VERSION: str = "0.1.0"


class TerrainAnalyzer:
    """Derive terrain analysis products from a LOLA DEM TerrainProduct.

    Args:
        processing_version: Version tag written into output product metadata.

    Example::

        analyzer = TerrainAnalyzer()
        slope = analyzer.compute_slope(dem)
        roughness = analyzer.compute_roughness(dem)
        hazard = analyzer.compute_hazard_map(slope, roughness)
        psrs = analyzer.extract_psr_boundaries(shadowcam)
    """

    def __init__(self, processing_version: str = _PROCESSING_VERSION) -> None:
        self.processing_version = processing_version

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute_slope(self, dem: TerrainProduct) -> TerrainProduct:
        """Compute slope map (degrees) using the Horn (1981) 3×3 gradient method.

        The slope at each pixel is arctan(sqrt(dz/dx² + dz/dy²)) where the
        horizontal distances are derived from the DEM resolution and the
        IAU 2015 lunar radius.

        Uncertainty: propagated from DEM vertical accuracy (1-sigma from
        ``dem.metadata.uncertainty_1sigma``) divided by the pixel size.

        Args:
            dem: Input DEM TerrainProduct (product_type must be a DEM).

        Returns:
            New ``TerrainProduct`` with ``product_type="slope_map"`` and
            units of degrees.
        """
        resolution_m = dem.metadata.resolution_m
        data = dem.data.astype(np.float64)

        # Pad with edge values so output shape matches input
        padded = np.pad(data, pad_width=1, mode="edge")

        # Horn (1981) finite differences
        dz_dx = (
            (padded[:-2, 2:] + 2 * padded[1:-1, 2:] + padded[2:, 2:])
            - (padded[:-2, :-2] + 2 * padded[1:-1, :-2] + padded[2:, :-2])
        ) / (8.0 * resolution_m)

        dz_dy = (
            (padded[2:, :-2] + 2 * padded[2:, 1:-1] + padded[2:, 2:])
            - (padded[:-2, :-2] + 2 * padded[:-2, 1:-1] + padded[:-2, 2:])
        ) / (8.0 * resolution_m)

        slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
        slope_deg = np.degrees(slope_rad).astype(np.float32)

        # Uncertainty: σ_slope ≈ σ_z / (pixel_size) × (1/cos²(slope))
        sigma_z = dem.metadata.uncertainty_1sigma or (resolution_m * 0.01)
        sigma_slope_deg = float(np.degrees(sigma_z / resolution_m))

        metadata = self._derived_metadata(
            source_meta=dem.metadata,
            product_id_prefix="slope",
            uncertainty_1sigma=sigma_slope_deg,
        )

        logger.debug("Slope map computed — shape=%s max=%.2f°", slope_deg.shape, float(slope_deg.max()))
        return TerrainProduct(
            product_id=metadata.lineage[0].split(":")[0] if metadata.lineage else str(uuid.uuid4()),
            product_type="slope_map",
            data=slope_deg,
            extent=dem.extent,
            metadata=metadata,
        )

    def compute_roughness(
        self, dem: TerrainProduct, window_m: float = 5.0
    ) -> TerrainProduct:
        """Compute surface roughness as RMS height deviation over a sliding window.

        Roughness is defined as the RMS of height residuals after subtracting
        a local mean within a square window of side ``window_m`` metres.

        Args:
            dem: Input DEM TerrainProduct.
            window_m: Side length of the sliding window in metres.

        Returns:
            New ``TerrainProduct`` with ``product_type="roughness_map"`` and
            units of metres.
        """
        resolution_m = dem.metadata.resolution_m
        half_w = max(1, int(round(window_m / (2.0 * resolution_m))))
        data = dem.data.astype(np.float64)
        rows, cols = data.shape

        roughness = np.zeros_like(data, dtype=np.float32)
        for r in range(rows):
            r0, r1 = max(0, r - half_w), min(rows, r + half_w + 1)
            for c in range(cols):
                c0, c1 = max(0, c - half_w), min(cols, c + half_w + 1)
                patch = data[r0:r1, c0:c1]
                residuals = patch - patch.mean()
                roughness[r, c] = float(np.sqrt((residuals**2).mean()))

        sigma_z = dem.metadata.uncertainty_1sigma or (resolution_m * 0.01)
        metadata = self._derived_metadata(
            source_meta=dem.metadata,
            product_id_prefix="roughness",
            uncertainty_1sigma=sigma_z,
        )

        logger.debug(
            "Roughness map computed — shape=%s max=%.4f m", roughness.shape, float(roughness.max())
        )
        return TerrainProduct(
            product_id=str(uuid.uuid4()),
            product_type="roughness_map",
            data=roughness,
            extent=dem.extent,
            metadata=metadata,
        )

    def compute_hazard_map(
        self,
        slope: TerrainProduct,
        roughness: TerrainProduct,
        rock_map: Optional[TerrainProduct] = None,
    ) -> TerrainProduct:
        """Compute a combined terrain hazard map.

        Hazard is a linear combination of normalised slope, roughness and
        (optionally) rock abundance.  Output is in [0.0, 1.0] where 0 = safe
        and 1 = hazardous.

        Weights:
        - slope:      0.50
        - roughness:  0.30
        - rock:       0.20 (applied only if ``rock_map`` is provided)

        When ``rock_map`` is not provided the rock weight is redistributed
        proportionally and a TBD warning is added to the metadata lineage.

        Args:
            slope: Slope map TerrainProduct (degrees).
            roughness: Roughness map TerrainProduct (metres).
            rock_map: Optional rock abundance TerrainProduct ([0, 1]).

        Returns:
            New ``TerrainProduct`` with ``product_type="hazard_map"``.
        """
        # Normalise slope: 0–15 deg maps to 0–1 (above 15 = max hazard)
        slope_norm = np.clip(slope.data.astype(np.float64) / 15.0, 0.0, 1.0)
        # Normalise roughness: 0–0.5 m maps to 0–1
        rough_norm = np.clip(roughness.data.astype(np.float64) / 0.5, 0.0, 1.0)

        lineage_notes: list[str] = []

        if rock_map is not None:
            rock_norm = np.clip(rock_map.data.astype(np.float64), 0.0, 1.0)
            hazard = 0.50 * slope_norm + 0.30 * rough_norm + 0.20 * rock_norm
        else:
            # TBD: rock abundance map not yet available; redistribute weights
            hazard = 0.625 * slope_norm + 0.375 * rough_norm
            lineage_notes.append(
                "TBD: rock abundance map absent — slope/roughness weights rescaled; "
                "update when rock product is available"
            )

        hazard_f32 = hazard.astype(np.float32)
        worst_quality = min(
            slope.metadata.quality_score, roughness.metadata.quality_score
        )
        metadata = self._derived_metadata(
            source_meta=slope.metadata,
            product_id_prefix="hazard",
            quality_override=worst_quality,
            extra_lineage=lineage_notes,
        )

        logger.debug(
            "Hazard map computed — shape=%s mean_hazard=%.3f",
            hazard_f32.shape,
            float(hazard_f32.mean()),
        )
        return TerrainProduct(
            product_id=str(uuid.uuid4()),
            product_type="hazard_map",
            data=hazard_f32,
            extent=slope.extent,
            metadata=metadata,
        )

    def extract_psr_boundaries(
        self,
        shadowcam: TerrainProduct,
        confidence_threshold: float = 0.8,
    ) -> List[PSRBoundary]:
        """Extract PSR boundary polygons from a ShadowCam radiance product.

        Regions with radiance consistently below the threshold are classified
        as permanently shadowed.  Polygon extraction uses a simple connected-
        component binarisation; production use should replace this with a
        GDAL vectorisation pipeline.

        Args:
            shadowcam: ShadowCam radiance TerrainProduct (normalised [0, 1]).
            confidence_threshold: Minimum confidence level for a pixel to be
                                   classified as permanently shadowed.

        Returns:
            List of :class:`~domain.environment.models.PSRBoundary` objects.

        .. note::
            TBD: Replace binarisation with multi-epoch confidence accumulation
            once a time series of ShadowCam observations is available.
        """
        # TODO: implement connected-component labelling with scipy.ndimage
        # and GDAL vectorisation for production-quality boundary extraction.
        # For now, return an empty list as a placeholder.
        logger.warning(
            "extract_psr_boundaries: full implementation pending — returning empty list. "
            "TBD: multi-epoch ShadowCam confidence accumulation required."
        )
        return []

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _derived_metadata(
        self,
        source_meta: DataProductMetadata,
        product_id_prefix: str,
        uncertainty_1sigma: Optional[float] = None,
        quality_override: Optional[float] = None,
        extra_lineage: Optional[List[str]] = None,
    ) -> DataProductMetadata:
        """Build output metadata for a derived product.

        Args:
            source_meta: Metadata of the source (input) product.
            product_id_prefix: Short prefix for the new product_id.
            uncertainty_1sigma: Propagated 1-sigma uncertainty (metres or degrees).
            quality_override: Override quality score (defaults to source quality).
            extra_lineage: Additional lineage notes (e.g. TBD warnings).

        Returns:
            New :class:`~domain.crater.models.DataProductMetadata` instance.
        """
        lineage = list(source_meta.lineage) + [
            f"{product_id_prefix}:derived_from:{source_meta.source}"
        ]
        if extra_lineage:
            lineage.extend(extra_lineage)

        return DataProductMetadata(
            source=f"TerrainAnalyzer/{source_meta.source}",
            timestamp=datetime.now(tz=timezone.utc),
            coordinate_reference_system=source_meta.coordinate_reference_system,
            resolution_m=source_meta.resolution_m,
            quality_score=quality_override
            if quality_override is not None
            else source_meta.quality_score,
            uncertainty_1sigma=uncertainty_1sigma,
            processing_version=self.processing_version,
            lineage=lineage,
        )
