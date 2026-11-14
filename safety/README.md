# safety/

Safety layer: health monitoring, FDIR, safe mode management, watchdog. See v1.0 §4.8.

Compliance Note 3: The safety budget is owned by the Power Management module; it is reported to the planner, and the flow direction is non-reversible (see `safety/safety_budget.md`).

FDIR operates independently of the planner (isolated memory — P0-AC-04).

## Subdirectories

- `health-monitor/` — System health telemetry monitoring; raw data before anomaly detection.
- `fdir/` — Fault Detection, Isolation & Recovery; abort decision generator.
- `safing/` — Safe state transition procedures; SAFE_STATE phase management.
- `watchdog/` — Software watchdog; critical task loop timeout protection.
