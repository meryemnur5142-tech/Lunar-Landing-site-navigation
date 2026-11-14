# status: draft
# owner: Agent C
# depends_on: [docs/qar/QAR_TABLE.md, tests/acceptance_criteria.md, simulation/simulator_design.md, simulation/scenarios/example_scenario.yaml, docs/adr/FMEA_KRITIK_MODULLER.md, infrastructure/risk_register.md]
# open_items: [TBD values awaiting §10 vehicle data; HIL test setup tied to P2 gate; FI references to remain consistent with simulation/simulator_design.md §5]

# Verification and Test Strategy — LUNA-AI v1.0

**Document ID:** LUNA-AI-TEST-001  
**Version:** 0.1-draft  
**Date:** 2026-11-14  
**Related Documents:** LUNA-AI-QAR-001, tests/acceptance_criteria.md, LUNA-AI-FMEA-001, LUNA-AI-SIM-001

---

## Verification Method Definitions

| Code | Method | Description |
|-----|--------|----------|
| **A** | Analysis | Analytical or mathematical verification; reference calculation or model comparison |
| **T** | Test | Runtime measurement; numerical target measurement on real or simulated system |
| **I** | Inspection | Code/design review; architectural inspection or dependency analysis |
| **D** | Demonstration | Systematic demonstration; end-to-end scenario execution |

## Test Environment Definitions

| Code | Environment | Description |
|-----|-------|----------|
| **UT** | Unit Test (pytest) | Module isolated; dependencies mocked/stubbed |
| **IT** | Integration Test | Two or more modules together; does not require FreeRTOS |
| **SIL** | Software-in-the-Loop | All software on host computer; environment + vehicle model simulated |
| **HIL** | Hardware-in-the-Loop | Real OBC + sensors; simulator provides environment |
| **FT** | Field Test | Real vehicle + real lunar surface (post-P3+) |
| **TVAC** | Thermal Vacuum Test | Real temperature/vacuum environment |

---

## QAR Verification Table

### FDIR — Fault Detection, Isolation and Recovery

| Requirement ID | Module | Attribute | Numerical Target | Verification Method | Test Environment | Acceptance Criterion | Owner |
|--------------|-------|---------|---------------|-------------------|-------------|---------------|---------|
| FDIR-001 | FDIR | Anomaly Detection Time | < 50 ms (P95) | T — FI-001..010 anomaly injection; timestamp delta measurement | SIL (RT-002..006), HIL (P3) | 95th percentile ≤ 50 ms; zero missed detections for critical faults (cross-check with FDIR-004) | safety/fdir |
| FDIR-002 | FDIR | Recovery Decision Time | < 500 ms from anomaly detection | T — anomaly detection timestamp → `abort_signal=true` [ICD-004] timestamp delta | SIL (RT-002..006), HIL (P3) | 95% of cases ≤ 500 ms; `fdir_confidence` ≥ 80 | safety/fdir |
| FDIR-003 | FDIR | False Positive Rate | < 1% per nominal operation hour | T — 100-hour nominal SIL run; false alarm count | SIL (RT-001 extended) | Total false alarms / total nominal hours < 0.01 | safety/fdir |
| FDIR-004 | FDIR | False Negative Rate | < 0.1% (zero target for critical faults) | T — 50 repetitions per each FMEA-top-10 fault mode; FDIR detection rate | SIL (RT-002..006 + additional), HIL (P3-AC-02) | Detection rate = 100% for each critical fault mode | safety/fdir |
| FDIR-005 | FDIR | State Machine Transition Consistency | 100% deterministic | A + T — TLA+ formal verification + 1000-repetition SIL test: same input = same transition | UT (P0-AC-03), SIL | Formal verification: no invariant violations; 1000 tests: zero inconsistent transitions | safety/fdir |

### NAV — Navigation

