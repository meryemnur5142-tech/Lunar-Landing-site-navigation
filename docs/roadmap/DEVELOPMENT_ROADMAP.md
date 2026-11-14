# status: draft
# owner: Agent C
# depends_on: [config/tbd_register.md, tests/acceptance_criteria.md, docs/qar/QAR_TABLE.md, docs/adr/FMEA_KRITIK_MODULLER.md, infrastructure/risk_register.md, tests/verification_strategy.md]
# open_items: [P2/P3 estimated durations depend on §10 vehicle data and Agent D work rate; TBD gates tracked from config/tbd_register.md]

# LUNA-AI Development Roadmap — P0–P3

**Document ID:** LUNA-AI-ROAD-001  
**Version:** 0.1-draft  
**Date:** 2026-11-14  
**Related Documents:** LUNA-AI-TEST-001 (Verification Strategy), tests/acceptance_criteria.md, config/tbd_register.md

---

## Roadmap Summary

```
Pre-Phase  COMPLETE
P0         COMPLETE (partially — lunar-navigator submodule pending)
P1         IN PROGRESS — Agent B/C outputs delivered; ODE/SPICE integration pending
P2         IN PROGRESS — Agent D (on feature/faz2-otonomi branch)
P3         NOT STARTED — awaiting §10 vehicle data
```

**Important Note:** P2 → P3 gate requires 6 critical TBDs to be closed. These TBDs cannot be closed without §10 vehicle engineering data.

---

## Pre-Phase — Concept and Design Foundation — COMPLETE

**Status:** Complete  
**Branch:** main (merged)

### Completed Outputs

| Output | Document | Status |
|-------|-------|-------|
| Operational Concept (ConOps) | `docs/conops/CONOPS.md` | DONE |
| Quality Attribute Requirements (QAR) | `docs/qar/QAR_TABLE.md` (30 items) | DONE |
| Critical Modules FMEA | `docs/adr/FMEA_KRITIK_MODULLER.md` (top-10 RPN) | DONE |
| Architecture Decision Records | `docs/adr/ADR-001..006` | DONE |
| Hard Constraints Catalogue | `domain/mission/constraints/hard_constraints_catalog.md` (18 HC) | DONE |
| Phase State Machine | `domain/mission/phase_state_machine.md` | DONE |
| Safety State Machine Design | `docs/architecture/SAFETY_STATE_MACHINE.md` | DONE |
| ICD Templates | `docs/architecture/ICD_TEMPLATES.md` (ICD-001..006) | DONE |
| Safety Budget | `safety/safety_budget.md` | DONE |
| Autonomy Matrix | `autonomy/autonomy_matrix.md` | DONE |
| Risk Register | `infrastructure/risk_register.md` (15 risks) | DONE |
| Operational Scenarios | `simulation/scenarios/operational_scenarios.md` (SC-001..009) | DONE |
| Acceptance Criteria | `tests/acceptance_criteria.md` (P0-P3 AC + AC-VAL-001..005) | DONE |
| TBD Register | `config/tbd_register.md` (44+ TBDs) | DONE |

---

## P0 — Architecture Foundation — LARGELY COMPLETE

**Status:** Largely complete; one item pending  
**Branch:** main (merged)  
**Acceptance Criteria:** `tests/acceptance_criteria.md` P0-AC-01..07

### Completed Outputs

| Output | Document / Module | Status |
|-------|---------------|-------|
| ICD Schemas (10 JSON Schemas) | `interfaces/schemas/*.schema.yaml` | DONE |
| Python TypedDict + JSON Schema compatibility | `interfaces/v1/energy_state.py`, `thermal_state.py`, `vehicle_pose.py` | DONE |
| Redundancy Matrix | `docs/architecture/redundancy_matrix.md` | DONE |
| Safety State Machine (PlantUML) | `docs/architecture/PLANTUML_DIAGRAMS.md` (Diagram 5) | DONE |
| Hard Constraints Python engine | `mission_intelligence/constraints/hard_constraints.py` | DONE |
| Energy state contract | `interfaces/v1/energy_state.py` | DONE |
| Thermal state contract | `interfaces/v1/thermal_state.py` | DONE |
| Vehicle pose contract | `interfaces/v1/vehicle_pose.py` | DONE |
| Component + Deployment + Sequence Diagrams | `docs/architecture/PLANTUML_DIAGRAMS.md` (Diagrams 1-4) | DONE |

### Pending Item

| Item | Dependency | Status |
|-------|-----------|-------|
| lunar-navigator submodule connection | TBD-REPO-001: submodule vs reference directory decision | PENDING |

