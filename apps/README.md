# apps/

User interfaces and service layer: ground control UI, mission API, simulator connector. See v1.0 §1.8.

## Subdirectories

- `ground-control/` — Ground control station UI; site selection, telemetry display, operator approval interface.
- `mission-api/` — Mission command and query REST/gRPC service; vehicle-ground data bridge.
- `simulator/` — Simulator connector layer; vehicle model interface for SIL runs.