| Requirement ID | Module | Attribute | Numerical Target | Verification Method | Test Environment | Acceptance Criterion | Owner |
|--------------|-------|---------|---------------|-------------------|-------------|---------------|---------|
| NAV-001 | Navigation | Position Accuracy (flat terrain) | < 0.5 m RMS | T — 50 measurements over known DEM reference points; EKF output vs reference | SIL (P1-AC-04), HIL (P3-AC-01) | σ_pos < 0.5 m RMS, within 95% confidence interval | vehicle/localization |
| NAV-002 | Navigation | Orientation Accuracy | < 0.5° RMS (yaw/pitch/roll) | T — reference orientation comparison; 100 samples | SIL, HIL | σ_yaw, σ_pitch, σ_roll < 0.5° RMS | vehicle/localization |
| NAV-003 | Navigation | Position Update Frequency | ≥ 10 Hz while moving, ≥ 1 Hz stop-wait | T — ICD-003 `vehicle_pose` message timestamp analysis | UT, SIL | While moving: dt between messages ≤ 100 ms; stop-wait: dt ≤ 1 s | vehicle/localization |
| NAV-004 | Navigation | Localisation Loss Detection | < 2 s (EKF divergence → alarm) | T — FI-001/FI-009 injection; detection timestamp measurement | SIL (RT-003/CT-005), HIL | ≤ 2 s in all 20 divergence scenarios; zero missed detections | vehicle/localization |
| NAV-005 | Navigation | Dead-Reckoning Drift | < 2 m/min (IMU-only) | T — closed-loop measurement over known path with FI-001 (IMU noise increase) | SIL | Cumulative error < 2 m after 1 minute of dead-reckoning | vehicle/localization |
| NAV-006 | Navigation | In-PSR Navigation Accuracy | < 1.0 m RMS (when visual landmarks reduced) | T — 20 PSR traversal scenarios; LiDAR-only or IMU+odometry mode | SIL (CT-005, PSR scenarios) | σ_pos < 1.0 m RMS, without landmark matching inside PSR | vehicle/localization |

### PLAN — Mission Planner

| Requirement ID | Module | Attribute | Numerical Target | Verification Method | Test Environment | Acceptance Criterion | Owner |
|--------------|-------|---------|---------------|-------------------|-------------|---------------|---------|
| PLAN-001 | Mission Planner | Global Route Computation Time | < 60 s (500m path, A*) | T — 10 different terrain profiles; mean and P99 computation time | SIL (P2-AC-01) | 95% of cases < 60 s; P99 < 90 s | autonomy/global-planner |
| PLAN-002 | Mission Planner | Replanning Time | < 30 s (after instantaneous obstacle) | T — SIL obstacle injection → replanning completion time; 50 scenarios | SIL (P2-AC-02, CT-003) | 95% of cases < 30 s | autonomy/replanner |
| PLAN-003 | Mission Planner | Energy Budget Estimation Error | < 10% (planned vs actual) | T — 20 nominal mission runs; plan_energy vs sim_energy comparison | SIL (CT-002), Digital Twin | |plan_energy - actual_energy| / plan_energy × 100 < 10% | power + autonomy |
| PLAN-004 | Mission Planner | PSR Entry Condition Evaluation Time | < 10 s | T — 50 PSR entry scenarios; decision generation time measurement | SIL | 100% of scenarios < 10 s | autonomy/global-planner |
| PLAN-005 | Mission Planner | Return Trigger Computation Frequency | ≥ 1 Hz (continuous return margin monitoring) | T — `estimated_return_soc_pct` update timestamp analysis [ICD-001] | UT, SIL | Update interval ≤ 1 s at all times | power |

### PWR — Power Management

