# LUNA-AI Quality Attribute Requirements (QAR) Table

**Document ID:** LUNA-AI-QAR-001  
**Version:** 0.1-draft  
**Date:** 2026-11-14  
**Status:** Draft — Hardware parameters TBD

---

## Abbreviations Used

| Abbreviation | Description |
|----------|----------|
| RMS | Root Mean Square |
| SoC | State of Charge |
| FDIR | Fault Detection, Isolation and Recovery |
| HIL | Hardware-in-the-Loop |
| EKF | Extended Kalman Filter |
| TBD | To Be Determined |

---

## QAR Priority Scale

| Priority | Description |
|---------|----------|
| **P1** | Safety critical — violation leads to mission abort or vehicle loss |
| **P2** | Mission critical — violation prevents reaching mission objectives |
| **P3** | Performance critical — violation reduces mission efficiency |
| **P4** | Desiderata — improvement beyond target |

---

## QAR Table

| ID | Module | Attribute | Numerical Target | Measurement Method | Priority |
|----|-------|---------|---------------|---------------|---------|
| **FDIR-001** | FDIR | Anomaly Detection Time | < 50 ms (P95) | HIL injection: measurement across 100 scenarios | P1 |
| **FDIR-002** | FDIR | Recovery Decision Time | < 500 ms from anomaly detection | HIL: delay measurement between anomaly → decision | P1 |
| **FDIR-003** | FDIR | False Positive Rate | < 1% per nominal operation hour | 100-hour nominal simulation, false alarm count | P2 |
| **FDIR-004** | FDIR | False Negative Rate | < 0.1% (zero target for critical faults) | Fault injection test: at least 50 tests per critical fault mode | P1 |
| **FDIR-005** | FDIR | State Machine Transition Consistency | 100% deterministic (same input → same transition) | Formal verification + 1000 repetition test | P1 |
| **NAV-001** | Navigation | Position Accuracy (flat terrain) | < 0.5 m RMS | 50 measurements over known reference points, RTK comparison | P1 |
| **NAV-002** | Navigation | Orientation Accuracy | < 0.5° RMS (yaw/pitch/roll) | Star-tracker comparison, 100 samples | P1 |
| **NAV-003** | Navigation | Position Update Frequency | ≥ 10 Hz (while moving), ≥ 1 Hz (stop-wait) | Data stream timestamp analysis | P2 |
| **NAV-004** | Navigation | Localisation Loss Detection | < 2 seconds (EKF divergence → alarm) | HIL: EKF divergence scenario | P1 |
| **NAV-005** | Navigation | Dead-Reckoning Drift | < 2 m/min (IMU alone, no slip sensor) | Closed-loop measurement over known path | P2 |
| **NAV-006** | Navigation | In-PSR Navigation Accuracy | < 1.0 m RMS (when visual landmarks reduced) | LiDAR-only simulation, 20 PSR scenarios | P2 |
| **PLAN-001** | Mission Planner | Global Route Computation Time | < 60 seconds (500m path, A* algorithm) | Simulation: 10 different terrain profiles, mean and P99 | P2 |
| **PLAN-002** | Mission Planner | Replanning Time | < 30 seconds (after instantaneous obstacle detection) | HIL: unexpected obstacle injection | P2 |
| **PLAN-003** | Mission Planner | Energy Budget Estimation Error | < 10% (planned vs actual energy consumption) | Plan-actual comparison over 20 nominal mission days | P2 |
| **PLAN-004** | Mission Planner | PSR Entry Condition Evaluation Time | < 10 seconds | Simulation: 50 entry scenarios | P1 |
| **PLAN-005** | Mission Planner | Return Trigger Computation Frequency | ≥ 1 Hz (continuous return margin monitoring) | Data stream period measurement | P1 |
| **PWR-001** | Power Management | Minimum Return SoC Reserve | ≥ 15% SoC (at safe haven gate) | Recorded each mission day; violation = P1 anomaly | P1 |
| **PWR-002** | Power Management | Energy Estimation Error | < 10% (for remaining time/distance) | Digital twin simulation, 50 mission day scenarios | P2 |
| **PWR-003** | Power Management | Load Shedding Response Time | < 100 ms (critical load cut command → actual cut) | HIL measurement: command timestamp vs current sensor | P1 |
| **PWR-004** | Power Management | Load Shedding Response Time (Survival) | < 10 ms (all optional loads in SURVIVAL mode) | HIL measurement | P1 |
| **PWR-005** | Power Management | SoC Measurement Accuracy | **TBD:** ±% — dependent on battery chemistry; target: 2% | Calibration test: known capacity comparison | P1 |
| **PWR-006** | Power Management | Panel Efficiency Monitoring | Update period ≤ 10 seconds | Data stream timestamp analysis | P3 |
| **THM-001** | Thermal Management | Temperature Monitoring Period | ≤ 1 second (all critical sensors) | Telemetry stream period validation | P1 |
| **THM-002** | Thermal Management | Heater Activation Delay | < 5 seconds (command → actual heating start) | HIL: temperature threshold crossing → activation time | P1 |
| **THM-003** | Thermal Management | Thermal Critical Detection Time | < 2 seconds (temperature threshold violation → FDIR alarm) | HIL injection: sudden temperature increase scenario | P1 |
| **THM-004** | Thermal Management | Min. Operating Temperature (Electronics) | **TBD:** °C — dependent on component selection | Thermal vacuum test (TVAC) | P1 |
| **THM-005** | Thermal Management | Max. Operating Temperature (Electronics) | **TBD:** °C — dependent on component selection | TVAC | P1 |
| **COM-001** | Communication | Command Processing Delay | < 500 ms (command received → executed) | End-to-end delay measurement, 100 tests | P2 |
| **COM-002** | Communication | Telemetry Update Period (Nominal) | ≤ 10 seconds | Timestamp analysis | P2 |
| **COM-003** | Communication | Telemetry Update Period (Critical State) | ≤ 1 second (CAUTION or above) | Update frequency after state transition | P1 |
| **COM-004** | Communication | Autonomous Operation Duration (No Link) | ≥ **TBD:** hours (full mission day expectation) | Simulation: link cut, mission continues | P1 |
| **COM-005** | Communication | Command Integrity (CRC Error Detection) | 100% (single bit flip detection guaranteed) | CRC test: 10,000 corrupted packet scenarios | P1 |
| **COM-006** | Communication | Link Reconnection Time | < **TBD:** minutes (when link window reopens) | Test environment link simulation | P2 |
| **SHV-001** | Safe Haven | Minimum Illumination Duration | ≥ **TBD:** hours/day (for solar energy sufficiency) | Orbital mechanics simulation (SPICE) | P1 |
| **SHV-002** | Safe Haven | Minimum Return Energy Reserve (at Safe Haven gate) | ≥ 15% SoC | Measured each mission day | P1 |
| **SHV-003** | Safe Haven | Safe Haven Arrival Time (Nominal) | ≤ **TBD:** minutes (for maximum distance) | Navigation simulation: from furthest mission point | P1 |
| **SHV-004** | Safe Haven | Safe Haven Arrival Time (SURVIVAL mode) | ≤ **TBD:** minutes (minimum energy route) | SURVIVAL mode simulation | P1 |
| **SHV-005** | Safe Haven | Ground Slope Tolerance | ≤ **TBD:** ° (for safe parking) | Terrain map + power/thermal analysis | P2 |

