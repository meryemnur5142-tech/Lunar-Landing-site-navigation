# LUNA-AI Critical Modules FMEA (Failure Mode and Effects Analysis)

**Document ID:** LUNA-AI-FMEA-001
**Version:** 0.1-draft
**Date:** 2026-11-14
**Method:** MIL-STD-1629A compliant; space mission adaptation

---

## Scoring Scale

| Score | Severity (S) | Occurrence (O) | Detection (D) |
|-------|-------------|---------------|--------------|
| 1 | Minimal impact | Extremely low | Almost certain detection |
| 2 | Minor impact | Low | High detection probability |
| 3 | Moderate impact | Moderate | Moderate detection probability |
| 4 | Critical impact | High | Low detection probability |
| 5 | Catastrophic (mission/vehicle loss) | Very high | Undetectable |

**RPN = Severity × Occurrence × Detection**
**RPN ≥ 50:** Mandatory action required
**RPN ≥ 80:** Critical; design change recommended

---

## FMEA Table

### Module: Power Management

| Module | Component | Failure Mode | Effect | Severity (S) | Occurrence (O) | Detection (D) | RPN | Mitigation |
|--------|-----------|--------------|--------|-------------|---------------|--------------|-----|-----------|
| Power Management | Battery | Sudden capacity drop (SoC reading < actual) | Return energy becomes insufficient; vehicle runs out of energy inside PSR → mission or vehicle loss | 5 | 2 | 3 | **30** | Dual SoC measurement method (voltage + Coulomb counter); return margin kept conservative (15% threshold) |
| Power Management | Solar Panel | Panel deployment failure (servo jam) | No charging; mission cannot be extended; energy reserve drops | 4 | 2 | 2 | **16** | Mechanical redundancy (spring-assisted fail-open); charging shortfall detected by power monitor within < 30 s |
| Power Management | Load Management Circuit | Critical load shedding command cannot be delivered | High power consumption continues in SURVIVAL mode; SoC drops rapidly | 5 | 1 | 2 | **10** | Hardware circuit breaker (latching relay); software and hardware provide separate shedding paths |
| Power Management | Charge Regulator | Overcharge (overcharge protection disabled) | Battery heats up; thermal critical; fire risk | 5 | 1 | 2 | **10** | Hardware charge protection circuit; independent voltage monitoring by software |

---

### Module: Thermal Management

| Module | Component | Failure Mode | Effect | Severity (S) | Occurrence (O) | Detection (D) | RPN | Mitigation |
|--------|-----------|--------------|--------|-------------|---------------|--------------|-----|-----------|
| Thermal Management | Heater | Heater open-circuit failure (not working) | Critical component cools → electronics failure → navigation/power loss | 5 | 2 | 2 | **20** | Redundant heater circuit; temperature sensor with 1 s periodic monitoring; FDIR early warning |
| Thermal Management | Temperature Sensor | Sensor short circuit (fixed false reading) | Incorrect temperature data; thermal decisions erroneous → delayed intervention | 4 | 2 | 2 | **16** | ≥ 2 independent sensors at each critical point; voting logic; anomaly detection |
| Thermal Management | Thermal Control Software | Heater control loop freezes (task freeze) | Heaters without intervention; temperature can drift | 4 | 2 | 2 | **16** | FDIR watchdog (5 s timeout); on watchdog trigger, FDIR directly moves heater to safe state |

---

### Module: Navigation

| Module | Component | Failure Mode | Effect | Severity (S) | Occurrence (O) | Detection (D) | RPN | Mitigation |
|--------|-----------|--------------|--------|-------------|---------------|--------------|-----|-----------|
| Navigation | IMU (Inertial Measurement Unit) | High drift (calibration corrupted) | Position error accumulates to > 1 m RMS; Local Planner throttles obstacle approach speed, may stop | 4 | 3 | 2 | **24** | Multi-sensor fusion (IMU + LiDAR landmark + camera); EKF covariance monitoring; rapid recalibration |
| Navigation | LiDAR | Contamination by dust/particles (increased return) | Visible range decreases; obstacle detection reliability drops | 3 | 3 | 2 | **18** | Multiple measurement perspectives; cross-validation with camera; outlier filtering in software |
| Navigation | EKF (Extended Kalman Filter) | Incorrect initialisation (initialization failure) | Localisation never converges; vehicle cannot move | 4 | 2 | 2 | **16** | Boot test: if EKF convergence not achieved within **TBD** seconds, FDIR is notified; restart procedure |

---

### Module: FDIR