| Requirement ID | Module | Attribute | Numerical Target | Verification Method | Test Environment | Acceptance Criterion | Owner |
|--------------|-------|---------|---------------|-------------------|-------------|---------------|---------|
| PWR-001 | Power Management | Min. Return SoC Reserve | ≥ 15% SoC (at safe haven gate) | T — SoC recorded at safe haven arrival for each mission run | SIL (P2-AC-04, CT-002), HIL | SoC ≥ 15% at safe haven gate; single violation = failed | power |
| PWR-002 | Power Management | Energy Estimation Error | < 10% (for remaining time/distance) | T + A — Digital twin: 50 mission scenarios; estimate vs actual comparison | SIL (CT-002), Digital Twin | Mean error < 5%; max error < 10% | power |
| PWR-003 | Power Management | Load Shedding Response Time (Critical) | < 100 ms (command → actual cut) | T — HIL: command timestamp vs current sensor measurement; FI-010 (PDU test) | HIL (P3) | 100% of critical shedding commands ≤ 100 ms | power |
| PWR-004 | Power Management | Load Shedding Response Time (SURVIVAL) | < 10 ms (SURVIVAL mode optional loads) | T — HIL: SURVIVAL transition → all optional load shedding time | HIL (P3) | 100% SURVIVAL shedding ≤ 10 ms | power |
| PWR-005 | Power Management | SoC Measurement Accuracy | ±TBD% (target: ±2%; chemistry-dependent) | T — Calibration test: known capacity Wh comparison; voltage + Coulomb dual measurement | HIL, TVAC (P3) | |SoC_measured - SoC_true| ≤ TBD-BAT-002 dependent threshold | power |
| PWR-006 | Power Management | Panel Efficiency Monitoring Period | ≤ 10 s update | T — `panel_power_w` message timestamp analysis [ICD-001] | UT, SIL | Update interval ≤ 10 s at all times | power |

### THM — Thermal Management

| Requirement ID | Module | Attribute | Numerical Target | Verification Method | Test Environment | Acceptance Criterion | Owner |
|--------------|-------|---------|---------------|-------------------|-------------|---------------|---------|
| THM-001 | Thermal Management | Temperature Monitoring Period | ≤ 1 s (all critical sensors) | T — `thermal_state` update timestamp analysis [ICD-002]; for all sensor_ids | UT, SIL | Each critical sensor: update interval ≤ 1 s | thermal |
| THM-002 | Thermal Management | Heater Activation Delay | < 5 s (command → heating start) | T — HIL: temperature threshold crossing → heater activation; test with FI-007 | SIL (CT-006), HIL (P3) | 100% of activation commands ≤ 5 s | thermal |
| THM-003 | Thermal Management | Thermal Critical Detection Time | < 2 s (threshold violation → FDIR alarm) | T — FI-007 injection; detection timestamp measurement | SIL (RT-005, CT-006), HIL | 100% of critical thermal events ≤ 2 s forwarded to FDIR | thermal |
| THM-004 | Thermal Management | Min. Operating Temperature (Electronics) | TBD-THM-001/003 — dependent on component selection | T — TVAC: cold qualification test | TVAC (P3) | All components operating nominally at min temperature (TBD-THM-003 threshold) | thermal |
| THM-005 | Thermal Management | Max. Operating Temperature (Electronics) | TBD-THM-001/003 — dependent on component selection | T — TVAC: hot qualification test | TVAC (P3) | All components operating nominally at max temperature (TBD-THM-003 threshold) | thermal |

### COM — Communication

