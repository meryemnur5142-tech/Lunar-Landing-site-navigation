"""
Base ingestor and concrete planetary data source adapters for LUNA-AI.

Every planetary data product that enters the pipeline is acquired through a
subclass of :class:`BaseIngestor`.  The base class enforces the contract:

1. **fetch** — download raw data from an external source to a local path.
2. **normalize** — reproject / reformat to IAU_MOON_2015 CRS, attach
   :class:`~domain.crater.models.DataProductMetadata`.
3. **ingest** — orchestrate fetch + normalize + provenance recording.

Concrete ingestors:
- :class:`LOLAIngestor` — LOLA DEM via the ODE REST API (TBD).
- :class:`ShadowCamIngestor` — ShadowCam PSR imagery via PDS4 API (TBD).

.. note::
    External API integrations are marked ``NotImplementedError`` / TODO.
    They will be implemented once API credentials and endpoint specs are
    confirmed with the data-engineering team.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from domain.crater.models import DataProductMetadata
from domain.environment.models import BoundingBox, TerrainProduct

__all__ = ["BaseIngestor", "LOLAIngestor", "ShadowCamIngestor"]

logger = logging.getLogger(__name__)


class BaseIngestor(ABC):
    """Abstract base class for all planetary data source ingestors.

    Subclasses must override :meth:`fetch` and :meth:`normalize`.
    The :meth:`ingest` template method orchestrates the full pipeline and
    records provenance automatically.

    Class attributes:
        SOURCE_NAME: Short, human-readable identifier for the data source.
                     Subclasses must override this.

    Example::

        ingestor = LOLAIngestor()
        product = ingestor.ingest(
            BoundingBox(min_lat=-86, max_lat=-84, min_lon=350, max_lon=5)
        )
    """

    SOURCE_NAME: str = ""  # subclass must override

    def __init__(self) -> None:
        if not self.SOURCE_NAME:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define SOURCE_NAME"
            )
        self._provenance_log: list[dict] = []

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def fetch(self, region: BoundingBox, **kwargs) -> Path:
        """Download raw data for *region* to a local temporary file.

        Args:
            region: Geographic bounding box of the area of interest.
            **kwargs: Source-specific parameters (resolution, epoch, etc.).

        Returns:
            Path to the downloaded raw file.
        """
        ...

    @abstractmethod
    def normalize(self, raw_path: Path) -> TerrainProduct:
        """Reproject/reformat *raw_path* to IAU_MOON_2015 CRS.

        Implementations must:
        - Reproject to IAU_MOON_2015 if the input uses a different CRS.
        - Convert to float32 NumPy array.
        - Populate :class:`~domain.crater.models.DataProductMetadata`.

        Args:
            raw_path: Path to the raw file returned by :meth:`fetch`.

        Returns:
            A fully populated :class:`~domain.environment.models.TerrainProduct`.
        """
        ...

    # ------------------------------------------------------------------
    # Template method
    # ------------------------------------------------------------------

    def ingest(self, region: BoundingBox, **kwargs) -> TerrainProduct:
        """Full ingest pipeline: fetch → normalize → record provenance.

        Args:
            region: Geographic bounding box.
            **kwargs: Forwarded to :meth:`fetch`.

        Returns:
            Normalised :class:`~domain.environment.models.TerrainProduct`.
        """
        logger.info(
            "[%s] Starting ingest for region %s", self.SOURCE_NAME, region
        )
        raw_path = self.fetch(region, **kwargs)
        logger.debug("[%s] Raw data at %s", self.SOURCE_NAME, raw_path)

        product = self.normalize(raw_path)
        self._record_provenance(product)

        logger.info(
            "[%s] Ingest complete — product_id=%s", self.SOURCE_NAME, product.product_id
        )
        return product

    # ------------------------------------------------------------------
    # Provenance
    # ------------------------------------------------------------------

    def _record_provenance(self, product: TerrainProduct) -> None:
        """Append a provenance entry for *product* to the in-memory log.

        In production this should persist to the data-platform provenance
        store (e.g. a PostgreSQL table or an STAC-compatible JSON record).

        Args:
            product: The product whose provenance to record.
        """
        entry = {
            "product_id": product.product_id,
            "product_type": product.product_type,
            "source": self.SOURCE_NAME,
            "recorded_at": datetime.now(tz=timezone.utc).isoformat(),
            "metadata": {
                "source": product.metadata.source,
                "timestamp": product.metadata.timestamp.isoformat(),
                "crs": product.metadata.coordinate_reference_system,
                "resolution_m": product.metadata.resolution_m,
                "quality_score": product.metadata.quality_score,
                "processing_version": product.metadata.processing_version,
                "lineage": product.metadata.lineage,
            },
        }
        self._provenance_log.append(entry)
        logger.debug("[%s] Provenance recorded: %s", self.SOURCE_NAME, entry)

    @property
    def provenance_log(self) -> list[dict]:
        """Read-only view of the in-process provenance log."""
        return list(self._provenance_log)


# ---------------------------------------------------------------------------
# Concrete ingestors
# ---------------------------------------------------------------------------


class LOLAIngestor(BaseIngestor):
    """LOLA DEM ingestor via the ODE REST API.

    Data source: https://ode.rsl.wustl.edu/moon/
    Format: GeoTIFF, IAU_MOON_2015
    Coverage: Global; polar stereo for latitudes > |70°|

    Args:
        resolution_m: Default DEM resolution in metres per pixel.
                      Available: 20 m, 60 m, 240 m.

    .. note::
        TBD: ODE API endpoint authentication and query parameters.
        Implementation pending confirmation of API credentials and
        rate-limit policy.
    """

    SOURCE_NAME = "LOLA_DEM"

    def __init__(self, resolution_m: float = 20.0) -> None:
        super().__init__()
        self.default_resolution_m = resolution_m

    def fetch(self, region: BoundingBox, resolution_m: Optional[float] = None, **kwargs) -> Path:
        """Download LOLA DEM GeoTIFF for *region* from the ODE API.

        Args:
            region: Geographic bounding box.
            resolution_m: Desired resolution (default: ``self.default_resolution_m``).

        Returns:
            Path to the downloaded GeoTIFF.

        Raises:
            NotImplementedError: Until ODE API integration is complete.
        """
        # TODO: implement ODE REST API request
        # Endpoint: https://ode.rsl.wustl.edu/moon/pdsimage/...
        # Parameters: minlat, maxlat, westlon, eastlon, resolution
        raise NotImplementedError(
            "LOLA ODE API integration required — TBD: confirm API key and endpoint"
        )

    def normalize(self, raw_path: Path) -> TerrainProduct:
        """Normalize LOLA GeoTIFF to a TerrainProduct.

        Steps:
        1. Open with GDAL/rasterio.
        2. Verify CRS is IAU_MOON_2015 (EPSG:30101 or equivalent).
        3. Read band 1 as float32 NumPy array.
        4. Build DataProductMetadata from GDAL metadata tags.

        Raises:
            NotImplementedError: Until GDAL integration is complete.
        """
        # TODO: implement GDAL/rasterio normalization
        # import rasterio; with rasterio.open(raw_path) as ds: ...
        raise NotImplementedError(
            "LOLA DEM normalization not yet implemented — requires rasterio/GDAL"
        )


class ShadowCamIngestor(BaseIngestor):
    """ShadowCam PSR imagery ingestor via the PDS4 API.

    ShadowCam is a camera on KPLO (Korea Pathfinder Lunar Orbiter) designed
    to image permanently shadowed regions using reflected Earthshine.

    Data source: PDS4 archive via NASA PDS Geosciences Node
    Format: FITS or GeoTIFF
    Coverage: Polar regions, selectively targeted

    .. note::
        TBD: PDS4 search API query syntax and authentication.
        Implementation pending PDS4 API access approval.
    """

    SOURCE_NAME = "ShadowCam"

    def fetch(self, region: BoundingBox, **kwargs) -> Path:
        """Query PDS4 archive for ShadowCam images covering *region*.

        Args:
            region: Geographic bounding box.

        Returns:
            Path to the downloaded image file.

        Raises:
            NotImplementedError: Until PDS4 API integration is complete.
        """
        # TODO: implement PDS4 search query
        # Base URL: https://pds-geosciences.wustl.edu/dataserv/shadowcam/
        raise NotImplementedError(
            "ShadowCam PDS4 API integration — TBD: confirm PDS4 search endpoint"
        )

    def normalize(self, raw_path: Path) -> TerrainProduct:
        """Normalize ShadowCam imagery to a TerrainProduct (psr_boundaries type).

        Steps:
        1. Open FITS/GeoTIFF.
        2. Reproject to IAU_MOON_2015 polar stereographic.
        3. Convert to radiance float32 array.
        4. Attach quality score based on solar elongation metadata.

        Raises:
            NotImplementedError: Until FITS/GDAL integration is complete.
        """
        # TODO: implement ShadowCam normalization
        raise NotImplementedError(
            "ShadowCam normalization not yet implemented — requires astropy/GDAL"
        )
