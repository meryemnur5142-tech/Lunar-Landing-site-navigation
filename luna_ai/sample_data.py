"""
Estimated lunar south pole candidate sites based on published orbital data.

Values are representative estimates derived from:
  - LROC WAC/NAC slope maps (Kreslavsky & Head 2013)
  - LOLA illumination models (Mazarico et al. 2011)
  - Mini-RF PSR mapping (Spudis et al. 2013)
  - Published rock abundance surveys (Bandfield et al. 2011)

These are NOT flight-qualified parameters. Use only for pipeline validation.
"""

from __future__ import annotations

from datetime import datetime, timezone

from domain.crater.models import CraterRecord, DataProductMetadata, LandingSiteCandidate


def _meta(source: str = "ESTIMATED") -> DataProductMetadata:
    return DataProductMetadata(
        source=source,
        timestamp=datetime(2027, 1, 1, tzinfo=timezone.utc),
        coordinate_reference_system="IAU_MOON_2015",
        resolution_m=20.0,
        quality_score=0.75,
        processing_version="estimated-v1",
        uncertainty_1sigma=0.15,
    )


def _crater(cid: str, name: str, lat: float, lon: float, diam_km: float) -> CraterRecord:
    return CraterRecord(
        crater_id=cid,
        name=name,
        center_lat=lat,
        center_lon=lon,
        diameter_km=diam_km,
        source_catalog="Robbins2019",
        metadata=_meta(),
    )


# ---------------------------------------------------------------------------
# Five representative south-pole landing site candidates
# ---------------------------------------------------------------------------

CANDIDATES: list[LandingSiteCandidate] = [
    # Shackleton rim — high PSR access, moderate slope
    LandingSiteCandidate(
        candidate_id="SP-001",
        crater=_crater("R-00001", "Shackleton", -89.9, 0.0, 21.0),
        landing_ellipse_center_lat=-89.67,
        landing_ellipse_center_lon=129.0,
        landing_ellipse_semi_major_m=500.0,
        landing_ellipse_semi_minor_m=250.0,
        max_slope_deg=12.5,
        roughness_rms_m=0.28,
        rock_abundance=0.11,
        psr_access_fraction=0.82,    # very high PSR access (key science target)
        metadata=_meta("LROC-estimated"),
    ),
    # Haworth — flat terrain, good illumination
    LandingSiteCandidate(
        candidate_id="SP-002",
        crater=_crater("R-00002", "Haworth", -86.9, 358.1, 51.0),
        landing_ellipse_center_lat=-86.6,
        landing_ellipse_center_lon=357.5,
        landing_ellipse_semi_major_m=600.0,
        landing_ellipse_semi_minor_m=300.0,
        max_slope_deg=7.3,
        roughness_rms_m=0.21,
        rock_abundance=0.09,
        psr_access_fraction=0.55,
        metadata=_meta("LROC-estimated"),
    ),
    # Nobile — large crater, good science but high rock abundance → HC-003 fail
    LandingSiteCandidate(
        candidate_id="SP-003",
        crater=_crater("R-00003", "Nobile", -85.2, 53.5, 73.0),
        landing_ellipse_center_lat=-84.9,
        landing_ellipse_center_lon=54.1,
        landing_ellipse_semi_major_m=700.0,
        landing_ellipse_semi_minor_m=350.0,
        max_slope_deg=9.1,
        roughness_rms_m=0.35,
        rock_abundance=0.21,         # exceeds HC-003 (0.20 limit) → rejected
        psr_access_fraction=0.48,
        metadata=_meta("LROC-estimated"),
    ),
    # de Gerlache — moderate on all dimensions, safe choice
    LandingSiteCandidate(
        candidate_id="SP-004",
        crater=_crater("R-00004", "de Gerlache", -88.5, 272.0, 32.0),
        landing_ellipse_center_lat=-88.3,
        landing_ellipse_center_lon=273.2,
        landing_ellipse_semi_major_m=500.0,
        landing_ellipse_semi_minor_m=250.0,
        max_slope_deg=10.8,
        roughness_rms_m=0.25,
        rock_abundance=0.13,
        psr_access_fraction=0.63,
        metadata=_meta("LROC-estimated"),
    ),
    # Unnamed Ridge — very steep slope → HC-001 fail
    LandingSiteCandidate(
        candidate_id="SP-005",
        crater=_crater("R-00005", "Unnamed-Ridge", -87.1, 185.0, 18.0),
        landing_ellipse_center_lat=-87.0,
        landing_ellipse_center_lon=185.5,
        landing_ellipse_semi_major_m=400.0,
        landing_ellipse_semi_minor_m=200.0,
        max_slope_deg=17.4,          # exceeds HC-001 (15° limit) → rejected
        roughness_rms_m=0.44,
        rock_abundance=0.14,
        psr_access_fraction=0.31,
        metadata=_meta("LROC-estimated"),
    ),
]