| Requirement ID | Module | Attribute | Numerical Target | Verification Method | Test Environment | Acceptance Criterion | Owner |
|--------------|-------|---------|---------------|-------------------|-------------|---------------|---------|
| COM-001 | Communication | Command Processing Delay | < 500 ms (command received → executed) | T — End-to-end delay measurement; 100 TC_IMMEDIATE + 100 TC_PLAN_UPLOAD | SIL (CT-004), HIL (P3) | 95% of cases ≤ 500 ms; TC_IMMEDIATE commands 100% ≤ 500 ms | communication |
| COM-002 | Communication | Telemetry Update Period (Nominal) | ≤ 10 s | T — ICD-006 downlink timestamp analysis; under nominal safety state | SIL, HIL | Update interval ≤ 10 s, nominal conditions | communication |
| COM-003 | Communication | Telemetry Update Period (Critical State) | ≤ 1 s (CAUTION or above) | T — Update frequency check after state transition triggered | SIL (CT-004), HIL | In CAUTION+ state: update interval ≤ 1 s | communication |
| COM-004 | Communication | Autonomous Operation Duration (No Link) | ≥ TBD-COM-002 hours | D — FI-006 link loss; SC-002/SC-007 scenarios; vehicle pre-planned protocol | SIL (CT-004), HIL | Vehicle stayed within safety boundaries; pre-planned abort triggers correctly fired | communication |
| COM-005 | Communication | Command Integrity (CRC) | 100% single bit flip detection | T — 10,000 corrupted packet scenarios; CRC error detection rate | UT, SIL | 100% of corrupted packets rejected; zero corrupted packets accepted | communication |
| COM-006 | Communication | Link Reconnection Time | < TBD-COM-003 minutes | T — SIL link simulation: connection time when link window reopens | SIL (CT-004) | 95% reconnection ≤ TBD-COM-003; ground telemetry updated | communication |

### SHV — Safe Haven

| Requirement ID | Module | Attribute | Numerical Target | Verification Method | Test Environment | Acceptance Criterion | Owner |
|--------------|-------|---------|---------------|-------------------|-------------|---------------|---------|
| SHV-001 | Safe Haven | Min. Illumination Duration | ≥ TBD hours/day (energy sufficiency) | A — SPICE orbital simulation; illumination analysis for selected region (AC-VAL-001..004) | Analysis + SIL | Daily illumination at selected safe haven ≥ energy budget requirement | mission_intelligence |
| SHV-002 | Safe Haven | Min. Return Energy Reserve | ≥ 15% SoC (at safe haven gate) | T — SoC recorded at safe haven arrival for each mission run (overlaps PWR-001) | SIL, HIL | SoC ≥ 15%; HC-006 violation = failed | power |
| SHV-003 | Safe Haven | Arrival Time (Nominal) | ≤ TBD minutes (max distance) | T — Navigation simulation: return from furthest mission point at nominal speed | SIL (CT-003) | 95% of scenarios ≤ TBD-TRV-001/TBD-TRV-002 dependent threshold | autonomy/global-planner |
| SHV-004 | Safe Haven | Arrival Time (SURVIVAL mode) | ≤ TBD minutes (minimum energy route) | T — SURVIVAL mode simulation; FI-005+FI-003 combination | SIL (CT-007) | Vehicle reached safe haven in SURVIVAL mode; SoC > 0% | autonomy/global-planner |
| SHV-005 | Safe Haven | Ground Slope Tolerance | ≤ TBD° (safe parking) | A + T — Terrain map slope analysis + vehicle stability analysis | Analysis, SIL | Slope at selected safe haven locations ≤ HC-001 slope limit (TBD-TRV-002) | mission_intelligence |

---

## Critical Test Scenarios

The following 7 critical test scenarios have priority in QAR verification. Each scenario is linked to FI-* references in `simulation/simulator_design.md` §5.

### CT-001: FDIR Response Time — Anomaly Injection

**Target QAR:** FDIR-001, FDIR-002, FDIR-004  
**Linked FI:** FI-001 (IMU noise), FI-005 (sudden SoC drop), FI-007 (heater open circuit), FI-008 (FDIR task freeze)  
**Test Environment:** SIL (P1/P2), HIL (P3)

```
Procedure:
1. Run nominal SCN-001 baseline run (RT-001).
2. Inject FI-XXX at time t0.
3. Record FDIR anomaly detection timestamp (t1).
4. Record FDIR abort_signal=true timestamp (t2) [ICD-004].
5. Calculate: detection_latency = t1 - t0; decision_latency = t2 - t1.
Acceptance: detection_latency ≤ 50 ms (P95), decision_latency ≤ 500 ms (P95).
Repetitions: 50 independent runs per FI type.
Reference regression: RT-002, RT-005, RT-006.
```

