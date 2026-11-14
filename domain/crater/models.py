"""
Crater domain models for LUNA-AI.

Defines data structures for crater records, data product metadata,
landing site candidates and ranked candidates used throughout the
ground-segment analysis pipeline.

Coordinate reference: IAU_MOON_2015 (areocentric lat/lon).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

__all__ = [
    "DataProductMetadata",
    "CraterRecord",
    "LandingSiteCandidate",
    "RankedCandidate",
]


@dataclass
class DataProductMetadata:
    """Provenance and quality metadata attached to every planetary data product.

    Attributes:
        source: Originating data source name (e.g. "LOLA_DEM", "ShadowCam").
        timestamp: UTC time when this product was generated or last updated.
        coordinate_reference_system: CRS identifier, typically "IAU_MOON_2015".
        resolution_m: Native spatial resolution in metres per pixel.
        quality_score: Overall quality indicator in [0.0, 1.0]; higher is better.
        uncertainty_1sigma: 1-sigma vertical/radial uncertainty (metres), if known.
        processing_version: Version string of the processing chain (e.g. "1.3.2").
        lineage: Ordered list of source file paths or dataset identifiers.
    """

    source: str
    timestamp: datetime
    coordinate_reference_system: str  # "IAU_MOON_2015"
    resolution_m: float
    quality_score: float  # 0.0 – 1.0
    processing_version: str
    lineage: List[str] = field(default_factory=list)
    uncertainty_1sigma: Optional[float] = None

    def __post_init__(self) -> None:
        if not (0.0 <= self.quality_score <= 1.0):
            raise ValueError(
                f"quality_score must be in [0.0, 1.0], got {self.quality_score}"
            )
        if self.resolution_m <= 0:
            raise ValueError(f"resolution_m must be positive, got {self.resolution_m}")


@dataclass
class CraterRecord:
    """Catalogued lunar impact crater.

    Attributes:
        crater_id: Unique identifier (catalog-prefixed, e.g. "R2019-00042").
        name: IAU-approved name or None for unnamed craters.
        center_lat: Areocentric latitude of crater centre (degrees, -90 to +90).
        center_lon: Areocentric east longitude of crater centre (degrees, 0 to 360).
        diameter_km: Rim-to-rim diameter in kilometres.
        depth_km: Crater depth in kilometres (floor to rim), if known.
        source_catalog: Catalogue this record originates from (e.g. "Robbins2019").
        morphology: Morphological class string (e.g. "simple", "complex", "peak-ring").
        metadata: Provenance and quality information for this record.
    """

    crater_id: str
    center_lat: float
    center_lon: float
    diameter_km: float
    source_catalog: str
    metadata: DataProductMetadata
    name: Optional[str] = None
    depth_km: Optional[float] = None
    morphology: Optional[str] = None

    def __post_init__(self) -> None:
        if not (-90.0 <= self.center_lat <= 90.0):
            raise ValueError(f"center_lat out of range: {self.center_lat}")
        if not (0.0 <= self.center_lon <= 360.0):
            raise ValueError(f"center_lon out of range: {self.center_lon}")
        if self.diameter_km <= 0:
            raise ValueError(f"diameter_km must be positive: {self.diameter_km}")


@dataclass
class LandingSiteCandidate:
    """Potential landing site associated with a crater region.

    Hard constraint results are stored here after evaluation by
    :class:`mission_intelligence.constraints.hard_constraints.HardConstraintEvaluator`.
    Only candidates with ``hard_constraints_passed=True`` proceed to scoring.

    Attributes:
        candidate_id: Unique candidate identifier.
        crater: Parent crater record.
        landing_ellipse_center_lat: Centre latitude of the 3-sigma landing ellipse.
        landing_ellipse_center_lon: Centre longitude of the 3-sigma landing ellipse.
        landing_ellipse_semi_major_m: Semi-major axis of the landing ellipse (metres).
        landing_ellipse_semi_minor_m: Semi-minor axis of the landing ellipse (metres).
        max_slope_deg: Maximum terrain slope within the landing ellipse (degrees).
        roughness_rms_m: RMS surface roughness within the landing ellipse (metres).
        rock_abundance: Fractional rock coverage in [0.0, 1.0].
        psr_access_fraction: Fraction of the landing ellipse overlapping a PSR.
        hard_constraints_passed: True if all hard constraints are satisfied, else False.
                                  None means evaluation has not been run yet.
        rejection_reason: Textual reason when hard_constraints_passed is False.
        metadata: Provenance metadata for this candidate record.
    """

    candidate_id: str
    crater: CraterRecord
    landing_ellipse_center_lat: float
    landing_ellipse_center_lon: float
    landing_ellipse_semi_major_m: float
    landing_ellipse_semi_minor_m: float
    max_slope_deg: float
    roughness_rms_m: float
    rock_abundance: float  # 0.0 – 1.0
    psr_access_fraction: float  # fraction of ellipse overlapping PSR
    metadata: DataProductMetadata
    hard_constraints_passed: Optional[bool] = None
    rejection_reason: Optional[str] = None

    def __post_init__(self) -> None:
        if not (0.0 <= self.rock_abundance <= 1.0):
            raise ValueError(
                f"rock_abundance must be in [0.0, 1.0], got {self.rock_abundance}"
            )
        if not (0.0 <= self.psr_access_fraction <= 1.0):
            raise ValueError(
                f"psr_access_fraction must be in [0.0, 1.0], got {self.psr_access_fraction}"
            )
        if self.max_slope_deg < 0:
            raise ValueError(f"max_slope_deg must be non-negative: {self.max_slope_deg}")
        if self.roughness_rms_m < 0:
            raise ValueError(
                f"roughness_rms_m must be non-negative: {self.roughness_rms_m}"
            )


@dataclass
class RankedCandidate:
    """Scored and ranked landing site candidate.

    All component scores are in [0.0, 1.0]; higher values are better.
    ``score_uncertainty`` expresses the propagated uncertainty of ``total_score``
    (1-sigma), keeping the *uncertainty visible* design principle.

    Attributes:
        candidate: The underlying landing site candidate (must have passed hard
                   constraints before ranking).
        science_score: Science value component (PSR access, instrument coverage).
        energy_score: Energy margin component (illumination, solar generation).
        thermal_score: Thermal safety component (PSR dark exposure tolerance).
        communication_score: Communication geometry component (Earth visibility).
        risk_score: Risk component (hazard density, data quality, PSR edge uncertainty).
        total_score: Weighted sum of component scores.
        score_uncertainty: 1-sigma uncertainty on total_score (uncertainty visible).
    """

    candidate: LandingSiteCandidate
    science_score: float
    energy_score: float
    thermal_score: float
    communication_score: float
    risk_score: float
    total_score: float
    score_uncertainty: float  # 1-sigma; uncertainty visible

    def __post_init__(self) -> None:
        for attr in (
            "science_score",
            "energy_score",
            "thermal_score",
            "communication_score",
            "risk_score",
            "total_score",
        ):
            val = getattr(self, attr)
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"{attr} must be in [0.0, 1.0], got {val}")
        if self.score_uncertainty < 0:
            raise ValueError(
                f"score_uncertainty must be non-negative: {self.score_uncertainty}"
            )
