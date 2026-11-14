"""
LUNA-AI Resource-Constrained Global Planner — Python Pseudocode
Document: autonomy/mission_planner.md §2–§5
Status: draft | Owner: Agent D
Date: 2026-11-14

NOTE: This file is not a real implementation. It is a pseudocode skeleton
      designed to illustrate the algorithm structure and module interfaces.
      Actual parameters will be filled in once the TBDs in
      config/tbd_register.md are closed.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Tuple, Dict
import heapq
import math


# ---------------------------------------------------------------------------
# Enum Definitions
# ---------------------------------------------------------------------------

class ThermalState(Enum):
    NOMINAL = auto()
    CAUTION = auto()
    CRITICAL = auto()


class SafetyLevel(Enum):
    NOMINAL = auto()
    CAUTION = auto()
    RETURN_REQUIRED = auto()
    SURVIVAL = auto()


class PlanDecision(Enum):
    LOCAL_CORRECTION = auto()   # Small deviation: local avoidance manoeuvre
    FULL_REPLAN = auto()        # Full replan required
    DIRECTED_REPLAN = auto()    # Return-focused replan (energy warning)
    ABORT_RETURN = auto()       # ACL emergency return triggered


# ---------------------------------------------------------------------------
# PlannerState — 6-dimensional state vector
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PlannerState:
    """
    6-dimensional planner state vector.
    Ref: autonomy/mission_planner.md §1.1

    frozen=True: State objects are hashable and can be added to the A* closed set.
    """
    konum_x: float          # metres, local map frame
    konum_y: float          # metres, local map frame
    zaman: float            # seconds, elapsed since mission start
    enerji_wh: float        # Wh, current battery state of charge
    termal_durum: ThermalState = ThermalState.NOMINAL
    guvenlik_seviyesi: SafetyLevel = SafetyLevel.NOMINAL

    def to_grid(self, resolution: float = 1.0) -> Tuple[int, int]:
        """Convert metric coordinates to grid indices."""
        return (int(self.konum_x / resolution), int(self.konum_y / resolution))

    def distance_to(self, other: "PlannerState") -> float:
        return math.sqrt((self.konum_x - other.konum_x) ** 2 +
                         (self.konum_y - other.konum_y) ** 2)

    def is_energy_critical(self, hc006_threshold_wh: float) -> bool:
        """HC-006: is the return energy reserve critical?"""
        return self.enerji_wh < hc006_threshold_wh

    def is_safe_to_plan(self) -> bool:
        """Return True if the planner is allowed to add new mission steps."""
        return self.guvenlik_seviyesi in (SafetyLevel.NOMINAL, SafetyLevel.CAUTION)


@dataclass
class EnergyBudget:
    """
    Computed by the Power Management module and reported to the planner via ICD-002.
    The planner does not compute this structure independently (HC-006 Conformance Note 3).
    """
    return_reserve_wh: float     # Minimum energy required for return (HC-006)
    current_soc_wh: float        # Current battery energy (Wh)
    energy_per_meter: float      # Vehicle energy consumption model (Wh/m); TBD-PLAN-003


@dataclass
class WaypointPlan:
    """Global planner output: waypoint list and energy profile."""
    waypoints: List[Tuple[float, float]]
    estimated_energy_wh: List[float]   # estimated energy consumption per step
    total_distance_m: float
    planning_time_s: float             # QAR-PLAN-001: < 60 s target


# ---------------------------------------------------------------------------
# CostModel — Cost function components
# ---------------------------------------------------------------------------

class CostModel:
    """
    Combined cost function.
    Ref: autonomy/mission_planner.md §2.3

    cost = w_dist  × dist(i,j)
         + w_energy × energy_cost(i,j)
         + w_thermal × thermal_cost(i,j)
         + w_risk   × risk_cost(i,j)
    """

    def __init__(
        self,
        w_dist: float = 1.0,
        w_energy: float = 2.0,
        w_thermal: float = 1.5,
        w_risk: float = 3.0,
        energy_per_meter: float = None,   # TBD-PLAN-003
        thermal_coeff: float = None,       # TBD-PLAN-004
        risk_coeff: float = None,          # TBD-PLAN-005
    ):
        self.w_dist = w_dist
        self.w_energy = w_energy
        self.w_thermal = w_thermal
        self.w_risk = w_risk
        # TBD: placeholders below will be replaced with real values once §10 vehicle data is confirmed
        self._energy_per_m = energy_per_meter   # TBD-PLAN-003
        self._thermal_coeff = thermal_coeff     # TBD-PLAN-004
        self._risk_coeff = risk_coeff           # TBD-PLAN-005

    def edge_cost(
        self,
        from_state: PlannerState,
        to_state: PlannerState,
        terrain_slope_deg: float,
        obstacle_fraction: float,  # HC-003: ≤ 0.20
    ) -> float:
        """
        Combined cost between two states.
        HC-003 hard constraint violation: returns infinite cost (obstacle fraction > 0.20).
        """
        if obstacle_fraction > 0.20:  # HC-003 hard constraint
            return math.inf

        dist = from_state.distance_to(to_state)

        # Energy cost: simplified model accounting for terrain slope
        # Real model: provided by Power Management (TBD-PLAN-003)
        slope_factor = 1.0 + abs(math.sin(math.radians(terrain_slope_deg)))
        energy_cost = dist * slope_factor  # Wh/m × distance; coefficient TBD-PLAN-003

        # Thermal cost: increased pressure inside a PSR (TBD-PLAN-004)
        thermal_cost = 0.0
        if to_state.termal_durum == ThermalState.CAUTION:
            thermal_cost = dist * 0.5   # placeholder; TBD-PLAN-004
        elif to_state.termal_durum == ThermalState.CRITICAL:
            thermal_cost = dist * 5.0   # high penalty; TBD-PLAN-004

        # Risk cost: slope and obstacle proximity (TBD-PLAN-005)
        risk_cost = obstacle_fraction * dist  # placeholder; TBD-PLAN-005

        return (self.w_dist * dist
                + self.w_energy * energy_cost
                + self.w_thermal * thermal_cost
                + self.w_risk * risk_cost)

    def heuristic(self, state: PlannerState, goal: PlannerState, w: float = 1.0) -> float:
        """
        Weighted A* heuristic: Euclidean distance × weight.
        w > 1 gives suboptimal but faster search; complies with QAR-PLAN-001 (< 60 s).
        w = TBD-PLAN-001.
        """
        return w * state.distance_to(goal)


# ---------------------------------------------------------------------------
# ResourceConstrainedAStar — Resource-Constrained A* Core Structure
# ---------------------------------------------------------------------------

class ResourceConstrainedAStar:
    """
    Resource-constrained A* planner.
    Ref: autonomy/mission_planner.md §2, ADR-001

    Key difference from classic A*: tracks energy and thermal state at each node
    via forward simulation; applies the return-reserve constraint as early pruning.
    """

    def __init__(
        self,
        cost_model: CostModel,
        energy_budget: EnergyBudget,
        heuristic_weight: float = 1.0,  # TBD-PLAN-001
        grid_resolution_m: float = 1.0,
    ):
        self.cost_model = cost_model
        self.energy_budget = energy_budget
        self.w = heuristic_weight  # TBD-PLAN-001
        self.resolution = grid_resolution_m

    def plan(
        self,
        start: PlannerState,
        goal: Tuple[float, float],
        occupancy_grid: Dict[Tuple[int, int], float],  # (ix, iy) → obstacle_fraction
        terrain_slope_grid: Dict[Tuple[int, int], float],  # (ix, iy) → slope_deg
        safe_haven_coords: List[Tuple[float, float]],
    ) -> Optional[WaypointPlan]:
        """
        A* search. The return-reserve constraint is checked at every expansion step.

        Returns:
            WaypointPlan or None (if no solution is found)
        """
        import time
        t_start = time.time()

        goal_state = PlannerState(goal[0], goal[1], 0, 0)  # for proximity detection

        # Priority queue: (f_score, state)
        open_set: list = []
        heapq.heappush(open_set, (0.0, id(start), start))

        came_from: Dict[PlannerState, Optional[PlannerState]] = {start: None}
        g_score: Dict[PlannerState, float] = {start: 0.0}

        while open_set:
            _, _, current = heapq.heappop(open_set)

            # Goal check
            if current.distance_to(goal_state) < self.resolution:
                plan = self._reconstruct_path(came_from, current)
                plan.planning_time_s = time.time() - t_start
                return plan  # QAR-PLAN-001: duration must be < 60 s

            for neighbor, slope, obstacle_frac in self._get_neighbors(
                current, occupancy_grid, terrain_slope_grid
            ):
                # --- Return reserve constraint (HC-006) ---
                return_energy = self._estimate_return_energy(
                    neighbor, safe_haven_coords
                )
                if neighbor.enerji_wh - return_energy < self.energy_budget.return_reserve_wh:
                    # Reaching this node would leave insufficient return energy → prune
                    continue

                tentative_g = g_score[current] + self.cost_model.edge_cost(
                    current, neighbor, slope, obstacle_frac
                )

                if tentative_g < g_score.get(neighbor, math.inf):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + self.cost_model.heuristic(neighbor, goal_state, self.w)
                    heapq.heappush(open_set, (f, id(neighbor), neighbor))

        return None  # No solution found

    def _get_neighbors(
        self,
        state: PlannerState,
        occupancy_grid: Dict,
        slope_grid: Dict,
    ):
        """
        Generate neighbour nodes (8-connected grid).
        Returns a (PlannerState, slope_deg, obstacle_fraction) tuple for each neighbour.
        In the real implementation, kinematic constraints and wheel angle limits will be added.
        """
        # Pseudocode: real grid traversal goes here
        neighbors = []
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
            nx = state.konum_x + dx * self.resolution
            ny = state.konum_y + dy * self.resolution
            grid_key = (int(nx / self.resolution), int(ny / self.resolution))
            slope = slope_grid.get(grid_key, 0.0)
            obs_frac = occupancy_grid.get(grid_key, 0.0)

            # HC-005: slope limit check (threshold: TBD-TRV-002)
            # if slope > TBD_TRV_002_max_slope: continue

            dist = math.sqrt(dx**2 + dy**2) * self.resolution
            energy_consumed = dist * self.energy_budget.energy_per_meter
            new_energy = state.enerji_wh - energy_consumed

            neighbor = PlannerState(
                konum_x=nx,
                konum_y=ny,
                zaman=state.zaman + dist / 0.1,  # TBD-TRV-001: nominal speed
                enerji_wh=new_energy,
                termal_durum=state.termal_durum,  # Real model: thermal simulation
                guvenlik_seviyesi=state.guvenlik_seviyesi,
            )
            neighbors.append((neighbor, slope, obs_frac))
        return neighbors

    def _estimate_return_energy(
        self,
        state: PlannerState,
        safe_haven_coords: List[Tuple[float, float]],
    ) -> float:
        """
        Minimum energy estimate from the given location to the nearest safe haven.
        Uses the Power Management model (Conformance Note 3: not computed independently).
        This pseudocode shows a simplified Euclidean estimate.
        """
        if not safe_haven_coords:
            return math.inf
        min_dist = min(
            math.sqrt((state.konum_x - sx)**2 + (state.konum_y - sy)**2)
            for sx, sy in safe_haven_coords
        )
        # Real implementation: obtains return_reserve_wh from Power Management (ICD-002)
        return min_dist * self.energy_budget.energy_per_meter

    def _reconstruct_path(
        self,
        came_from: Dict,
        current: PlannerState,
    ) -> WaypointPlan:
        """Back-trace the came_from map to build the waypoint list."""
        path = []
        node = current
        while node is not None:
            path.append((node.konum_x, node.konum_y))
            node = came_from.get(node)
        path.reverse()
        # Energy profile: pseudocode placeholder
        return WaypointPlan(
            waypoints=path,
            estimated_energy_wh=[0.0] * len(path),
            total_distance_m=sum(
                math.sqrt((path[i][0]-path[i-1][0])**2 + (path[i][1]-path[i-1][1])**2)
                for i in range(1, len(path))
            ),
            planning_time_s=0.0,
        )

    def evaluate_replan_decision(
        self,
        current_state: PlannerState,
        blocked_waypoints: int,
        safety_transition: bool,
        return_margin_ratio: float,
    ) -> PlanDecision:
        """
        Full replan or local correction?
        Ref: autonomy/mission_planner.md §4.1
        """
        if safety_transition:
            # FDIR safety state changed → mandatory full replan
            if current_state.guvenlik_seviyesi == SafetyLevel.RETURN_REQUIRED:
                return PlanDecision.ABORT_RETURN
            return PlanDecision.FULL_REPLAN

        if return_margin_ratio <= 1.1:
            # Return margin 110% early-warning threshold → return-focused replan
            return PlanDecision.DIRECTED_REPLAN

        if blocked_waypoints > 2:
            # Multiple consecutive obstacles → full replan
            return PlanDecision.FULL_REPLAN

        # Single obstacle → local correction
        return PlanDecision.LOCAL_CORRECTION


# ---------------------------------------------------------------------------
# SafeHavenSelector — Safe Haven Scoring Function
# ---------------------------------------------------------------------------

@dataclass
class SafeHavenCandidate:
    """Candidate safe haven location and raw metric values."""
    coord: Tuple[float, float]
    illumination_hr: float            # HC-009: TBD-PLAN-006
    max_darkness_hr: float            # HC-010
    recharge_wh_per_sol: float        # HC-011: TBD-PLAN-007
    return_distance_m: float          # HC-012: distance × energy_per_m + margin
    thermal_safe: bool                # HC-013
    comm_visibility_min_per_sol: float  # HC-014
    emergency_route_distance_m: float  # HC-015


class SafeHavenSelector:
    """
    Safe haven selector: HC-009..HC-015 hard constraint filtering + weighted scoring.
    Ref: autonomy/mission_planner.md §5

    Important: candidates that do not pass the HC set are excluded from scoring
    (HC catalogue preamble).
    """

    # HC thresholds: TBDs will be closed as §10 vehicle data is confirmed
    HC009_MIN_ILLUMINATION_HR = None     # TBD-PLAN-006 / SHV-001
    HC010_MAX_DARKNESS_HR = None         # TBD §10 thermal
    HC011_MIN_RECHARGE_WH_SOL = None     # TBD-PLAN-007
    HC013_THERMAL_SAFE_REQUIRED = True   # boolean hard constraint
    HC014_MIN_COMM_MIN_SOL = None        # TBD §10 communication
    HC015_MAX_EMERGENCY_DIST_M = None    # TBD §10

    # Scoring weights (sum = 1.0)
    W1_ILLUMINATION = 0.20
    W2_RECHARGE = 0.20
    W3_RETURN_ENERGY = 0.20
    W4_THERMAL = 0.15
    W5_COMM = 0.15
    W6_EMERGENCY_ROUTE = 0.05
    W7_DARKNESS_PENALTY = 0.05

    def __init__(self, energy_budget: EnergyBudget):
        self.energy_budget = energy_budget

    def _passes_hard_constraints(self, candidate: SafeHavenCandidate) -> bool:
        """
        HC-009..HC-015 hard constraint pass/fail check.
        Returns False if any HC fails; the candidate is eliminated.
        """
        # HC-009: minimum continuous illumination
        if (self.HC009_MIN_ILLUMINATION_HR is not None and
                candidate.illumination_hr < self.HC009_MIN_ILLUMINATION_HR):
            return False

        # HC-010: maximum darkness interval
        if (self.HC010_MAX_DARKNESS_HR is not None and
                candidate.max_darkness_hr > self.HC010_MAX_DARKNESS_HR):
            return False

        # HC-011: recharge capacity
        if (self.HC011_MIN_RECHARGE_WH_SOL is not None and
                candidate.recharge_wh_per_sol < self.HC011_MIN_RECHARGE_WH_SOL):
            return False

        # HC-012: return energy sufficiency
        required_return_energy = (candidate.return_distance_m *
                                   self.energy_budget.energy_per_meter +
                                   self.energy_budget.return_reserve_wh)
        if self.energy_budget.current_soc_wh < required_return_energy:
            return False

        # HC-013: thermal safety
        if self.HC013_THERMAL_SAFE_REQUIRED and not candidate.thermal_safe:
            return False

        # HC-014: communication line-of-sight availability
        if (self.HC014_MIN_COMM_MIN_SOL is not None and
                candidate.comm_visibility_min_per_sol < self.HC014_MIN_COMM_MIN_SOL):
            return False

        # HC-015: emergency access distance
        if (self.HC015_MAX_EMERGENCY_DIST_M is not None and
                candidate.emergency_route_distance_m > self.HC015_MAX_EMERGENCY_DIST_M):
            return False

        return True

    def _score(self, candidate: SafeHavenCandidate, max_values: Dict) -> float:
        """
        Normalised weighted score computation.
        All components are normalised to [0, 1].
        """
        # Normalise: high illumination → high score
        s_illumination = min(1.0, candidate.illumination_hr /
                             max(max_values.get("illumination_hr", 1), 1))

        # Normalise: high recharge capacity → high score
        s_recharge = min(1.0, candidate.recharge_wh_per_sol /
                         max(max_values.get("recharge_wh_per_sol", 1), 1))

        # Normalise: short return distance → high score
        s_return = 1.0 - min(1.0, candidate.return_distance_m /
                             max(max_values.get("return_distance_m", 1), 1))

        # Thermal safety: boolean → 1.0 or 0.0
        s_thermal = 1.0 if candidate.thermal_safe else 0.0

        # Normalise: large communication window → high score
        s_comm = min(1.0, candidate.comm_visibility_min_per_sol /
                     max(max_values.get("comm_visibility_min_per_sol", 1), 1))

        # Normalise: short emergency route → high score
        s_emergency = 1.0 - min(1.0, candidate.emergency_route_distance_m /
                                max(max_values.get("emergency_route_distance_m", 1), 1))

        # Darkness penalty: low darkness → high score
        s_darkness = 1.0 - min(1.0, candidate.max_darkness_hr /
                               max(max_values.get("max_darkness_hr", 1), 1))

        return (self.W1_ILLUMINATION * s_illumination
                + self.W2_RECHARGE * s_recharge
                + self.W3_RETURN_ENERGY * s_return
                + self.W4_THERMAL * s_thermal
                + self.W5_COMM * s_comm
                + self.W6_EMERGENCY_ROUTE * s_emergency
                + self.W7_DARKNESS_PENALTY * s_darkness)

    def select(
        self,
        candidates: List[SafeHavenCandidate],
    ) -> Optional[SafeHavenCandidate]:
        """
        1. HC-009..HC-015 hard constraint filtering
        2. Weighted scoring among passing candidates
        3. Returns the highest-scoring candidate; None if no candidates pass

        Returns:
            Best SafeHavenCandidate or None
        """
        qualifying = [c for c in candidates if self._passes_hard_constraints(c)]

        if not qualifying:
            return None  # Critical: no safe haven found → notify FDIR

        # Compute max values for normalisation
        max_values = {
            "illumination_hr": max(c.illumination_hr for c in qualifying),
            "recharge_wh_per_sol": max(c.recharge_wh_per_sol for c in qualifying),
            "return_distance_m": max(c.return_distance_m for c in qualifying),
            "comm_visibility_min_per_sol": max(c.comm_visibility_min_per_sol for c in qualifying),
            "emergency_route_distance_m": max(c.emergency_route_distance_m for c in qualifying),
            "max_darkness_hr": max(c.max_darkness_hr for c in qualifying),
        }

        scored = [(self._score(c, max_values), c) for c in qualifying]
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]


# ---------------------------------------------------------------------------
# ReplanningDecisionModule — Trigger and Decision Module
# ---------------------------------------------------------------------------

class ReplanningDecisionModule:
    """
    Replanning triggers and local/global decision logic.
    Ref: autonomy/mission_planner.md §4
    QAR-PLAN-002: replanning duration < 30 s
    """

    # QAR-PLAN-002: replanning duration target
    REPLAN_TIME_TARGET_S = 30.0

    # QAR-PLAN-005: return margin monitoring frequency
    RETURN_MARGIN_CHECK_HZ = 1.0

    # Local avoidance distance threshold (linked to TBD-PLAN-002)
    LOCAL_DEVIATION_MAX_M = 20.0  # placeholder; TBD

    def check_triggers(
        self,
        current_state: PlannerState,
        blocked_waypoints: int,
        hc006_threshold_wh: float,
        return_energy_wh: float,
        safety_transition: bool,
        safe_haven_changed: bool,
    ) -> PlanDecision:
        """
        Evaluate replanning trigger conditions.
        Ref: autonomy/mission_planner.md §4.1

        ABT-series abort triggers (autonomy matrix) are checked:
        - ABT-001: return_reserve_wh < HC-006
        - ABT-002: position_uncertainty > QAR-NAV-004 threshold
        """
        # ABT-001: return reserve critical → mandatory return
        available_energy = current_state.enerji_wh - return_energy_wh
        if available_energy < hc006_threshold_wh:
            return PlanDecision.ABORT_RETURN

        # Safety state transition → plan invalidated
        if safety_transition:
            if current_state.guvenlik_seviyesi == SafetyLevel.RETURN_REQUIRED:
                return PlanDecision.ABORT_RETURN
            return PlanDecision.FULL_REPLAN

        # Safe haven coordinates changed
        if safe_haven_changed:
            return PlanDecision.FULL_REPLAN

        # Return margin 110% early warning
        return_margin_ratio = current_state.enerji_wh / max(hc006_threshold_wh, 1e-9)
        if return_margin_ratio <= 1.1:
            return PlanDecision.DIRECTED_REPLAN

        # Multiple consecutive obstacles
        if blocked_waypoints > 2:
            return PlanDecision.FULL_REPLAN

        # Single obstacle → local correction
        if blocked_waypoints > 0:
            return PlanDecision.LOCAL_CORRECTION

        return PlanDecision.LOCAL_CORRECTION  # Nominal: no change


# ---------------------------------------------------------------------------
# ScienceScheduler — Science Objective vs Resource Balance
# ---------------------------------------------------------------------------

@dataclass
class ScienceTask:
    """A single science task."""
    task_id: str
    priority: int           # 1 = lowest, 4 = never auto-cancelled (sample)
    energy_cost_wh: float
    is_optional: bool


class ScienceScheduler:
    """
    Science task scheduling and cancellation logic.
    Ref: autonomy/mission_planner.md §7
    TBD-PLAN-009: priority weights determined from the ground-segment mission package.
    """

    def filter_executable_tasks(
        self,
        tasks: List[ScienceTask],
        current_state: PlannerState,
        available_energy_wh: float,
    ) -> List[ScienceTask]:
        """
        Executable task list based on current safety state and energy budget.
        Ref: autonomy/mission_planner.md §7.2 cancellation rules
        """
        if current_state.guvenlik_seviyesi == SafetyLevel.RETURN_REQUIRED:
            # All science operations are frozen
            return []

        if current_state.guvenlik_seviyesi == SafetyLevel.SURVIVAL:
            # No science task may run
            return []

        eligible = []
        for task in tasks:
            # Safety state CAUTION: high-power science instrument cannot be started
            if (current_state.guvenlik_seviyesi == SafetyLevel.CAUTION
                    and task.energy_cost_wh > 10.0):  # threshold: TBD-PLAN-009
                continue

            # Energy budget check
            if task.energy_cost_wh > available_energy_wh:
                continue

            # Priority 4 (sample): never auto-cancelled
            if task.priority == 4:
                eligible.append(task)
                continue

            # Other tasks: add if energy and state allow
            eligible.append(task)

        # Priority ordering: highest priority first
        eligible.sort(key=lambda t: t.priority, reverse=True)
        return eligible