### CT-002: Energy Budget Estimation Accuracy — Simulated PSR Traversal

**Target QAR:** PLAN-003, PWR-001, PWR-002  
**Linked FI:** FI-005 (sudden SoC drop — worst-case)  
**Test Environment:** SIL (Digital Twin), SC-003

```
Procedure:
1. PSR traversal scenario: entry SoC 85%, TBD distance inside PSR.
2. Record planner's initial estimated return_reserve_wh and actual SoC at safe haven gate.
3. Calculate: estimation_error = |estimate - actual| / estimate × 100%.
4. 20 independent runs (different terrain and energy consumption variation).
Acceptance: Mean estimation error < 5%; max < 10%.
             SoC at safe haven gate ≥ 15% (PWR-001).
Reference regression: RT-002.
```

### CT-003: Safe Haven Selection Accuracy — Known Optimum Comparison

**Target QAR:** SHV-001..005, PLAN-002  
**Linked FI:** None (terrain injection present)  
**Test Environment:** SIL (SC-005)

```
Procedure:
1. Test scenario: Primary safe haven route blocked (SC-005 — route injection).
2. Candidate safe havens evaluated across 7 criteria.
3. Reference solution: Expert manually computed optimum safe haven coordinates.
4. Compare system decision against reference solution.
5. 10 different blocking configurations + edge cases with 1 of 7 criteria at different weight.
Acceptance: System selection matches reference with 80%+ overlap; candidate containing HC violation never selected.
Reference: operational_scenarios.md SC-005 §3 7-criteria list.
```

### CT-004: Autonomous Behaviour Under Communication Disruption — Link Drop Simulation

**Target QAR:** COM-001, COM-003, COM-004, COM-006  
**Linked FI:** FI-006 (link loss)  
**Test Environment:** SIL (SC-002, SC-007)

```
Procedure — SURFACE_EXPLORATION scenario:
1. FI-006: Link cut at t0. Duration: TBD-COM-002 warning threshold / 2× warning threshold / critical threshold.
2. FDIR CAUTION trigger detection time recorded.
3. Pre-planned abort trigger list (ABT-001..006) checked.
4. CAUTION → NOMINAL transition time recorded when link returns.
Procedure — PSR_OPS scenario:
5. FI-006 injection inside PSR → RETURN_REQUIRED must trigger.
6. ACL return route must start; no ground approval awaited.
Acceptance: State transitions comply with SC-002 protocol; vehicle did not leave pre-planned boundaries.
            Ground telemetry updated ≤ 1 s when link returns (COM-003).
Reference regression: RT-004.
```

### CT-005: Localisation Loss Recovery — IMU Drift Injection

**Target QAR:** NAV-001, NAV-004, NAV-005, NAV-006  
**Linked FI:** FI-001 (IMU noise increase), FI-002 (IMU bias shift), FI-009 (EKF init error)  
**Test Environment:** SIL (SC-004), HIL (P3)

```
Procedure:
1. Inject FI-001 or FI-002 during nominal traversal.
2. Monitor EKF covariance: FDIR notification time when uncertainty_m exceeds threshold (> 1.0 m).
3. Observe FDIR Detection → Isolation → Recovery steps.
4. Recovery successful: landmark search → σ_pos < 0.5 m → return to NOMINAL.
5. Recovery unsuccessful: RETURN_REQUIRED must trigger; return with IMU-only navigation.
Acceptance: Detection ≤ 2 s (NAV-004); dead-reckoning drift < 2 m/min (NAV-005).
             CAUTION → RETURN_REQUIRED transition correctly triggered (SC-004 step 8).
Reference regression: RT-003.
```

### CT-006: PSR Traversal Thermal Budget — Extended Darkness Simulation

