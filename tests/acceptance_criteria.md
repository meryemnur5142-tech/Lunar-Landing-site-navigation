# status: draft
# owner: luna-ai-architecture
# depends_on: [docs/qar/, infrastructure/risk_register.md, simulation/scenarios/operational_scenarios.md, autonomy/autonomy_matrix.md, mission-intelligence/constraints/hard_constraints.py]
# open_items: [illumination model validation tolerance ±TBD% (source: LOLA/SPICE baseline), energy-thermal simulator tolerance ±TBD% (source: §10 vehicle profile), FDIR false positive rate threshold TBD]

# Verification Acceptance Criteria — LUNA-AI v1.1 (§1.10)

## Purpose

Measurable exit criteria demonstrating completion of each project phase (P0-P3). Test methods: Unit (unit test), SIL (Software-in-the-Loop), HIL (Hardware-in-the-Loop), Analysis (analytical verification).

**Note:** Hard constraints (HC-001..015) are always evaluated first in each phase. Acceptance criteria measure the functional correctness of a system that has passed the HC set.

---

## P0 — Architecture Foundation

**P0 is complete when:**

| Criterion ID | Criterion | Measurement Method | Target |
|-----------|--------|---------------|-------|
| P0-AC-01 | All module interfaces implemented conformant to ICD schema | Unit test: schema validation for each module interface | 100% pass |
| P0-AC-02 | Hard constraints engine evaluating HC-001..015 set | Unit test: positive + negative test case for each HC | 15 HC × 2 tests = 30 tests, 100% pass |
| P0-AC-03 | Safety state machine handling all transitions between 4 states | Unit test: NOMINAL↔CAUTION↔RETURN_REQUIRED↔SURVIVAL transition matrix | All valid transitions handled, invalid transitions rejected |
| P0-AC-04 | FDIR operating independently from planner (isolated memory verified) | Analysis + Unit test: memory isolation review, no FDIR planner dependency | Zero dependencies |
| P0-AC-05 | Compliance Notes 1-5 approved in code review | Manual review: mission phase/safety state separation, safe haven 7 criteria, Power Mgmt flow direction | Approved (reviewer signature) |
| P0-AC-06 | temporal_class field present in all environment product TypedDicts | Unit test: `temporal_class` field mandatory, None rejected | 100% coverage |
| P0-AC-07 | JSON Schema and Python TypedDict compatibility (interoperability) | Unit test: JSON Schema vs Python TypedDict comparison | Zero mismatches |

---

## P1 — Scientific Simulation

**P1 is complete when:**

| Criterion ID | Criterion | Measurement Method | Target |
|-----------|--------|---------------|-------|
| P1-AC-01 | Illumination model validated against LOLA/SPICE real data | Analysis: simulation vs LOLA/SPICE comparison | ±TBD% (source: LOLA/SPICE baseline to be determined) |
| P1-AC-02 | Crater candidate filtering correctly applying HC set | SIL: 100 test candidates, set containing known HC violations | HC-violating candidates 100% eliminated, valid candidates not missed |
| P1-AC-03 | Energy-thermal simulator validated against known vehicle profile | Analysis: simulator vs §10 vehicle profile | ±TBD% (source: §10 vehicle thermal + energy model) |
| P1-AC-04 | Digital twin completing nominal mission scenario (SC-001) | SIL: SC-001 full run — simulated DEM + sensor noise | Target reached, energy within budget, σ_pos < 0.5m |
| P1-AC-05 | All temporal_class=predicted products kept separate from historical | Unit test: data stream monitoring; no mixed predicted and historical records | Zero mixing |
| P1-AC-06 | Mitigation verified for RR-002, RR-003, RR-004, RR-007 (high RPN) | SIL: dedicated test scenario for each high-RPN risk | Mitigation effectiveness demonstrated for each risk |

---

## P2 — Autonomy Prototype

**P2 is complete when:**

| Criterion ID | Criterion | Measurement Method | Target |
|-----------|--------|---------------|-------|
| P2-AC-01 | Global planner generating route in < 60s (1km² terrain) | SIL performance test: 1km² DEM, 50 different start-target pairs | 95% under 60s |
| P2-AC-02 | Replanning completing in < 30s | SIL: sudden obstacle injection → replanning time measurement | 95% under 30s |
| P2-AC-03 | SC-002 (link loss) passes SIL | SIL: SC-002 — separate runs for SURFACE_EXPLORATION and PSR_OPS | Both scenarios met acceptance criteria |
| P2-AC-04 | SC-003 (energy drop) passes SIL | SIL: SC-003 — HC-006 violation injection, FDIR→Planner flow | FDIR triggered within 5s, Planner generated route within 30s |
| P2-AC-05 | FDIR generating correct abort for SC-004 (localisation loss) | SIL: QAR-NAV-002 violation injection → FDIR response | Detection, Isolation, Recovery steps in correct order |
| P2-AC-06 | FDIR generating correct abort for SC-006 (thermal violation) | SIL: thermal_margin < 0°C injection → FDIR response | RETURN_REQUIRED within 5s, heater prioritisation active |
| P2-AC-07 | Fault injection: 10 critical scenarios × FDIR expected response | SIL fault injection (from Fault Injection Coverage Matrix) | 100% compliance |
| P2-AC-08 | Power Mgmt → Planner flow direction verified (Compliance Note 3) | SIL + Code review: Planner cannot generate energy policy, only consumes | Dependency direction is unidirectional |

