# status: draft
# owner: luna-ai-architecture
# depends_on: [mission-intelligence/constraints/hard_constraints.py, docs/qar/, simulation/scenarios/operational_scenarios.md, autonomy/autonomy_matrix.md]
# open_items: [RPN threshold policy TBD — above which RPN counts as programme risk; mitigation strategies will be updated as §10 vehicle data arrives]

# Risk Register — LUNA-AI v1.1

## Purpose

This document records the identified technical and operational risks of the LUNA-AI system, their probability/impact assessments, and mitigation strategies. Risk owners and monitoring methods are updated per project phase.

## Scoring Scale

- **Probability (1-5):** 1=Very low (<5%), 2=Low (5-20%), 3=Medium (20-40%), 4=High (40-60%), 5=Very high (>60%)
- **Impact (1-5):** 1=Negligible, 2=Minor, 3=Moderate (mission objective affected), 4=Major (mission success at risk), 5=Critical (safety hazard or total mission loss)
- **RPN = Probability × Impact**

---

## Risk Table

| ID | Risk Description | Source | Probability (1-5) | Impact (1-5) | RPN | Mitigation Strategy | Monitoring Method | Owner | Status |
|----|-----------------|--------|-------------------|-------------|-----|--------------------|--------------------|-------|--------|
| RR-001 | Resource-constrained planner computation timeout | §6 A* algorithm | 3 | 3 | 9 | Fallback for computation timeout: previous valid route or fixed safe haven orientation. Time budget < 30 s replanning target. Anytime algorithm approach to be evaluated. | SIL performance test: 1 km² terrain, 100 scenarios. Replanning time histogram. | autonomy/global-planner | OPEN |
| RR-002 | Insufficient return reserve under uncertainty | Estimation error + distance accumulation | 3 | 5 | 15 | HC-006 worst-case (2σ) planning mandatory. Return reserve update period to be optimised. Energy consumption model calibration tests. | HIL energy consumption validation; worst-case scenario SIL. σ_energy monitoring. | power | OPEN |
| RR-003 | Thermal model accuracy — VIPER parameter | §6 warning: if VIPER data is used | 4 | 4 | 16 | Thermal model will be recalibrated when §10 vehicle data arrives. TBD(source: §10 vehicle thermal mass + insulation). Which modules use VIPER parameters must be documented. | P2: simulator thermal validation; P3 HIL: real vehicle thermal measurement. Deviation threshold: ±TBD%. | thermal | OPEN |
| RR-004 | Communication loss duration estimate — blackout longer than expected | Lunar relay geometry, ground antenna availability | 3 | 4 | 12 | Link budget calculation depends on §10 communication hardware. TBD(source: §10). Pre-planned abort trigger durations to be selected conservatively. Blackout tolerance to be designed based on SC-002 scenario. | Trajectory simulation with link outage analysis. SC-002 SIL test. | communication | OPEN |
| RR-005 | Uncertainty threshold calibration — QAR values incompatible with real vehicle | QAR-NAV-002 and other QAR thresholds | 3 | 3 | 9 | P1 simulator calibration. P3 HIL: threshold revision under real sensor noise. Update as vehicle sensor suite arrives from §10. | HIL: localisation sigma measurement < 0.5 m target (P3 acceptance criterion). QAR threshold review meeting. | vehicle/localization | OPEN |
| RR-006 | PSR map resolution insufficient — ShadowCam quality lower than expected | ShadowCam/LOLA data quality | 2 | 4 | 8 | Uncertainty band widened for temporal_class=predicted products. DEM resolution adequacy evaluated per B5 §1 table (> 20 m/px elimination). Alternative data sources (Kaguya, LRO) to be evaluated. | Data quality score monitoring. P1: illumination model ±TBD% validation. | data-platform | OPEN |
| RR-007 | Localisation bootstrap error — initial position estimate wrong after landing | Landing GNC → navigation handover | 3 | 4 | 12 | P3 acceptance criterion: Landing GNC → surface navigation handover to be validated. Bootstrap uncertainty σ initial value to be selected conservatively. First landmark match prioritised. | P3 HIL: landing simulation + localisation initialisation test. σ_pos < threshold target. | vehicle/localization | OPEN |
| RR-008 | Power-thermal loop instability — heater load continuously violates energy budget | Thermal-energy feedback loop | 2 | 4 | 8 | Power Mgmt owner, Planner consumer (Compliance Note 3). Loop stability: heater demand update period to be optimised. TBD(source: §10 heater power profile). Stability analysis to be done in SIL. | SIL: energy-thermal co-simulation 24-hour mission. Energy band excess counter for instability detection. | power + thermal | OPEN |
| RR-009 | Vehicle hardware parameter change — §10 inputs outside expected range | §10 vehicle design revision | 3 | 3 | 9 | Blocking vs. range-freezable inputs separated in config/open_inputs.md. Parameter change impact analysis procedure to be established. TBD register tracked in config/tbd_register.md. | config/tbd_register.md regular updates. §10 input change triggers re-test list for affected modules. | luna-ai-architecture | OPEN |
| RR-010 | FDIR false positive — abort triggered in healthy system | FDIR threshold calibration | 2 | 3 | 6 | FDIR threshold values to be included in QAR validation scope. False positive rate to be measured with SIL fault injection. Threshold tuning to be conservative but prevent unnecessary aborts. | B4 Fault Injection Matrix: 10 critical scenarios × FDIR expected response = 100% compliance target. FDIR false positive rate < TBD%. | safety/fdir | OPEN |
| RR-011 | Resolution limit: 80 m DEM / 300 m site finder cell — small obstacle missed | 80 m DEM → obstacle < 80 m size; 300 m site finder cell | 3 | 4 | 12 | Local planner detects sub-80 m obstacles in real time with IMU/lidar. 300 m site finder cell accepts ±150 m uncertainty at site boundary; PSR boundary confidence calculation adjusted accordingly. Aligned with B5-EK §7.3. | P1 simulator: sub-80 m obstacle injection, local planner response. | vehicle/perception | OPEN |
| RR-012 | Time range limit: Repo valid only for 2024–2035; mission outside this range | Ephemeris and illumination model validity range | 1 | 3 | 3 | Mission date must remain within 2024–2035. If outside, ephemeris and illumination calculations TBD (a different tool may be needed). `ephemeris_validity_range` schema field is required. | config/open_inputs.md mission date constraint. Monitoring: mission date approval gate. | luna-ai-architecture | OPEN |
| RR-013 | Observer height sensitivity: 1 m height difference can halve the longest night; operational antenna height TBD | Vehicle structural design (§10) | 3 | 3 | 9 | SC-009 sensitivity analysis to be completed in P1. horizon.py to be rerun once antenna height is frozen from §10. TBD-HEIGHT-001: observer_height_m (source: §10). | P1 Analysis: observer_height ±1 m sensitivity. Recalculation once §10 input is frozen. | thermal + power | OPEN |
| RR-014 | Earth eclipse refraction ignored: Repo does not calculate this effect; real Earth visibility may deviate in marginal cases | pipeline/ephem/ design decision | 2 | 3 | 6 | Marginal Earth visibility windows (elevation < TBD°) flagged with `confidence: LOW`. These windows excluded from safe band in link planning calculation. B5-EK §7.4 mitigation strategy. | P2 SIL: marginal window tests. AC-VAL-003 Earth visibility validation (r≥0.993). | communication | OPEN |
| RR-015 | Site finder 300 m resolution: downsampled from 80 m DEM; fine topography losses possible | Site finder pipeline resolution choice | 2 | 3 | 6 | Site boundary uncertainty ±150 m accepted; candidates on boundaries may need 80 m DEM re-evaluation. `terrain_resolution` schema field required. AC-VAL-005: 80 m vs 300 m difference report. | P1: 80 m vs 300 m site boundary comparison. AC-VAL-005 delivery. | data-platform | OPEN |