**Target QAR:** THM-001, THM-002, THM-003, SHV-001  
**Linked FI:** FI-007 (heater open circuit — worst-case)  
**Test Environment:** SIL (SC-006, PSR thermal scenario)

```
Procedure:
1. Vehicle stays inside PSR for TBD hours (longest lunar night simulation).
2. Heaters operating nominally: monitor temperature profile.
3. t_mid: Inject FI-007 (one heater failure) → FDIR thermal critical detection time.
4. Fallback heater activation → monitor temperature stabilisation.
5. Lowest SoC point recorded.
Acceptance: No critical component dropped below minimum operating temperature.
             THM-003: Critical detection ≤ 2 s.
             THM-002: Fallback heater activation ≤ 5 s.
             SoC return reserve ≥ 15% maintained.
```

### CT-007: Multiple Simultaneous Faults — Combined Failure

**Target QAR:** FDIR-001..004, PWR-001, NAV-001, THM-003  
**Linked FI:** FI-005 + FI-001 + FI-006 combination  
**Linked RPN:** FMEA-RPN-PWR-001 (30) + FMEA-RPN-NAV-001 (24) combination  
**Test Environment:** SIL (RT-002 + RT-003 + RT-004 combination)

```
Procedure:
1. Nominal PSR operation.
2. t=0: FI-001 (IMU noise increase 3×)
   t=30s: FI-006 (link loss)
   t=60s: FI-005 (sudden SoC drop 20%)
3. FDIR must correctly select highest-priority trigger:
   SoC drop (HC-006) → RETURN_REQUIRED (most critical).
4. FDIR must make one consistent decision under multiple faults.
5. Vehicle must initiate abort and return to safe haven.
Acceptance: FDIR behaving deterministically under multiple triggers (FDIR-005).
             Highest-priority trigger selected (SoC > link > nav, context-dependent).
             Vehicle reached safe haven with SoC ≥ 15%.
Reference regression: RT-002, RT-003, RT-004 (separately); this scenario is additional CT.
```

---

## Regression Test Suite

Minimum test set to run automatically on each PR.

### Current Unit Test Reference

`tests/unit/test_models.py` — 29 unit tests covering the following areas:

| Test Group | Coverage | QAR Relation |
|------------|--------|--------------|
| `ScoringWeights` sum 1.0 | Target scoring consistency | PLAN verification base |
| `HardConstraintEvaluator` pass/fail | HC-001..015 engine | P0-AC-02 (30 HC tests) |
| `DataProductMetadata` mandatory fields | temporal_class, resolution_m | P0-AC-06, P0-AC-07 |
| `LandingSiteCandidate` structure | Area constraints | SHV verification base |
| `BoundingBox` construction | Coordinate consistency | NAV verification base |
| `CraterRecord` construction | Data model integrity | Scientific data platform |

**Target:** Current 29 tests 100% passing; this count does not decrease after each PR.

### PR Regression Suite Definition

| Level | Test | Environment | Duration (estimated) | Trigger |
|--------|------|-------|----------------|-------------|
| L1 — Every PR | 29 current unit tests | UT (pytest) | < 2 min | Every commit |
| L1 — Every PR | P0-AC-01..07 (ICD schema, HC engine, state machine) | UT | < 5 min | Every commit |
| L2 — Before merge | RT-001 (nominal SCN-001 run) | SIL | < 15 min | PR merge approval |
| L2 — Before merge | RT-002 (PSR energy drop, FI-005) | SIL | < 10 min | PR merge approval |
| L2 — Before merge | RT-003 (localisation loss, FI-001) | SIL | < 10 min | PR merge approval |
| L2 — Before merge | RT-004 (link loss PSR, FI-006) | SIL | < 10 min | PR merge approval |
| L2 — Before merge | RT-005 (thermal critical, FI-007) | SIL | < 10 min | PR merge approval |
| L2 — Before merge | RT-006 (FDIR watchdog freeze, FI-008) | SIL | < 5 min | PR merge approval |
| L3 — Weekly | CT-001..007 full scenario set | SIL | < 2 hours | Weekly CI |
| L4 — Phase gate | P0-AC..P2-AC full set | SIL + IT | < 4 hours | Phase transition gate |