### Entry Conditions (Met)

- Pre-phase all outputs delivered.
- Project context and technical constraints documented.

### Exit Criteria

- P0-AC-01..07 unit tests green (current 29 unit tests + ICD schema tests)
- All module interfaces conformant to ICD schema
- HC engine evaluating HC-001..015 set
- lunar-navigator integration decision (after TBD-REPO-001 closed) — pending

### Critical Dependencies

| Dependency | Source | Status |
|-----------|--------|-------|
| TBD-REPO-001 (submodule vs reference) | Project decision | OPEN |

---

## P1 — Scientific Platform — IN PROGRESS

**Status:** Core outputs delivered; integration items pending  
**Branch:** feature/faz1-tamamlama (this branch)  
**Acceptance Criteria:** `tests/acceptance_criteria.md` P1-AC-01..06  
**Estimated Duration:** §10-independent: 2–4 weeks to complete; §10-dependent: after §10

### Completed Outputs

| Output | Document / Module | Status |
|-------|---------------|-------|
| Data ingestion pipeline drafts | `data-platform/ingestion/base_ingestor.py` | DONE |
| Terrain analyzer | `data-platform/processing/terrain_analyzer.py` | DONE |
| Crater candidate filtering + ranking | `mission_intelligence/scoring/scorer.py`, `hard_constraints.py` | DONE |
| Domain models | `domain/crater/models.py`, `domain/environment/models.py`, `domain/mission/models.py` | DONE |
| Digital Twin base infrastructure | `simulation/simulator_design.md` | DONE |
| Scenario runner design | `simulation/simulator_design.md` §4 | DONE |
| Example scenario YAML | `simulation/scenarios/example_scenario.yaml` | DONE |
| Verification and Test Strategy | `tests/verification_strategy.md` | DONE |

### Pending Items

| Item | Dependency | Priority |
|-------|-----------|---------|
| ODE API real connection (LOLAIngestor, ShadowCamIngestor full impl.) | Network access + API key | P-HIGH |
| SPICE kernel integration (illumination model full run) | TBD-TIME-001 (mission date) | P-CRIT |
| AC-VAL-001..004 illumination validation (JPL/NASA GSFC comparison) | SPICE kernel | P-CRIT |
| AC-VAL-005 resolution report (80m vs 300m) | ODE + SPICE | P-HIGH |
| SIL baseline run (RT-001 first run) | Simulator impl. complete | P-HIGH |
| RR-002, RR-003, RR-004, RR-007 mitigation verification (P1-AC-06) | SIL ready | P-HIGH |

### Entry Conditions

- P0 exit criteria largely met.
- Domain models and ICD schemas available.

### Exit Criteria

| Criterion | Method | Target |
|--------|--------|-------|
| P1-AC-01: Illumination model validated with JPL/NASA GSFC | Analysis | AC-VAL-001..004 |
| P1-AC-02: HC filtering 100% accuracy | SIL (100 test candidates) | Zero false eliminations |
| P1-AC-03: Energy-thermal simulator ±TBD% with §10 profile | Analysis + SIL | After TBD-THM-002 closed |
| P1-AC-04: Digital twin completes SC-001 nominal run | SIL (RT-001) | Waypoint ±1m, SoC ≥ 15% |
| P1-AC-05: temporal_class mixing = zero | UT | 100% coverage |
| P1-AC-06: RR-002/003/004/007 mitigation verified | SIL | Mitigation shown for each risk |
| AC-VAL-005: Resolution report delivered | Analysis | Difference analysis approved |

### Critical Dependencies

| Dependency | TBD ID | Status |
|-----------|--------|-------|
| Mission start date (for SPICE) | TBD-TIME-001 | P-CRIT OPEN |
| Vehicle thermal model | TBD-THM-001/002 | P-CRIT OPEN |

### P1 → P2 Gate TBDs

The following TBDs must be closed before P1 gate opens:

| TBD ID | Parameter | Priority |
|--------|-----------|---------|
| TBD-TIME-001 | Mission start date (UTC) | P-CRIT |
| TBD-THM-001 | Thermal mass + insulation configuration | P-CRIT |

---

## P2 — Autonomy Prototype — IN PROGRESS (Agent D)

**Status:** Agent D working on `feature/faz2-otonomi` branch  
**Branch:** feature/faz2-otonomi (separate branch)  
**Acceptance Criteria:** `tests/acceptance_criteria.md` P2-AC-01..08  
**Estimated Duration:** 4–8 weeks (after P1 gate opens)

