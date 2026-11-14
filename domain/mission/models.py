"""
Mission domain models for LUNA-AI.

Defines mission objectives, hard safety constraints, multi-criteria scoring
weights, and the top-level mission configuration that drives the
ground-segment analysis pipeline.

Design principle: *Safety first* — hard constraints are expressed as
explicit, traceable data objects rather than magic numbers scattered through
the code.  Every constraint carries a reference to the source requirement
document (ADR / QAR).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Optional

from domain.environment.models import BoundingBox

__all__ = [
    "MissionObjective",
    "HardConstraint",
    "ScoringWeights",
    "MissionConfig",
]


@dataclass
class MissionObjective:
    """A single science or operational objective for the mission.

    Attributes:
        objective_id: Unique identifier (e.g. "OBJ-001").
        description: Human-readable objective statement.
        priority: Integer priority; 1 is the highest priority.
        science_category: Broad science domain this objective belongs to.
        minimum_psr_access_hours: Minimum hours of PSR access required to
                                   satisfy this objective.
        required_instruments: List of instrument names needed (e.g. ["NIRVSS"]).
    """

    objective_id: str
    description: str
    priority: int
    science_category: Literal[
        "geology", "volatiles", "psr_characterization", "resource_assessment"
    ]
    minimum_psr_access_hours: float
    required_instruments: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.priority < 1:
            raise ValueError(f"priority must be >= 1, got {self.priority}")
        if self.minimum_psr_access_hours < 0:
            raise ValueError(
                f"minimum_psr_access_hours must be non-negative: {self.minimum_psr_access_hours}"
            )


@dataclass
class HardConstraint:
    """A binary pass/fail safety constraint applied to landing site candidates.

    The constraint is satisfied when:
        ``getattr(candidate, parameter) <operator> threshold``

    Traceable to a specific requirement document (``source``).

    Attributes:
        constraint_id: Unique identifier (e.g. "HC-001").
        name: Human-readable constraint name.
        parameter: Attribute name on :class:`~domain.crater.models.LandingSiteCandidate`
                   to evaluate.
        operator: Comparison operator as a short string.
        threshold: Numeric threshold value.
        unit: Physical unit of the threshold (for documentation).
        source: Requirement source reference (e.g. "ADR-001/QAR-NAV-001").
    """

    constraint_id: str
    name: str
    parameter: str
    operator: Literal["lt", "gt", "lte", "gte", "eq"]
    threshold: float
    unit: str
    source: str


@dataclass
class ScoringWeights:
    """Relative weights for the multi-criteria landing site scorer.

    Weights must sum to 1.0 (validated in ``__post_init__``).  Default
    values reflect the LUNA-AI baseline trade study; adjust per mission
    phase as requirements evolve.

    Attributes:
        science: Weight for the science value score component.
        energy: Weight for the energy margin score component.
        thermal: Weight for the thermal safety score component.
        communication: Weight for the communication geometry score component.
        risk: Weight for the risk (hazard + uncertainty) score component.
    """

    science: float = 0.30
    energy: float = 0.25
    thermal: float = 0.20
    communication: float = 0.15
    risk: float = 0.10

    def __post_init__(self) -> None:
        total = self.science + self.energy + self.thermal + self.communication + self.risk
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"Scoring weights must sum to 1.0, got {total:.8f}"
            )
        for attr in ("science", "energy", "thermal", "communication", "risk"):
            val = getattr(self, attr)
            if val < 0:
                raise ValueError(f"Weight '{attr}' must be non-negative, got {val}")


@dataclass
class MissionConfig:
    """Top-level mission configuration driving the ground-segment pipeline.

    Attributes:
        mission_id: Unique mission identifier (e.g. "LUNA-AI-2027-M1").
        objectives: Ordered list of mission objectives (highest priority first).
        hard_constraints: Set of hard constraints applied before scoring.
        scoring_weights: Relative weights for multi-criteria scoring.
        target_region: Geographic bounding box defining the region of interest.
    """

    mission_id: str
    objectives: List[MissionObjective]
    hard_constraints: List[HardConstraint]
    scoring_weights: ScoringWeights
    target_region: BoundingBox

    def __post_init__(self) -> None:
        if not self.objectives:
            raise ValueError("MissionConfig must have at least one objective")
        if not self.hard_constraints:
            raise ValueError("MissionConfig must have at least one hard constraint")
        # Sort objectives by priority (ascending: 1 is highest)
        self.objectives = sorted(self.objectives, key=lambda o: o.priority)

    @property
    def primary_objective(self) -> Optional[MissionObjective]:
        """The highest-priority (priority=1) objective, if present."""
        return self.objectives[0] if self.objectives else None