---

## P3 — Vehicle Integration

**P3 is complete when:**

| Criterion ID | Criterion | Measurement Method | Target |
|-----------|--------|---------------|-------|
| P3-AC-01 | HIL: localisation sigma < 0.5m (under real sensor noise) | HIL: nominal run with real sensor package, σ_pos measurement | σ_pos < 0.5m under nominal conditions |
| P3-AC-02 | HIL: FDIR response < 50ms (with anomaly injection) | HIL: 10 anomaly types injected, FDIR decision time measurement | 95% under 50ms |
| P3-AC-03 | Landing GNC → surface navigation handover verified | HIL: full landing simulation + navigation initialisation | Handover σ_pos < bootstrap threshold |
| P3-AC-04 | All QAR-P1 (Critical priority) items met in HIL | HIL: full run of QAR-P1 items | 100% pass |
| P3-AC-05 | SC-003, SC-004, SC-005, SC-006 pass HIL | HIL: critical scenario runs | Each scenario met acceptance criteria |

---

## Fault Injection Coverage Matrix

> Rows: Top-10 RPN fault modes from FMEA (aligned with B3 risk register).
> Columns: Test level.
> Cell: C=Covered, —=Not covered.

| Fault Mode | Risk | Unit | SIL | HIL |
|-----------|------|------|-----|-----|
| Planner computation timeout | RR-001 | C | C | — |
| Return reserve (HC-006) violation | RR-002 | C | C | C |
| Thermal model deviation (> ±threshold) | RR-003 | — | C | C |
| Communication blackout (long-duration) | RR-004 | — | C | C |
| QAR-NAV-002 localisation threshold violation | RR-005 | C | C | C |
| PSR map low resolution | RR-006 | C | C | — |
| Localisation bootstrap error | RR-007 | — | C | C |
| Power-thermal cycle instability | RR-008 | — | C | C |
| Sensor failure (partial/full) | SC-004 | C | C | C |
| FDIR false positive | RR-010 | C | C | — |

**Note:** HIL coverage gaps (RR-001, RR-006, RR-010) will be closed with analysis in P3.

---

## Repository Validation Acceptance Criteria (B4-EK — lunar-navigator VALIDATION.md source)

> Source: daniel27-space/lunar-navigator VALIDATION.md — JPL Horizons and NASA GSFC comparison.
> These criteria measure the physics accuracy of the environment model layer; independent of vehicle hardware.

| Criterion ID | Criterion | Source | Target |
|-----------|--------|--------|-------|
| AC-VAL-001 | Sun/Earth angles consistent with JPL Horizons | JPL Horizons | Within ±0.001° |
| AC-VAL-002 | Illumination fraction correlation with NASA GSFC map | NASA GSFC | r ≥ 0.988, RMS ≤ 2.7 points |
| AC-VAL-003 | Earth visibility correlation with NASA GSFC | NASA GSFC | r ≥ 0.993 |
| AC-VAL-004 | Shackleton ridge illumination: 2m observer 92.29%, 10m observer 95.69% (±0.05 point tolerance) | Gläser et al. (2014): 92.27% / 95.65% | Within ±0.05 points |
| AC-VAL-005 | Resolution-based validation report: 80m vs 20m vs 300m difference analysis must be delivered | B3-EK RR-011/RR-015 | Difference report delivered and approved |

**Application phase:** AC-VAL-001..004 is within P1 scope (illumination model validation). AC-VAL-005 is a P1 exit gate condition.

**Marginal window note:** In AC-VAL-003 test, windows where Earth elevation < TBD° are reported separately marked as `confidence: LOW` (aligned with B5-EK §7.1 and B3-EK RR-014).

---

## Phase Transition Gates

| Phase | Gate Condition | Authority |
|-----|-------------|---------|
| P0 → P1 | P0-AC-01..07 all green | luna-ai-architecture |
| P1 → P2 | P1-AC-01..06 all green | luna-ai-architecture |
| P2 → P3 | P2-AC-01..08 all green | luna-ai-architecture |
| P3 → Operational | P3-AC-01..05 all green + §10 vehicle data frozen | Mission authority |

---

## Revision History

| Version | Date | Change |
|----------|-------|------------|
| 0.1 | 2026-11-14 | First draft — B4 task |
| 0.2 | 2026-11-14 | B4-EK: AC-VAL-001..005 — repository validation criteria sourced from lunar-navigator VALIDATION.md |