### Ongoing Work (Agent D)

| Item | Module | Status |
|-------|-------|-------|
| Global planner (A*-based routing) | `autonomy/global-planner/` | IN PROGRESS |
| Local planner (obstacle avoidance) | `autonomy/local-planner/` | IN PROGRESS |
| FDIR implementation | `safety/fdir/` | IN PROGRESS |
| Navigation + EKF sensor fusion | `vehicle/localization/` | IN PROGRESS |
| Mission executive | `autonomy/mission-executive/` | IN PROGRESS |

### Pending Items (P2 scope)

| Item | Dependency | Priority |
|-------|-----------|---------|
| Communication architecture (CCSDS impl.) | TBD-COM-001 | P-CRIT |
| FreeRTOS task prioritisation | §10 OBC selection | P-CRIT |
| SIL regression suite first full run (RT-001..006) | All P2 modules ready | P-HIGH |
| CT-001..007 critical test scenarios | SIL ready | P-HIGH |
| HIL bridge design (SIL/HIL bridge) | §10 OBC interface | P-MED |

### Entry Conditions

- P1 exit criteria all green.
- Following P-CRIT TBDs closed:

| TBD ID | Parameter |
|--------|-----------|
| TBD-BAT-002 | Battery chemistry |
| TBD-SNS-001 | Sensor package |
| TBD-SNS-002 | IMU noise parameters |
| TBD-SNS-003 | Odometry error parameters |
| TBD-COM-001 | Communication hardware |
| TBD-ENE-002 | HC-006 return reserve threshold (Wh) |

### Exit Criteria

| Criterion | Method | Target |
|--------|--------|-------|
| P2-AC-01: Global planner < 60s | SIL | 95% success |
| P2-AC-02: Replanning < 30s | SIL | 95% success |
| P2-AC-03: SC-002 (link loss) passes SIL | SIL | Both scenarios |
| P2-AC-04: SC-003 (energy drop) passes SIL | SIL | FDIR 5s, Planner 30s |
| P2-AC-05: SC-004 (localisation loss) SIL | SIL | Detection-Isolation-Recovery |
| P2-AC-06: SC-006 (thermal violation) SIL | SIL | RETURN_REQUIRED 5s |
| P2-AC-07: 10 critical scenarios × FDIR response | SIL (CT-001..007) | 100% compliance |
| P2-AC-08: Power Mgmt → Planner flow direction | SIL + Code review | Unidirectional dependency |

### P2 → P3 Gate TBDs

| TBD ID | Parameter | Priority |
|--------|-----------|---------|
| TBD-BAT-002 | Battery chemistry | P-CRIT |
| TBD-SNS-001 | Sensor package | P-CRIT |
| TBD-SNS-002 | IMU noise | P-CRIT |
| TBD-SNS-003 | Odometry error | P-CRIT |
| TBD-COM-001 | Communication hardware | P-CRIT |
| TBD-ENE-002 | HC-006 return reserve threshold | P-CRIT |

---

## P3 — Vehicle Integration — NOT STARTED

**Status:** Awaiting §10 vehicle data  
**Branch:** feature/faz3-entegrasyon (not yet created)  
**Acceptance Criteria:** `tests/acceptance_criteria.md` P3-AC-01..05  
**Estimated Duration:** 8–16 weeks (after §10 and P2 gate opens)

### Planned Work

| Item | Module | Dependency |
|-------|-------|-----------|
| Power integration (real battery + PDU) | `power/` | TBD-BAT-001/002 |
| Thermal integration (real heaters + sensors) | `thermal/` | TBD-THM-001/003 |
| Localisation HIL (real sensors) | `vehicle/localization` | TBD-SNS-001/002/003 |
| SIL/HIL bridge implementation | `simulation/digital-twin/sil_hil_bridge` | §10 OBC interface |
| Landing GNC (separate design) | `vehicle/landing-gnc/` | TBD-GNC-001 |
| TVAC tests (THM-004/005) | Thermal vacuum facility | TBD-THM-001/003 |
| HIL regression suite (all RT + CT-001..007) | Real OBC + sensors | TBD-SNS-001 |

### Entry Conditions

- P2 exit criteria all green.
- §10 vehicle data frozen (all P-CRIT TBDs closed):

| TBD ID | Parameter |
|--------|-----------|
| TBD-BAT-001 | Battery capacity (Wh) |
| TBD-BAT-002 | Battery chemistry |
| TBD-SNS-001 | Sensor package |
| TBD-SNS-002 | IMU noise |
| TBD-SNS-003 | Odometry error |
| TBD-THM-001 | Thermal mass + insulation |
| TBD-COM-001 | Communication hardware |
| TBD-GNC-001 | Landing GNC requirements |
| TBD-ENE-002 | HC-006 return reserve threshold |
| TBD-TIME-001 | Mission start date |

