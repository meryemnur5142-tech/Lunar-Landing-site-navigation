# simulation/

Simulation infrastructure: environment model, vehicle model, digital twin, test scenarios, fault injection. See v1.0 §7.

## Subdirectories

- `environment-model/` — Lunar DEM, illumination, thermal environment simulation.
- `vehicle-model/` — Vehicle dynamics and energy model simulation.
- `digital-twin/` — Real-time digital twin; SIL/HIL bridge.
- `scenarios/` — Operational test scenarios (SC-001..SC-009).
- `fault-injection/` — FMEA-based fault injection framework; B4 coverage matrix.

Lunar-Navigator integration: the SPICE pipeline (`data-platform/processing/ephemeris/`), 720-ray local horizon calculation (`data-platform/processing/horizon/`), and Earth disk visibility (`data-platform/processing/visibility/`) will be fed into this simulation environment as the reference implementation. See `infrastructure/repo_integration_map.md`.