---

## RPN Ranking

| Rank | ID | RPN | Description |
|------|----|-----|-------------|
| 1 | RR-003 | 16 | Thermal model accuracy (VIPER warning) |
| 2 | RR-002 | 15 | Return reserve uncertainty |
| 3 | RR-004 | 12 | Communication loss duration |
| 4 | RR-007 | 12 | Localisation bootstrap error |
| 5 | RR-001 | 9 | Planner computation time |
| 6 | RR-005 | 9 | QAR threshold calibration |
| 7 | RR-009 | 9 | Hardware parameter change |
| 8 | RR-006 | 8 | PSR map resolution |
| 9 | RR-008 | 8 | Power-thermal instability |
| 10 | RR-010 | 6 | FDIR false positive |

| 11 | RR-011 | 12 | Resolution limit: 80 m DEM / 300 m site finder |
| 12 | RR-012 | 3 | Time range limit (2024–2035) |
| 13 | RR-013 | 9 | Observer height sensitivity |
| 14 | RR-014 | 6 | Earth eclipse refraction ignored |
| 15 | RR-015 | 6 | Site finder 300 m resolution |

**High priority threshold (RPN ≥ 12):** RR-002, RR-003, RR-004, RR-007, RR-011 → mitigation must be completed in P1 simulation phase.

---

## TBD References in This Document

- RR-003: Thermal model deviation threshold `±TBD%` (source: §10 vehicle thermal mass + insulation)
- RR-004: Link timeout duration (source: §10 communication hardware)
- RR-008: Heater power profile (source: §10)
- RR-010: FDIR false positive rate target (source: reliability analysis)

---

## Revision History

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-11-14 | Initial draft — B3 task, 10 risks, RPN ranking |
| 0.2 | 2026-11-14 | B3-EK: RR-011..015 added (resolution limit, time range, observer height, refraction, site finder 300 m) |