### Pass / Fail Criteria

| Status | Criterion | Outcome |
|-------|--------|-------|
| **Pass** | All L1 + L2 tests green | PR merge approval may be given |
| **Red flag** | Any L1 test failed | PR merge blocked; bug must be fixed |
| **Red flag** | Any L2 FDIR/safety test failed | PR merge blocked |
| **Yellow flag** | L2 performance test (PLAN-001/002) threshold exceeded | Acceptable; added to risk register |
| **Phase gate block** | Any L4 AC failed | Phase transition blocked |

### Metric Collection

The following metrics are logged on each CI run:

```yaml
regression_metrics:
  - safety_state_transitions_correct: bool
  - fdir_detection_latency_p95_ms: float
  - fdir_decision_latency_p95_ms: float
  - soc_min_pct: float
  - nav_uncertainty_max_m: float
  - thermal_min_temp_c: float
  - plan_energy_error_pct: float
  - waypoints_reached_count: int
  - false_alarm_count: int
```

---

## Repository Validation Acceptance Criteria (AC-VAL-001..005)

Source: `tests/acceptance_criteria.md` §Repository Validation Acceptance Criteria (B4-EK).

| Criterion ID | Criterion | Source | Target | Test Environment | QAR Relation |
|-----------|--------|--------|-------|-------------|--------------|
| AC-VAL-001 | Sun/Earth angles consistent with JPL Horizons | JPL Horizons | Within ±0.001° | Analysis | SHV-001, COM-004 (link window) |
| AC-VAL-002 | Illumination fraction correlation with NASA GSFC | NASA GSFC | r ≥ 0.988, RMS ≤ 2.7 points | Analysis + SIL | SHV-001, P1-AC-01 |
| AC-VAL-003 | Earth visibility correlation with NASA GSFC | NASA GSFC | r ≥ 0.993 | Analysis | COM-004, RR-014 |
| AC-VAL-004 | Shackleton ridge illumination: 2m observer 92.29%, 10m observer 95.69% | Gläser et al. (2014) | Within ±0.05 points | Analysis | P1-AC-01, SHV-001 |
| AC-VAL-005 | Resolution validation report: 80m vs 20m vs 300m difference analysis | B3-EK RR-011/015 | Report delivered + approved | Analysis | NAV-006, PLAN-001 |

**Phase application:** AC-VAL-001..004 is a P1 gate condition. AC-VAL-005 is within the P1 exit report scope.

---

## Verification Traceability Matrix (Summary)

| Verification Method | QAR Count Covered | Test Environment | Phase |
|-------------------|--------------------|-----------|----|
| Analysis (A) | SHV-001, SHV-005, AC-VAL-001..005 | — | P1 |
| Unit Test (T/UT) | FDIR-005, NAV-003, PWR-005/006, THM-001, COM-002/005 | pytest | P0 |
| Integration Test (IT) | P0-AC-01..07 combination | IT | P0 |
| SIL (T/D/SIL) | FDIR-001..004, NAV-001/004..006, PLAN-001..005, PWR-001..003, THM-002/003, COM-001/003/004/006, SHV-002..004 | SIL | P1/P2 |
| HIL (T/HIL) | FDIR-001/002, NAV-001, PWR-003/004, THM-004/005, COM-001 | HIL | P3 |
| TVAC (T) | THM-004, THM-005, PWR-005 | TVAC | P3 |

---

## Revision History

| Version | Date | Change |
|----------|-------|------------|
| 0.1 | 2026-11-14 | First draft — Agent C, C4 task; 30 QAR items, 7 critical scenarios, regression suite |
