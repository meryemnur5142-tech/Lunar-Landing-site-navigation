"""
Hard constraint evaluation engine for LUNA-AI landing site candidates.

Design principle: *Safety first* — candidates that fail any hard constraint
are excluded from scoring entirely.  The constraint engine runs before the
multi-criteria scorer, making the safety gate explicit and auditable.

Each constraint carries a source reference (ADR/QAR document ID) so that
threshold values are always traceable to a requirements document.
"""

from __future__ import annotations

import operator as op
from typing import Dict, List, Optional, Tuple

from domain.crater.models import LandingSiteCandidate
from domain.mission.models import HardConstraint

__all__ = ["HardConstraintEvaluator"]

# Map operator string tokens to Python operator functions
_OPERATOR_MAP: Dict[str, object] = {
    "lt": op.lt,
    "gt": op.gt,
    "lte": op.le,
    "gte": op.ge,
    "eq": op.eq,
}


class HardConstraintEvaluator:
    """Evaluate landing site candidates against a set of hard safety constraints.

    *Safety first* principle: this evaluator must run before any scoring.
    Candidates that fail even one constraint are assigned
    ``hard_constraints_passed=False`` and are excluded from the scorer.

    Args:
        constraints: List of :class:`~domain.mission.models.HardConstraint`
                     objects that define the safety envelope.

    Example::

        evaluator = HardConstraintEvaluator(HardConstraintEvaluator.default_constraints())
        passed_candidates = evaluator.evaluate_batch(all_candidates)
    """

    def __init__(self, constraints: List[HardConstraint]) -> None:
        if not constraints:
            raise ValueError("At least one HardConstraint must be provided")
        self.constraints = constraints

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self, candidate: LandingSiteCandidate
    ) -> Tuple[bool, Optional[str]]:
        """Evaluate a single candidate against all hard constraints.

        Returns immediately on the first failing constraint (fail-fast
        semantics) so the rejection reason is unambiguous.

        Args:
            candidate: The candidate to evaluate.

        Returns:
            A ``(passed, rejection_reason)`` tuple.  ``rejection_reason``
            is *None* when ``passed`` is *True*.
        """
        for constraint in self.constraints:
            passed, reason = self._apply_constraint(candidate, constraint)
            if not passed:
                return False, reason
        return True, None

    def evaluate_batch(
        self, candidates: List[LandingSiteCandidate]
    ) -> List[LandingSiteCandidate]:
        """Evaluate all candidates and annotate them in-place.

        Sets ``hard_constraints_passed`` and ``rejection_reason`` on every
        candidate.  Returns only the candidates that passed all constraints.

        Args:
            candidates: Full list of candidates to filter.

        Returns:
            Filtered list containing only candidates that passed all
            hard constraints.
        """
        passing: List[LandingSiteCandidate] = []
        for candidate in candidates:
            passed, reason = self.evaluate(candidate)
            candidate.hard_constraints_passed = passed
            candidate.rejection_reason = reason
            if passed:
                passing.append(candidate)
        return passing

    # ------------------------------------------------------------------
    # Default constraint set
    # ------------------------------------------------------------------

    @staticmethod
    def default_constraints() -> List[HardConstraint]:
        """Return the baseline LUNA-AI hard constraint set.

        Thresholds are taken from the LUNA-AI System Requirements and will
        be updated when vehicle-specific parameters are confirmed.

        .. note::
            TBD constraints are marked below; they will be finalised when
            the navigation/power subsystem interface documents (ICD-003,
            ICD-001) are released.
        """
        return [
            HardConstraint(
                constraint_id="HC-001",
                name="Maximum Slope",
                parameter="max_slope_deg",
                operator="lte",
                threshold=15.0,
                unit="deg",
                source="ADR-001/QAR-NAV-001",
            ),
            HardConstraint(
                constraint_id="HC-002",
                name="Minimum PSR Access",
                parameter="psr_access_fraction",
                operator="gte",
                threshold=0.10,
                unit="fraction",
                source="QAR-SCI-001",
            ),
            HardConstraint(
                constraint_id="HC-003",
                name="Maximum Rock Abundance",
                parameter="rock_abundance",
                operator="lte",
                threshold=0.20,
                unit="fraction",
                source="QAR-MOB-001",
            ),
            # TBD: landing ellipse size — depends on vehicle navigation parameters (ICD-003)
            # TBD: communication line-of-sight angle — depends on frequency band and antenna gain
        ]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_constraint(
        candidate: LandingSiteCandidate, constraint: HardConstraint
    ) -> Tuple[bool, Optional[str]]:
        """Apply a single constraint to a candidate.

        Args:
            candidate: Candidate to test.
            constraint: Constraint specification.

        Returns:
            ``(passed, rejection_reason)`` where *rejection_reason* is
            *None* on success.

        Raises:
            AttributeError: If the candidate does not have the named parameter.
            ValueError: If the constraint specifies an unknown operator.
        """
        value = getattr(candidate, constraint.parameter)  # raises AttributeError if missing

        compare_fn = _OPERATOR_MAP.get(constraint.operator)
        if compare_fn is None:
            raise ValueError(
                f"Unknown operator '{constraint.operator}' in constraint "
                f"'{constraint.constraint_id}'"
            )

        passed = bool(compare_fn(value, constraint.threshold))  # type: ignore[operator]
        if passed:
            return True, None

        reason = (
            f"{constraint.constraint_id} '{constraint.name}': "
            f"{constraint.parameter}={value:.4g} {constraint.unit} "
            f"failed {constraint.operator} {constraint.threshold:.4g} {constraint.unit} "
            f"[{constraint.source}]"
        )
        return False, reason