---

## Measurement Method Dictionary

| Method | Description |
|--------|----------|
| **HIL** | Real flight software + simulated hardware; fault-injected scenarios |
| **Digital Twin Simulation** | Monte Carlo or scenario-based testing on full system model |
| **Formal Verification** | State machine consistency via model checking (e.g. TLA+, SPIN) |
| **TVAC** | Thermal Vacuum Chamber — testing in real temperature/vacuum environment |
| **Data Stream Analysis** | Period and delay measurement from runtime telemetry |

---

## TBD Tracking List

The following QAR values are awaiting hardware/terrain data:

| QAR ID | TBD Parameter | Dependent Data |
|--------|----------------|--------------|
| PWR-005 | SoC measurement tolerance | Battery chemistry selection |
| THM-004/005 | Min/Max electronics temperature | Electronics parts list (BoM) |
| COM-004 | Autonomous operation duration | Mission profile + link analysis |
| COM-006 | Reconnection time | Orbital mechanics simulation |
| SHV-001 | Min illumination duration | SPICE orbital simulation |
| SHV-003/004 | Safe haven arrival times | Vehicle speed + energy profile |
| SHV-005 | Ground slope tolerance | Vehicle mechanical design |

---

*QAR values will be reviewed during the hardware integration phase and cross-checked against the SRS (System Requirements Specification).*
