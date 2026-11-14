# autonomy/

Mission execution, global/local planning, replanning, science scheduling. See v1.0 §4.3.

## Subdirectories

- `mission-executive/` — Mission phase management; phase transition logic, abort decisions.
- `global-planner/` — A*-based global route planning; < 60 s target (1 km² terrain).
- `local-planner/` — Real-time obstacle avoidance and local waypoint generation.
- `replanner/` — < 30 s replanning on sudden condition changes; ABT trigger integration.
- `scheduler/` — Science task scheduling; energy-time budget optimisation.