| Module | Component | Failure Mode | Effect | Severity (S) | Occurrence (O) | Detection (D) | RPN | Mitigation |
|--------|-----------|--------------|--------|-------------|---------------|--------------|-----|-----------|
| FDIR | FDIR Software Task | FDIR task freeze (watchdog kick stopped) | State machine receives no updates; safety decisions cannot be made → single point of failure | 5 | 1 | 1 | **5** | Hardware watchdog: on FDIR freeze the system is restarted; automatic CAUTION after boot; critical task monitoring dual-channel |
| FDIR | State Machine Logic | Incorrect state transition (false positive return) | Vehicle triggers early return; mission objective lost | 3 | 2 | 2 | **12** | Formal verification (TLA+); 10,000 simulation scenarios; hysteresis threshold (noise filter) |
| FDIR | Fault Detection Thresholds | Threshold too loose (missed fault) | Critical fault detected late; CAUTION may be skipped and SURVIVAL reached | 5 | 2 | 3 | **30** | Parameter validation test (threshold sweep); safety design: each threshold reviewed by 3 independent engineers |

---

### Module: Motion Control

| Module | Component | Failure Mode | Effect | Severity (S) | Occurrence (O) | Detection (D) | RPN | Mitigation |
|--------|-----------|--------------|--------|-------------|---------------|--------------|-----|-----------|
| Motion Control | Motor Driver | Motor driver failure (one wheel) | Vehicle cannot travel straight; manoeuvrability restricted | 3 | 3 | 2 | **18** | 4+ wheel differential drive; driver failure detected by motor current sensor in < 500 ms |
| Motion Control | Servo Controller | Servo jam (panel or antenna) | Panel cannot be oriented (energy drops) or antenna cannot be oriented (link weakens) | 3 | 2 | 2 | **12** | Fail-safe mechanism (servo locks at last safe position); manual override command (TC_IMMEDIATE) |
| Motion Control | Wheel Encoder | Encoder read error | Speed/position feedback incorrect → Local Planner issues erroneous motion command → collision risk | 4 | 2 | 2 | **16** | Cross-validation with IMU speed; on anomaly detection, encoder disabled, switch to IMU-only mode |

---

## Summary Analysis

### Top 3 Failure Modes by RPN

| Rank | Module | Failure Mode | RPN | Why Critical |
|------|--------|--------------|-----|-------------|
| 1 | Power Management | Sudden battery capacity drop | **30** | Return energy calculation incorrect → vehicle can become stranded in PSR |
| 2 | FDIR | Threshold too loose — missed critical fault | **30** | Critical state detected late → risk of rapidly reaching SURVIVAL |
| 3 | Navigation | IMU high drift | **24** | Localisation loss → vehicle must stop |

---

### Single-Point Failure List

The following components are non-redundant in the current design and cause immediate mission interruption if they fail:

| Component | Risk | Recommended Mitigation |
|-----------|------|----------------------|
| FDIR hardware watchdog | No safety decision when FDIR freezes | Dual-channel hardware watchdog or secondary processor |
| Main battery pack | Total power loss | Minimum two independent battery modules (parallel or backup) |
| Primary communication module | Link completely severed | Backup low-gain/UHF omni antenna (low bandwidth but maintains link) |
| IMU | Navigation completely blind | Backup MEMS IMU or strong visual odometry capability |

---

### Mission Loss vs Vehicle Loss Distinction

| Failure Category | Definition | Example Failure Modes |
|-----------------|------------|----------------------|
| **Mission Loss** | Vehicle safe but scientific objectives cannot be achieved | Panel deployment failure, servo jam, IMU drift, incorrect state transition |
| **Vehicle Loss** | Return from vehicle cannot be achieved or vehicle is damaged | Battery sudden capacity drop (inside PSR), critical heater failure (sub-zero environment), FDIR freeze (no watchdog) |
| **Data Loss** | Scientific data cannot be collected or transmitted | LiDAR contamination, communication loss (if buffering insufficient) |

**Priority:** Vehicle safety always takes precedence over mission objectives. Mission loss scenarios are acceptable; for vehicle loss scenarios, redundancy or software mitigation must always be defined.

---

## TBD Tracking List

| ID | TBD Parameter | Dependent Data |
|----|--------------|----------------|
| FMEA-TBD-001 | Sudden capacity drop probability will be updated once battery chemistry is determined | Battery selection |
| FMEA-TBD-002 | Drift value should be updated per IMU part selection | IMU part BoM |
| FMEA-TBD-003 | Heater failure probability will be updated as thermal environment (PSR minimum temperature) is determined | Thermal analysis |
| FMEA-TBD-004 | SEU-caused software failure probabilities will be added once radiation environment analysis is complete | Radiation analysis |

---

*This FMEA is in draft stage and will be updated as hardware selections are finalised. Every revision of the FMEA will be approved at a system design review meeting.*
