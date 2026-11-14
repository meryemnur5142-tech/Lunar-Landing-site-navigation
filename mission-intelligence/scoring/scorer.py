"""
Multi-criteria landing site scorer for LUNA-AI.

Design principles applied here:
- *Safety first*: only candidates that passed hard constraints are accepted.
- *Uncertainty visible*: every component score returns a (score, uncertainty)
  pair; the propagated total uncertainty is stored on :class:`RankedCandidate`.
- *Interface-based modularity*: scorer depends on domain model interfaces,
  not on concrete data-platform implementations.

Scoring dimensions:
    science   — PSR access fraction, instrument objectives alignment
    energy    — illumination time, solar generation margin (TBD: vehicle params)
    thermal   — safe dark-exposure duration margin (TBD: vehicle thermal model)
    communication — Earth visibility geometry (TBD: link budget model)
    risk      — terrain hazard density, PSR edge uncertainty, data quality

Component scores are in [0.0, 1.0] with 1.0 being ideal.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

from domain.crater.models import LandingSiteCandidate, RankedCandidate
from domain.environment.models import EnvironmentalDataProduct
from domain.mission.models import MissionObjective, ScoringWeights

__all__ = ["CandidateScorer"]


class CandidateScorer:
    """Score and rank landing site candidates using weighted multi-criteria analysis.

    Args:
        weights: Relative importance of each scoring dimension.
        mission_objectives: Ordered list of mission objectives (priority 1 first)
                            used to weight the science score.

    Example::

        scorer = CandidateScorer(
            weights=ScoringWeights(),
            mission_objectives=config.objectives,
        )
        ranked = scorer.rank(candidates, env_products)
        best = ranked[0]
    """

    def __init__(
        self,
        weights: ScoringWeights,
        mission_objectives: List[MissionObjective],
    ) -> None:
        self.weights = weights
        self.objectives = mission_objectives

    # ------------------------------------------------------------------
    # Component scorers
    # ------------------------------------------------------------------

    def score_science(
        self,
        candidate: LandingSiteCandidate,
        env: EnvironmentalDataProduct,
    ) -> Tuple[float, float]:
        """Compute science value score.

        Considers:
        - PSR access fraction relative to the minimum required by objectives.
        - Number of satisfied science objectives (by PSR access hours proxy).
        - Data quality of the PSR boundary product (from metadata quality_score).

        Args:
            candidate: Landing site candidate (must have passed hard constraints).
            env: Environmental data products for the candidate region.

        Returns:
            ``(score, uncertainty)`` where both are in [0.0, 1.0].
        """
        # PSR access component
        # Normalise against the most demanding objective's requirement
        min_required_fraction = 0.10  # default minimum (HC-002 baseline)
        if self.objectives:
            # Use maximum required PSR access hours as a proxy
            max_hours = max(o.minimum_psr_access_hours for o in self.objectives)
            # Map hours requirement to a fraction target heuristic (TBD: eclipse model)
            # For now assume 1 h per 0.05 fraction as a placeholder
            # TBD: replace with illumination time-series integration when available
            min_required_fraction = max(0.10, min(1.0, max_hours * 0.05))

        psr_score = min(1.0, candidate.psr_access_fraction / min_required_fraction)

        # PSR boundary data quality modulates score confidence
        psr_quality = 1.0
        if env.psr_boundaries:
            psr_quality = sum(p.confidence_level for p in env.psr_boundaries) / len(
                env.psr_boundaries
            )

        # Terrain data quality (from terrain product metadata if available)
        terrain_quality = 1.0
        if env.terrain is not None:
            terrain_quality = env.terrain.metadata.quality_score

        combined_quality = (psr_quality + terrain_quality) / 2.0
        score = psr_score * combined_quality
        uncertainty = 1.0 - combined_quality  # higher quality → lower uncertainty

        return _clamp(score), _clamp(uncertainty)

    def score_energy(
        self,
        candidate: LandingSiteCandidate,
        env: EnvironmentalDataProduct,
    ) -> Tuple[float, float]:
        """Compute energy margin score.

        Considers:
        - Average illumination fraction from the time series (solar generation proxy).
        - Proximity to a safe-haven PSR boundary (traverse energy reserve).

        .. note::
            TBD: Vehicle power budget (peak load, battery capacity, solar array
            efficiency) has not been confirmed.  The current implementation uses
            illumination fraction as a proxy.  Refine when ICD-001 (EnergyState)
            parameters are locked.

        Args:
            candidate: Landing site candidate.
            env: Environmental data products.

        Returns:
            ``(score, uncertainty)`` where both are in [0.0, 1.0].
        """
        if env.illumination is not None and env.illumination.illumination_fraction:
            avg_illumination = sum(env.illumination.illumination_fraction) / len(
                env.illumination.illumination_fraction
            )
            # Historical data is more reliable than prediction
            uncertainty = 0.05 if env.illumination.is_historical else 0.20
            score = avg_illumination
        else:
            # No illumination data available — conservative neutral score
            # TBD: compute from SPICE ephemeris when available
            score = 0.5
            uncertainty = 0.40  # high uncertainty without actual data

        return _clamp(score), _clamp(uncertainty)

    def score_thermal(
        self,
        candidate: LandingSiteCandidate,
        env: EnvironmentalDataProduct,
    ) -> Tuple[float, float]:
        """Compute thermal safety score.

        A higher score indicates the site allows more flexible thermal operations.
        Proximity to a PSR that can be exited quickly is beneficial.

        .. note::
            TBD: Safe dark-duration limit depends on the vehicle's thermal model
            (battery operating range, heater power budget).  Waiting for
            ICD-002 (ThermalState) parameters.  Current implementation uses
            PSR access fraction as a proxy for thermal exposure risk.

        Args:
            candidate: Landing site candidate.
            env: Environmental data products.

        Returns:
            ``(score, uncertainty)`` where both are in [0.0, 1.0].
        """
        # Higher PSR access → more dark exposure → higher thermal risk → lower score
        # Invert the PSR fraction: a site entirely inside a PSR is thermally risky
        psr_thermal_risk = candidate.psr_access_fraction
        score = 1.0 - psr_thermal_risk

        # Surface temperature product modulates uncertainty
        if env.surface_temperature is not None:
            uncertainty = 1.0 - env.surface_temperature.metadata.quality_score
        else:
            # TBD: no Diviner surface temperature product available yet
            uncertainty = 0.35

        return _clamp(score), _clamp(uncertainty)

    def score_communication(
        self,
        candidate: LandingSiteCandidate,
        env: EnvironmentalDataProduct,
    ) -> Tuple[float, float]:
        """Compute communication geometry score.

        .. note::
            TBD: Earth visibility and relay satellite orbit parameters have not
            been confirmed.  Returns a neutral score with high uncertainty until
            the communication link budget (ICD-003 extension) is available.

        Args:
            candidate: Landing site candidate.
            env: Environmental data products for the region.

        Returns:
            ``(score, uncertainty)`` where both are in [0.0, 1.0].
        """
        # TBD: implement SPICE Earth-visibility computation using candidate lat/lon
        # and the mission epoch from the illumination time series.
        # For near-polar sites the communication window is dominated by relay orbiters.
        score = 0.5
        uncertainty = 0.40  # TBD: placeholder until link budget model is integrated
        return score, uncertainty

    def score_risk(
        self,
        candidate: LandingSiteCandidate,
        env: EnvironmentalDataProduct,
    ) -> Tuple[float, float]:
        """Compute composite risk score (lower hazard = higher score).

        Components:
        - Terrain hazard: slope and rock abundance penalties.
        - PSR edge uncertainty: low PSR boundary confidence increases risk.
        - Data quality: low quality_score increases uncertainty.

        Args:
            candidate: Landing site candidate.
            env: Environmental data products.

        Returns:
            ``(score, uncertainty)`` where both are in [0.0, 1.0].
            A score of 1.0 means the site is least risky.
        """
        # Slope risk: normalise against hard constraint threshold (15 deg)
        slope_risk = min(1.0, candidate.max_slope_deg / 15.0)
        # Rock risk: rock_abundance is already in [0, 1]
        rock_risk = candidate.rock_abundance
        # Roughness risk: normalise against 1 m reference
        roughness_risk = min(1.0, candidate.roughness_rms_m / 1.0)

        terrain_risk = (slope_risk + rock_risk + roughness_risk) / 3.0
        terrain_score = 1.0 - terrain_risk

        # PSR edge uncertainty risk
        if env.psr_boundaries:
            avg_psr_confidence = sum(p.confidence_level for p in env.psr_boundaries) / len(
                env.psr_boundaries
            )
            psr_edge_risk = 1.0 - avg_psr_confidence
        else:
            psr_edge_risk = 0.5  # unknown PSR boundaries → moderate risk

        combined_score = (terrain_score + (1.0 - psr_edge_risk)) / 2.0

        # Uncertainty driven by data quality
        if env.terrain is not None:
            uncertainty = 1.0 - env.terrain.metadata.quality_score
        else:
            uncertainty = 0.30

        return _clamp(combined_score), _clamp(uncertainty)

    # ------------------------------------------------------------------
    # Full ranking pipeline
    # ------------------------------------------------------------------

    def rank(
        self,
        candidates: List[LandingSiteCandidate],
        env_products: Dict[str, EnvironmentalDataProduct],
    ) -> List[RankedCandidate]:
        """Score and rank all candidates that passed hard constraints.

        Only candidates with ``hard_constraints_passed=True`` are scored.
        Candidates without an entry in ``env_products`` use an empty
        :class:`~domain.environment.models.EnvironmentalDataProduct`.

        Args:
            candidates: List of annotated candidates (after
                        :class:`~mission_intelligence.constraints.hard_constraints.HardConstraintEvaluator`).
            env_products: Mapping from ``candidate_id`` to its environmental
                          data product bundle.

        Returns:
            List of :class:`~domain.crater.models.RankedCandidate` sorted by
            ``total_score`` descending.
        """
        ranked: List[RankedCandidate] = []

        for candidate in candidates:
            if not candidate.hard_constraints_passed:
                continue  # safety gate: never score a failed candidate

            env = env_products.get(candidate.candidate_id, EnvironmentalDataProduct())

            sci_score, sci_unc = self.score_science(candidate, env)
            eng_score, eng_unc = self.score_energy(candidate, env)
            thm_score, thm_unc = self.score_thermal(candidate, env)
            com_score, com_unc = self.score_communication(candidate, env)
            rsk_score, rsk_unc = self.score_risk(candidate, env)

            w = self.weights
            total = (
                w.science * sci_score
                + w.energy * eng_score
                + w.thermal * thm_score
                + w.communication * com_score
                + w.risk * rsk_score
            )

            # Propagate uncertainty (weighted RMS of component uncertainties)
            score_uncertainty = math.sqrt(
                (w.science * sci_unc) ** 2
                + (w.energy * eng_unc) ** 2
                + (w.thermal * thm_unc) ** 2
                + (w.communication * com_unc) ** 2
                + (w.risk * rsk_unc) ** 2
            )

            ranked.append(
                RankedCandidate(
                    candidate=candidate,
                    science_score=sci_score,
                    energy_score=eng_score,
                    thermal_score=thm_score,
                    communication_score=com_score,
                    risk_score=rsk_score,
                    total_score=_clamp(total),
                    score_uncertainty=_clamp(score_uncertainty),
                )
            )

        ranked.sort(key=lambda rc: rc.total_score, reverse=True)
        return ranked


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp *value* to [*lo*, *hi*]."""
    return max(lo, min(hi, value))
