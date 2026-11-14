# Vehicle Mobility Control

**v1.0 Reference:** §4.6 Navigation & Mobility

Differential drive command generation, wheel torque control, and motor driver interface.

## Dependencies

- `vehicle/localization/` — current position and heading (ICD-003)
- `safety/` — motion commands are supervised by the safety monitor

## Motor Stall FDIR

On motor stall detection, FI-004-referenced fault injection is applied.
FDIR response: stop motor → report fault to FDIR → wait for NOMINAL→CAUTION transition.
See `docs/adr/FMEA_KRITIK_MODULLER.md` (FI-004) and `safety/README.md`
