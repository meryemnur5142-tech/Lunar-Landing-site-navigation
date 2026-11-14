"""
Environmental domain models for LUNA-AI.

Covers terrain analysis products derived from LOLA DEM, illumination time
series, Permanently Shadowed Region (PSR) boundary polygons, and the
container that bundles all environmental data for a given region of interest.

All products carry :class:`DataProductMetadata` to satisfy the
*uncertainty visible* design principle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal, Optional, Tuple

import numpy as np

from domain.crater.models import DataProductMetadata

__all__ = [
    "BoundingBox",
    "TerrainProduct",
    "IlluminationTimeSeries",
    "PSRBoundary",
    "EnvironmentalDataProduct",
]


@dataclass
class BoundingBox:
    """Geographic bounding box in areocentric lat/lon (degrees, IAU_MOON_2015).

    Attributes:
        min_lat: Southern boundary latitude (degrees, -90 to +90).
        max_lat: Northern boundary latitude (degrees, -90 to +90).
        min_lon: Western boundary longitude (degrees, 0 to 360).
        max_lon: Eastern boundary longitude (degrees, 0 to 360).
    """

    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float

    def __post_init__(self) -> None:
        if self.min_lat >= self.max_lat:
            raise ValueError(
                f"min_lat ({self.min_lat}) must be less than max_lat ({self.max_lat})"
            )
        if self.min_lon >= self.max_lon:
            raise ValueError(
                f"min_lon ({self.min_lon}) must be less than max_lon ({self.max_lon})"
            )

    @property
    def center_lat(self) -> float:
        """Centre latitude of the bounding box."""
        return (self.min_lat + self.max_lat) / 2.0

    @property
    def center_lon(self) -> float:
        """Centre longitude of the bounding box."""
        return (self.min_lon + self.max_lon) / 2.0


@dataclass
class TerrainProduct:
    """Raster terrain analysis product derived from LOLA DEM.

    The ``data`` array is a 2-D NumPy grid aligned with ``extent``.
    Row index 0 corresponds to ``extent.max_lat`` (north-up convention).

    Attributes:
        product_id: Unique identifier for this product instance.
        product_type: One of ``slope_map``, ``roughness_map``,
                      ``hazard_map``, or ``psr_boundaries``.
        data: 2-D NumPy array of float32 values.
        extent: Lat/lon bounding box covered by the raster.
        metadata: Provenance and quality metadata.
    """

    product_id: str
    product_type: Literal["slope_map", "roughness_map", "hazard_map", "psr_boundaries"]
    data: np.ndarray  # 2-D float32 grid
    extent: BoundingBox
    metadata: DataProductMetadata

    def __post_init__(self) -> None:
        if self.data.ndim != 2:
            raise ValueError(
                f"data must be a 2-D array, got shape {self.data.shape}"
            )

    @property
    def shape(self) -> Tuple[int, int]:
        """(rows, cols) of the data array."""
        return self.data.shape  # type: ignore[return-value]


@dataclass
class IlluminationTimeSeries:
    """Per-pixel illumination time series for a geographic point.

    Used to characterise solar access for energy planning and to identify
    PSR candidates.  Applies to both historical reconstructions and future
    ephemeris predictions.

    Attributes:
        pixel_lat: Areocentric latitude of the pixel centre (degrees).
        pixel_lon: Areocentric east longitude of the pixel centre (degrees).
        timestamps: Ordered list of UTC observation/prediction times.
        illumination_fraction: Corresponding illumination values in [0.0, 1.0].
                               0.0 = fully shadowed, 1.0 = fully illuminated.
        is_historical: True if the series is reconstructed from past observations;
                       False if it is a future ephemeris prediction.
        metadata: Provenance and quality metadata.
    """

    pixel_lat: float
    pixel_lon: float
    timestamps: List[datetime]
    illumination_fraction: List[float]  # 0.0 (full shadow) – 1.0 (full illumination)
    is_historical: bool
    metadata: DataProductMetadata

    def __post_init__(self) -> None:
        if len(self.timestamps) != len(self.illumination_fraction):
            raise ValueError(
                "timestamps and illumination_fraction must have equal length"
            )
        for val in self.illumination_fraction:
            if not (0.0 <= val <= 1.0):
                raise ValueError(
                    f"illumination_fraction values must be in [0.0, 1.0], got {val}"
                )


@dataclass
class PSRBoundary:
    """Polygon delineating a Permanently Shadowed Region (PSR).

    PSR boundaries are derived from ShadowCam imagery and illumination
    modelling.  Confidence reflects the fraction of independent observations
    consistent with permanent shadowing.

    Attributes:
        psr_id: Unique PSR identifier.
        crater_id: Identifier of the parent crater, if applicable.
        polygon_vertices: Ordered list of (lat, lon) tuples forming a closed
                          polygon (IAU_MOON_2015, degrees).
        area_km2: Area enclosed by the polygon in square kilometres.
        confidence_level: Confidence in permanent-shadow classification [0.0, 1.0].
        metadata: Provenance and quality metadata.
    """

    psr_id: str
    polygon_vertices: List[Tuple[float, float]]  # (lat, lon) pairs
    area_km2: float
    confidence_level: float  # 0.0 – 1.0
    metadata: DataProductMetadata
    crater_id: Optional[str] = None

    def __post_init__(self) -> None:
        if len(self.polygon_vertices) < 3:
            raise ValueError(
                f"A polygon requires at least 3 vertices, got {len(self.polygon_vertices)}"
            )
        if not (0.0 <= self.confidence_level <= 1.0):
            raise ValueError(
                f"confidence_level must be in [0.0, 1.0], got {self.confidence_level}"
            )
        if self.area_km2 <= 0:
            raise ValueError(f"area_km2 must be positive, got {self.area_km2}")


@dataclass
class EnvironmentalDataProduct:
    """Container bundling all environmental analysis products for a region.

    Fields are optional because not every pipeline stage produces all
    products.  Callers should check for ``None`` before consuming a product.

    Attributes:
        terrain: Slope/roughness/hazard raster for the region of interest.
        illumination: Illumination time series for a representative pixel.
        psr_boundaries: List of PSR boundary polygons (may be empty).
        surface_temperature: Temperature raster derived from Diviner/LRO data.
                             TBD: instrument thermal model integration pending.
    """

    psr_boundaries: List[PSRBoundary] = field(default_factory=list)
    terrain: Optional[TerrainProduct] = None
    illumination: Optional[IlluminationTimeSeries] = None
    # TBD: Diviner surface temperature integration pending instrument thermal model
    surface_temperature: Optional[TerrainProduct] = None
