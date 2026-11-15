"""
Landing efficiency window calculator for LUNA-AI.

Computes four orbital landing windows for a given LandingSiteCandidate,
scoring each window on terrain quality, solar margin, Earth communication
geometry, and propellant margin.

Efficiency (%) represents the probability of achieving full mission objectives
when landing in that specific window, relative to the theoretical maximum for
the candidate site.

Formula
-------
terrain_quality  = f(slope, roughness, rock_abundance)   – site-specific
science_quality  = f(psr_access_fraction, rock_abundance) – site-specific
window_quality   = f(solar_elevation, earth_elevation, delta_v_penalty) – time-varying

efficiency = 85 + scaled(terrain*0.35 + science*0.25 + window*0.40) * 15
            clamped to [85, 99]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal

from domain.crater.models import LandingSiteCandidate

__all__ = ["LandingWindow", "EfficiencyCalculator"]

# ---------------------------------------------------------------------------
# Pre-computed orbital windows (south-pole, 2026-11 epoch)
# ---------------------------------------------------------------------------

_ORBITAL_CONFIGS: list[dict] = [
    {
        "label": "W-1",
        "utc_time": "2026-11-23 14:32 UTC",
        "solar_deg": 3.2,
        "earth_deg": 12.5,
        "descent_angle_deg": 8.0,
        "delta_v_penalty_ms": 0.0,
        "comm_mode": "direct",
    },
    {
        "label": "W-2",
        "utc_time": "2026-11-24 02:17 UTC",
        "solar_deg": 2.5,
        "earth_deg": 8.0,
        "descent_angle_deg": 10.0,
        "delta_v_penalty_ms": 12.0,
        "comm_mode": "direct",
    },
    {
        "label": "W-3",
        "utc_time": "2026-11-24 19:55 UTC",
        "solar_deg": 1.8,
        "earth_deg": 5.5,
        "descent_angle_deg": 12.0,
        "delta_v_penalty_ms": 28.0,
        "comm_mode": "relay",
    },
    {
        "label": "W-4",
        "utc_time": "2026-11-25 11:40 UTC",
        "solar_deg": 1.2,
        "earth_deg": 3.0,
        "descent_angle_deg": 15.0,
        "delta_v_penalty_ms": 45.0,
        "comm_mode": "relay",
    },
]


@dataclass
class LandingWindow:
    """One orbital landing opportunity with computed efficiency score.

    Attributes:
        window_id: Unique id, e.g. "SP-001-W1".
        label: Short display name, e.g. "W-1".
        utc_time: UTC datetime string for descent initiation.
        solar_elevation_deg: Sun elevation above local horizon (degrees).
        earth_elevation_deg: Earth elevation above local horizon (degrees).
        descent_angle_deg: Powered-descent approach angle (degrees).
        delta_v_penalty_ms: Additional Δv vs minimum-energy trajectory (m/s).
        solar_flux_wm2: Estimated solar flux at this window (W/m²).
        link_margin_dbm: RF link margin for primary Earth comm path (dBm).
        comm_mode: "direct" (LRS-1 direct link) or "relay" (LRO/relay only).
        efficiency_pct: Computed landing efficiency percentage.
        terrain_score: Site terrain quality, normalised [0, 1].
        window_quality: Time-varying orbital window quality [0, 1].
        dominant_factor: Primary driver of efficiency ("solar", "communication",
                         "terrain", or "propellant").
        conditions: Key parameter labels mapped to display strings.
    """

    window_id: str
    label: str
    utc_time: str
    solar_elevation_deg: float
    earth_elevation_deg: float
    descent_angle_deg: float
    delta_v_penalty_ms: float
    solar_flux_wm2: float
    link_margin_dbm: float
    comm_mode: Literal["direct", "relay"]
    efficiency_pct: float
    terrain_score: float
    window_quality: float
    dominant_factor: str
    conditions: dict = field(default_factory=dict)


class EfficiencyCalculator:
    """Compute four landing efficiency windows for a candidate site.

    Example::

        calc = EfficiencyCalculator()
        windows = calc.compute_windows(candidate)
        best = max(windows, key=lambda w: w.efficiency_pct)
    """

    # Solar constants
    _MAX_SOUTH_POLE_SOLAR_DEG = 3.5  # peak sun elevation, south pole
    _SOLAR_CONSTANT_WM2 = 1361.0     # W/m² at 1 AU

    # Terrain normalisation references
    _SLOPE_IDEAL_DEG = 0.0
    _SLOPE_NORM_REF_DEG = 12.0       # 12° → score 0 on slope component
    _ROUGHNESS_NORM_REF_M = 0.5
    _ROCK_NORM_REF = 0.15

    # Communication model
    _COMM_MAX_EARTH_DEG = 12.0       # Earth elevation for full link margin
    _LINK_SCALE_DBM = 0.67           # dBm per degree (linearised model)

    # Propellant model
    _DV_PENALTY_REF_MS = 60.0        # Δv at which prop score = 0

    def compute_windows(
        self,
        candidate: LandingSiteCandidate,
    ) -> List[LandingWindow]:
        """Compute efficiency for all four orbital windows.

        Args:
            candidate: Landing site candidate (hard constraints need not have
                       been evaluated; this scorer is geometry-only).

        Returns:
            List of four :class:`LandingWindow` objects, ordered W-1 to W-4.
        """
        terrain_score = self._terrain_score(candidate)
        science_score = self._science_score(candidate)

        windows: List[LandingWindow] = []
        for i, cfg in enumerate(_ORBITAL_CONFIGS, start=1):
            window_quality, solar_q, comm_q, prop_q = self._window_quality(cfg)

            efficiency_pct = self._combined_efficiency(
                terrain_score, science_score, window_quality
            )

            solar_flux = self._solar_flux(cfg["solar_deg"])
            link_margin = self._link_margin(cfg["earth_deg"])
            dominant = self._dominant_factor(
                terrain_score, solar_q, comm_q, prop_q
            )

            windows.append(
                LandingWindow(
                    window_id=f"{candidate.candidate_id}-W{i}",
                    label=cfg["label"],
                    utc_time=cfg["utc_time"],
                    solar_elevation_deg=cfg["solar_deg"],
                    earth_elevation_deg=cfg["earth_deg"],
                    descent_angle_deg=cfg["descent_angle_deg"],
                    delta_v_penalty_ms=cfg["delta_v_penalty_ms"],
                    solar_flux_wm2=round(solar_flux, 1),
                    link_margin_dbm=round(link_margin, 1),
                    comm_mode=cfg["comm_mode"],
                    efficiency_pct=efficiency_pct,
                    terrain_score=round(terrain_score, 3),
                    window_quality=round(window_quality, 3),
                    dominant_factor=dominant,
                    conditions={
                        "solar": f"{cfg['solar_deg']}° — {solar_flux:.0f} W/m²",
                        "earth": f"{cfg['earth_deg']}° — {cfg['comm_mode']}",
                        "descent": f"{cfg['descent_angle_deg']}° / +{cfg['delta_v_penalty_ms']:.0f} m/s",
                        "terrain": f"{candidate.max_slope_deg}° eğim / {candidate.roughness_rms_m:.2f} m pürüz",
                    },
                )
            )

        return windows

    # ------------------------------------------------------------------
    # Component scorers
    # ------------------------------------------------------------------

    def _terrain_score(self, c: LandingSiteCandidate) -> float:
        slope_norm = max(0.0, 1.0 - c.max_slope_deg / self._SLOPE_NORM_REF_DEG)
        rough_norm = max(0.0, 1.0 - c.roughness_rms_m / self._ROUGHNESS_NORM_REF_M)
        rock_norm = max(0.0, 1.0 - c.rock_abundance / self._ROCK_NORM_REF)
        return slope_norm * 0.50 + rough_norm * 0.25 + rock_norm * 0.25

    def _science_score(self, c: LandingSiteCandidate) -> float:
        return c.psr_access_fraction * 0.70 + (1.0 - c.rock_abundance) * 0.30

    def _window_quality(self, cfg: dict) -> tuple[float, float, float, float]:
        solar_q = min(1.0, cfg["solar_deg"] / self._MAX_SOUTH_POLE_SOLAR_DEG)
        comm_q = min(1.0, cfg["earth_deg"] / self._COMM_MAX_EARTH_DEG)
        prop_q = max(0.0, 1.0 - cfg["delta_v_penalty_ms"] / self._DV_PENALTY_REF_MS)
        window_quality = solar_q * 0.40 + comm_q * 0.30 + prop_q * 0.30
        return window_quality, solar_q, comm_q, prop_q

    def _combined_efficiency(
        self,
        terrain: float,
        science: float,
        window: float,
    ) -> float:
        composite = terrain * 0.35 + science * 0.25 + window * 0.40
        # Nonlinear boost: reward composites above 0.70
        scaled = (
            0.70 + (composite - 0.70) * 1.80
            if composite > 0.70
            else composite
        )
        raw = 85.0 + scaled * 15.0
        return round(min(99.0, max(85.0, raw)), 1)

    def _solar_flux(self, solar_deg: float) -> float:
        import math
        return self._SOLAR_CONSTANT_WM2 * math.sin(math.radians(solar_deg))

    def _link_margin(self, earth_deg: float) -> float:
        return earth_deg * self._LINK_SCALE_DBM - 0.5

    @staticmethod
    def _dominant_factor(
        terrain: float,
        solar_q: float,
        comm_q: float,
        prop_q: float,
    ) -> str:
        scores = {
            "terrain": terrain,
            "solar": solar_q,
            "communication": comm_q,
            "propellant": prop_q,
        }
        return min(scores, key=scores.get)  # the weakest link dominates negatively
