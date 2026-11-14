# ADR-001: Route Planning Algorithm

**Status:** Accepted
**Date:** 2026-11-14
**Related QAR:** PLAN-001, PLAN-002, PLAN-004, NAV-001

---

## Context

LUNA-AI must travel to craters containing PSRs (Permanently Shadowed Regions) on the lunar surface and return. Route planning operates under the following constraints:

- **Energy budget:** A route must not only be geometrically optimal but also energy-cost-aware (slope, illumination, motor power). Climbing a slope consumes more energy; if downhill regeneration is available it must be included in the model.
- **Thermal state:** The vehicle may or may not want to stay in shadowed areas for extended periods (cooling or heating needs). The route must reflect this preference.
- **Resource constraint:** The processor and memory on the vehicle are limited. Algorithmic complexity must remain within a practical running time.
- **Dynamic obstacles:** Unknown obstacles (rocks, pits) exist both inside and outside the PSR. Planning must operate at both global and local levels.
- **Replanning:** Replanning must be completed in < 30 seconds on new obstacle detection (PLAN-002).

---

## Alternatives Evaluated

### Alternative 1: A* (A-Star)

**Pros:**
- Optimal solution guarantee (with admissible heuristic)
- Wide literature support; proven use in space missions
- Efficient on static maps; predictable memory management
- Adding energy cost and thermal preference to the heuristic function is relatively straightforward (weighted A*)
- Deterministic structure simplifying formal verification

**Cons:**
- With dynamic obstacles, the entire map or large portions may need replanning
- With high-resolution PSR maps, memory consumption may increase
- Multi-dimensional cost function (energy + thermal + distance) complicates heuristic design

---

### Alternative 2: D* Lite (Dynamic A*)

**Pros:**
- Incremental replanning with dynamic obstacles → only changed portions are recalculated
- Derived from A*, so optimal solution is preserved
- Significant efficiency gain on real-time changing maps

**Cons:**
- Reference implementations are less tested in the space environment than A*
- State update mechanism requires extra design for integration with energy/thermal-weighted heuristic
- Harder to debug and formally verify than A*

---

### Alternative 3: RRT* (Rapidly-exploring Random Tree)

**Pros:**
- Efficient in high-dimensional state spaces (6-DOF vehicle)
- Can naturally model non-holonomic constraints (vehicle turn radius)

**Cons:**
- Stochastic structure: different result with same input → violates deterministic requirement (FDIR-005 analogue)
- Optimal solution guarantee only asymptotic; may not be optimal in practical time
- Computation cost typically higher than A* and D*; risk in resource-constrained environment
- Reproducibility and formal verification are difficult

---

### Alternative 4: Potential Field

**Pros:**
- Extremely fast and lightweight; suitable for real-time local obstacle avoidance
- Simple to implement; easy to debug

**Cons:**
- Local minimum traps: can get stuck at crater passages or narrow corridors
- No guaranteed safe return path; unacceptable safety risk for this mission (P1)
- Global optimum not guaranteed; energy waste on long routes

---

## Decision

**A hybrid architecture has been adopted:**

- **Global Planning:** Weighted A* — an A* variant with energy, thermal preference, and slope cost incorporated into the heuristic. Runs at mission start and when replanning is needed (< 60 s guarantee, PLAN-001).
- **Local/Reactive Planning:** D* Lite-based incremental update — when new obstacle data arrives from LiDAR/camera, only the affected area is updated (< 30 s replanning, PLAN-002).
- **Short-range obstacle avoidance:** Potential Field is not used; the D* Lite local update takes on this role.

**Rationale:** RRT* was eliminated because it does not meet the deterministic requirement. Potential Field is unacceptable from a safety perspective due to local minimum risk. The hybrid use of A* and D* Lite provides both the optimal global solution and dynamic efficiency.

---

## Consequences and Constraints

1. **Heuristic maintenance:** The energy-weighted heuristic function must be calibrated once the hardware energy parameters arrive (TBD-PWR); it will be initially deployed with conservative (non-overestimating) values.
2. **Map resolution:** Global map resolution (**TBD:** m/pixel — DEM data pending) will determine the memory budget.
3. **Replanning threshold:** The D* Lite update trigger must be tuned based on obstacle size and position difference; triggering too frequently increases processor load.
4. **Simulation first:** Every heuristic change must be validated in the digital twin before going to production (Simulation Before Validation principle).
5. **ICD dependency:** The planner receives energy/thermal state from Power Management (ICD-001) and Thermal Management (ICD-002); until these interfaces are locked, the heuristic will operate with simple distance targets.