### Exit Criteria

| Criterion | Method | Target |
|--------|--------|-------|
| P3-AC-01: HIL localisation σ < 0.5m | HIL | Under real sensor |
| P3-AC-02: HIL FDIR response < 50ms | HIL | 10 anomaly types |
| P3-AC-03: Landing GNC handover | HIL | σ_pos < bootstrap threshold |
| P3-AC-04: All QAR-P1 items met in HIL | HIL | 100% |
| P3-AC-05: SC-003/004/005/006 pass HIL | HIL | Each scenario |
| THM-004/005 TVAC qualification | TVAC | Min/Max temperature |
| Digital twin SoH degradation verified | HIL + Digital Twin | §3.3 metrics |

---

## TBD Gate Map

Summary table of which phase gates each TBD blocks. Source: `config/tbd_register.md`.

| TBD ID | Parameter | P1 Gate | P2 Gate | P3 Gate |
|--------|-----------|-----------|-----------|-----------|
| TBD-BAT-001 | Battery capacity | — | — | BLOCKS |
| TBD-BAT-002 | Battery chemistry | — | BLOCKS | BLOCKS |
| TBD-SNS-001 | Sensor package | — | BLOCKS | BLOCKS |
| TBD-SNS-002 | IMU noise | — | BLOCKS | BLOCKS |
| TBD-SNS-003 | Odometry error | — | BLOCKS | BLOCKS |
| TBD-THM-001 | Thermal mass + insulation | BLOCKS | BLOCKS | BLOCKS |
| TBD-COM-001 | Communication hardware | — | BLOCKS | BLOCKS |
| TBD-GNC-001 | Landing GNC | — | — | BLOCKS |
| TBD-ENE-002 | HC-006 return reserve | — | BLOCKS | BLOCKS |
| TBD-TIME-001 | Mission start date | BLOCKS | — | BLOCKS |
| TBD-REPO-001 | lunar-navigator submodule | P0 pending | — | — |

**Minimum to open P1 gate:** TBD-THM-001 + TBD-TIME-001  
**Minimum to open P2 gate:** 6 P-CRIT TBDs (TBD-BAT-002, SNS-001/002/003, COM-001, ENE-002)  
**To open P3 gate:** All P-CRIT TBDs + §10 vehicle data frozen

---

## Risk–Roadmap Intersection

Which phase mitigates high-RPN risks:

| Risk | RPN | Mitigation Phase | Method |
|------|-----|--------------|--------|
| RR-003 (Thermal model VIPER warning) | 16 | P1 (Analysis) + P3 (TVAC) | Simulator calibration with §10 thermal mass |
| RR-002 (Return reserve uncertainty) | 15 | P1-AC-06 (SIL), P3 (HIL) | Energy estimation error < 10% (CT-002) |
| RR-004 (Link timeout long) | 12 | P2-AC-03 (SIL SC-002) | FI-006 CT-004 |
| RR-007 (Localisation bootstrap) | 12 | P3-AC-03 (HIL) | Landing GNC handover test |
| RR-011 (DEM 80m resolution limit) | 12 | P1-AC-02 (SIL), AC-VAL-005 | Sub-80m obstacle local planner test |

---

## Phase Transition Gates Summary

| Transition | Gate Conditions | Authority | Estimated Date |
|-------|----------------|---------|---------------|
| Pre-Phase → P0 | ConOps + QAR + HC approved | luna-ai-architecture | DONE 2026-11-14 |
| P0 → P1 | P0-AC-01..07 green; TBD-REPO-001 decision | luna-ai-architecture | PENDING TBD |
| P1 → P2 | P1-AC-01..06 + AC-VAL-001..005 green; TBD-THM-001 + TBD-TIME-001 closed | luna-ai-architecture | PENDING — after §10 |
| P2 → P3 | P2-AC-01..08 green; 6 P-CRIT TBDs closed | luna-ai-architecture | PENDING — after §10 |
| P3 → Operational | P3-AC-01..05 + TVAC + all P-CRIT TBDs closed | Mission authority | PENDING — after §10 + P3 |

---

## Revision History

| Version | Date | Change |
|----------|-------|------------|
| 0.1 | 2026-11-14 | First draft — Agent C, C5 task; P0-P3 roadmap, TBD gate map |
