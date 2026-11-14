# status: draft
# owner: luna-ai-architecture
# depends_on: [autonomy/autonomy_matrix.md, mission-intelligence/constraints/hard_constraints.py, docs/conops/, docs/qar/]
# open_items: [link_timeout values TBD(source: §10), thermal_margin critical threshold TBD(source: §10 vehicle thermal model), return_reserve_wh threshold defined in HC-006]

# Operational Scenarios — LUNA-AI v1.1

## Purpose

This document defines standard operation and response scenarios for typical and critical situations the LUNA-AI vehicle may encounter. Each scenario is used as a validation reference in SIL/HIL acceptance tests.

**Important:** Safety states (NOMINAL/CAUTION/RETURN_REQUIRED/SURVIVAL) and mission phases (CRUISE/LANDING/SURFACE_EXPLORATION/PSR_OPS/RETURN/SAFE_STATE) are independent axes. Transitions are tracked separately on each axis.

---

## SC-001: Nominal Surface Exploration

| Field | Content |
|------|--------|
| **Scenario ID** | SC-001 |
| **Name** | Nominal Surface Exploration — Nominal Path |
| **Trigger condition** | Mission phase SURFACE_EXPLORATION, safety state NOMINAL, energy budget nominal |
| **Starting phase** | SURFACE_EXPLORATION |
| **Responsible modules** | vehicle/localization, autonomy/global-planner, autonomy/local-planner, power, communication |

**Expected vehicle response (step by step):**

1. **Localisation:** Initial position estimate using previous orbital map and landing data. `position_uncertainty_m < 0.5m` confirmed.
2. **Local plan:** Local planner calculates next N waypoints from global route. Obstacle avoidance evaluated.
3. **Motion:** Vehicle advances toward waypoint at nominal speed (`TBD(source: §10)` m/s). IMU + odometry fusion active.
4. **Localisation update:** Landmark matching attempted every `TBD(source: §10)` metres. If successful, σ_pos is reset.
5. **Telemetry:** Position, energy, thermal status report sent to ground control every `TBD(source: §10)` seconds.
6. **Waypoint confirmation:** Target waypoint reached within ±1m → target marked as successful.
7. **Scientific data collection:** Vehicle stops at target, science payload powered on (OTN — autonomous decision). Measurement cycle completed.
8. **Next waypoint:** Global planner selects next target; energy budget checked.

| Field | Content |
|------|--------|
| **Safety state transition** | NOMINAL → NOMINAL (no transition under nominal conditions) |
| **Ground control notification condition** | Waypoint arrival confirmation; scientific data summary; energy consumption report |
| **Acceptance criterion** | Target reached (±1m), energy within budget (nominal ±10%), localisation σ < 0.5m maintained |
| **Test method** | SIL (simulated DEM + sensor noise), HIL (Phase P3 — real sensor) |

---

## SC-002: Communication Loss

| Field | Content |
|------|--------|
| **Scenario ID** | SC-002 |
| **Name** | Communication Loss — Link Timeout (v1.0 §4.7) |
| **Trigger condition** | Telemetry link interrupted for `link_timeout_s > TBD(source: §10)` |
| **Starting phase** | SURFACE_EXPLORATION or PSR_OPS (two separate responses — see below) |
| **Responsible modules** | communication, autonomy/mission-executive, safety/fdir, autonomy/global-planner |

**Expected vehicle response — link loss in SURFACE_EXPLORATION (step by step):**

1. Communication module detects link_timeout → notifies FDIR.
2. Safety state NOMINAL → CAUTION transition.
3. Vehicle continues moving toward current waypoint (OTN — if no pre-planned trigger active).
4. Pre-planned abort trigger list (ABT-001..006) checked. If none triggered, continue.
5. Wait counter `link_wait_timeout = TBD(source: §10)` starts.
6. If link returns before wait period expires: CAUTION → NOMINAL, operation continues.
7. If wait period exceeded: Move toward pre-planned safe haven list (OTN). Energy budget checked.
8. On reaching safe haven: Wait, periodic communication attempts continue.

**Expected vehicle response — link loss in PSR_OPS (step by step):**

1. Communication module detects link_timeout → notifies FDIR.
2. Safety state NOMINAL → RETURN_REQUIRED transition (link loss in PSR = return trigger).
3. FDIR: Check energy status. Is `return_reserve_wh` sufficient?
   - **Yes:** Start ACL return route. Scientific operation stopped.
   - **No:** ACL emergency return + energy conservation mode. Power Mgmt performs prioritisation.
4. Planner generates shortest energy-efficient route from current position to safe haven.
5. Vehicle makes periodic link attempts while progressing on return route.
6. Link may return if antenna angle recovers after PSR exit.

**Pre-planned abort trigger list (within SC-002 scope):**

| Trigger | Condition | Action |
|---------|-------|-------|
| ABT-001 | `return_reserve_wh < HC-006_threshold` AND phase=PSR_OPS | ACL emergency return |
| ABT-004 | `link_timeout > TBD(source: §10)` AND phase=PSR_OPS AND `energy_critical=true` | ACL emergency return |
| ABT-006 | `fdir_abort_flag=true` | ACL action per mission |

| Field | Content |
|------|--------|
| **Safety state transition** | SURFACE_EXPLORATION: NOMINAL→CAUTION→(if link returns, NOMINAL) or →RETURN_REQUIRED; PSR_OPS: NOMINAL→RETURN_REQUIRED |
| **Ground control notification condition** | When link returns: link loss start/end time, actions taken, current position and energy status |
| **Acceptance criterion** | Vehicle did not go outside pre-planned limits during link loss; energy did not fall below critical threshold; coordination successfully established on link return |
| **Test method** | SIL (with link simulation), HIL (P3) |

---

## SC-003: Sudden Energy Drop in PSR

| Field | Content |
|------|--------|
| **Scenario ID** | SC-003 |
| **Name** | Sudden Energy Drop in PSR (v1.0 §5.D) |
| **Trigger condition** | `return_reserve_wh < HC-006_threshold` — return reserve fell below critical threshold while inside PSR |
| **Starting phase** | PSR_OPS |
| **Responsible modules** | power, safety/fdir, autonomy/global-planner, thermal |

**Expected vehicle response (step by step):**

1. **Power Mgmt detects:** `return_reserve_wh` dropped below HC-006 threshold → anomaly notification to FDIR.
2. **FDIR decision:** HC-006 violation → safety state transition NOMINAL → RETURN_REQUIRED.
   - FDIR operates independently (memory isolated from planner).
3. **Power Mgmt updates energy budget:** Science payload shut down (reduce energy consumption). Heaters reduced to minimum mandatory level. This decision belongs to Power Mgmt; Planner is a consumer.
4. **FDIR → return command to Planner:** `abort_to_safe_haven = true`, `reason = HC006_violation`.
5. **Planner generates route:** Minimum energy route from current PSR position to safe haven. Route generation target < 30s.
6. **Vehicle enters return route:** Phase PSR_OPS → RETURN transition.
7. **Telemetry:** HC-006 violation, return start, expected arrival time transmitted to ground control.
8. **Return monitoring:** `return_reserve_wh` recalculated at each step. If sufficient, continue; if critical, increase energy conservation mode.
9. **Safe haven arrival:** Charging starts. Safety state RETURN_REQUIRED → NOMINAL (after charge complete).

**Flow direction note (Compliance Note 3):** Power Mgmt owns the energy budget; budget calculations and limits come from Power Mgmt. Planner consumes this information and cannot determine its own energy policy.

| Field | Content |
|------|--------|
| **Safety state transition** | NOMINAL → RETURN_REQUIRED (at HC-006 violation), RETURN_REQUIRED → NOMINAL (after safe haven charge) |
| **Ground control notification condition** | At HC-006 violation (energy value, position, expected return time); on safe haven arrival |
| **Acceptance criterion** | FDIR detected HC-006 violation and triggered RETURN_REQUIRED within 5s; planner generated return route within 30s; vehicle arrived at safe haven with energy above HC-006 threshold |
| **Test method** | SIL (energy consumption simulation), HIL (P3) |

---

## SC-004: Localisation Loss / Sensor Failure

| Field | Content |
|------|--------|
| **Scenario ID** | SC-004 |
| **Name** | Localisation Loss / Sensor Failure (v1.0 §4.8) |
| **Trigger condition** | `position_uncertainty_m > QAR-NAV-002_threshold` — position uncertainty exceeded acceptance threshold |
| **Starting phase** | SURFACE_EXPLORATION or PSR_OPS |
| **Responsible modules** | vehicle/localization, safety/fdir, autonomy/global-planner, autonomy/local-planner |

**FDIR Steps — Detection → Isolation → Recovery:**

**Detection:**
1. Localisation module continuously monitors σ_pos.
2. `position_uncertainty_m > QAR-NAV-002_threshold` → FDIR anomaly flag set.
3. Safety state NOMINAL → CAUTION.
4. Vehicle receives STOP command (motion halted).

**Isolation:**
5. Attempt to identify which sensor is faulty:
   - IMU inconsistency test
   - Odometry/IMU comparison
   - Last landmark match quality check
6. Faulty sensor isolated (degraded mode).

**Recovery:**
7. **Landmark search:** Vehicle rotates in place attempting landmark match against orbital map.
   - Match successful: σ_pos drops below threshold → CAUTION → NOMINAL. Motion resumes.
   - Match unsuccessful (N attempts, TBD(source: §10)): Recovery fails.
8. **Recovery fails:** Safety state CAUTION → RETURN_REQUIRED.
   - If phase PSR_OPS: ACL emergency return (degraded navigation with position uncertainty).
   - If phase SURFACE_EXPLORATION: IMU-only navigation toward pre-planned safe haven coordinates.
9. **Degraded navigation mode:** IMU + odometry only, without landmarks. Error accumulation bounded by accepted maximum distance.
10. Ground control notification: Sensor failure type, current σ_pos, planned action.

| Field | Content |
|------|--------|
| **Safety state transition** | NOMINAL→CAUTION (detection), CAUTION→NOMINAL (recovery successful) or CAUTION→RETURN_REQUIRED (recovery fails) |
| **Ground control notification condition** | At QAR-NAV-002 violation; on recovery decision (success/failure) |
| **Acceptance criterion** | FDIR detected localisation loss within 5s; landmark search attempt made; if recovery fails, RETURN_REQUIRED triggered and vehicle reached safe haven |
| **Test method** | SIL (sensor noise injection), HIL (P3 — real sensor failure simulation) |

---

## SC-005: Safe Haven Unreachable

| Field | Content |
|------|--------|
| **Scenario ID** | SC-005 |
| **Name** | Safe Haven Unreachable — Primary Route Blocked |
| **Trigger condition** | `primary_safe_haven_route_blocked = true` — obstacle or terrain condition blocked primary safe haven route |
| **Starting phase** | SURFACE_EXPLORATION, PSR_OPS or RETURN |
| **Responsible modules** | autonomy/global-planner, autonomy/replanner, safety/fdir, power |

**Expected vehicle response (step by step):**

1. Local planner detects impassable obstacle on primary safe haven route → notifies FDIR.
2. Vehicle STOPS. FDIR initiates backup safe haven evaluation.
3. **Backup safe haven selection — 7 criteria (Compliance Note 2):**
   - Criterion 1: Continuous illumination (for energy charging)
   - Criterion 2: Darkness interval tolerance (thermal endurance)
   - Criterion 3: Recharge capacity (panel angle, expected power)
   - Criterion 4: Return energy sufficiency (from there to landing site)
   - Criterion 5: Thermal safety (temperature range)
   - Criterion 6: Communication (line of sight to ground antenna)
   - Criterion 7: Emergency access (for future mission or rescue)
4. Backup safe haven meeting all 7 criteria found → replanner generates new route. Ground control approval (in normal operations) or ACL (inside PSR or if energy critical).
5. Ground control notification: Primary safe haven blocked, backup selected, 7 criteria results.
6. **No backup safe haven:** If no alternative meets all 7 criteria:
   - Safety state RETURN_REQUIRED → SURVIVAL transition.
   - SURVIVAL mode preparation: shut down science payload, maintain heaters at minimum mandatory level, max energy conservation.
   - Vehicle waits at current position. Periodic communication attempts.
   - Critical status notification to ground control: position, energy, thermal status, expected survival time.

| Field | Content |
|------|--------|
| **Safety state transition** | (current)→RETURN_REQUIRED (if backup found, return plan); RETURN_REQUIRED→SURVIVAL (if no backup) |
| **Ground control notification condition** | At primary route blockage; on backup selection decision; on SURVIVAL entry (critical) |
| **Acceptance criterion** | 7 criteria correctly applied; route generated if backup found; in SURVIVAL, energy conservation active and notification sent |
| **Test method** | SIL (route blocking injection, 7-criteria scenarios), HIL (P3) |

---

## SC-006: Thermal Limit Violation

| Field | Content |
|------|--------|
| **Scenario ID** | SC-006 |
| **Name** | Thermal Limit Violation (v1.0 §4.5) |
| **Trigger condition** | `thermal_margin_c < 5°C` (warning) or `thermal_margin_c < 0°C` (critical) |
| **Starting phase** | SURFACE_EXPLORATION or PSR_OPS |
| **Responsible modules** | thermal, power, safety/fdir, autonomy/global-planner |

**Expected vehicle response — Warning level (< 5°C margin):**

1. Thermal module detects warning threshold → notifies FDIR. Safety state NOMINAL → CAUTION.
2. Heater prioritisation: Critical system heaters (processor, battery, sensors) first. Science payload heaters suspended.
3. **Impact on energy budget (Compliance Note 3):** Power Mgmt receives heater power demand, updates budget. If total consumption increases, new budget limit sent to Planner. Planner reduces traversal speed/frequency.
4. Ground control notification: Thermal warning, which heaters activated, impact on energy budget.
5. Status monitored; if margin rises above 5°C, CAUTION → NOMINAL.

**Expected vehicle response — Critical level (< 0°C margin):**

1. Thermal module detects critical threshold → notifies FDIR. Safety state CAUTION/NOMINAL → RETURN_REQUIRED.
2. All heaters set to maximum priority. Science payload emergency shutdown.
3. **If inside PSR, decision:**
   - `warm_in_place_vs_return` evaluation: based on current thermal model + energy status.
   - If no sunlight inside PSR and heater power sufficient: **warm in place** (< X minutes, TBD(source: §10 thermal model)).
   - If warming insufficient or energy critical: **ACL emergency return** initiated.
4. In SURFACE_EXPLORATION: ACL move to nearest lit area (thermal gain).
5. **Power Mgmt → Planner flow:** Power Mgmt sends updated budget with heater demand. Planner generates route within this budget.
6. Ground control notification: Critical thermal status, action taken, expected recovery time.

| Field | Content |
|------|--------|
| **Safety state transition** | NOMINAL→CAUTION (warning), CAUTION→RETURN_REQUIRED (critical) |
| **Ground control notification condition** | When warning threshold crossed; at critical threshold (emergency); on PSR return/warm-in-place decision |
| **Acceptance criterion** | Warning: Heater prioritisation active within 2s; energy budget updated. Critical: RETURN_REQUIRED triggered within 5s; correct decision (warm/return) made inside PSR |
| **Test method** | SIL (fault injection with thermal model), HIL (P3) |

---

---

## SC-007: Longest Communication Outage (B2-EK)

| Field | Content |
|------|--------|
| **Scenario ID** | SC-007 |
| **Name** | Longest Communication Outage — 60-Day Window Metrics |
| **Trigger condition** | Entered the longest link outage window caused by sun/Earth geometry (source: repo 60-day sun/Earth window longest gap metric) |
| **Starting phase** | SURFACE_EXPLORATION or PSR_OPS |
| **Responsible modules** | communication, autonomy/mission-executive, safety/fdir, power |

**Expected vehicle response (step by step):**

1. Pre-mission planning: 60-day window analysis identifies longest expected link outage. This value enters the pre-planned abort trigger list and energy budget.
2. Before entering outage window: Energy top-up, science data buffer flush, safe haven positioning.
3. When outage begins: SC-002 protocol applied (depending on phase).
4. During outage: OTN pre-planned operation — periodic communication attempts, energy conservation, thermal monitoring.
5. When outage end estimate is passed: Link attempts intensified. If estimate exceeded, SC-002 critical path activates.

**Parameters:** `longest_outage_hours` = TBD (source: repo 60-day analysis, varies by region). `uncertainty_minutes` = TBD (source: §7.1 B5-EK — uncertainty in marginal Earth visibility).

| Field | Content |
|------|--------|
| **Safety state transition** | Same logic as SC-002; RETURN_REQUIRED if duration exceeds expectation |
| **Ground control notification condition** | Before entering outage window; when outage ends |
| **Acceptance criterion** | Pre-planned plan ready for longest expected outage; vehicle remained within energy and thermal limits throughout outage |
| **Test method** | SIL (60-day window simulation), Analysis |

---

## SC-008: Window Miss / Geometry Update (B2-EK)

| Field | Content |
|------|--------|
| **Scenario ID** | SC-008 |
| **Name** | Window Miss / Geometry Update — Landing Time Revision |
| **Trigger condition** | New ephemeris data (JPL Horizons update) arrived and previous landing time estimate became invalid |
| **Starting phase** | CRUISE (pre-landing planning phase) |
| **Responsible modules** | apps/ground-control, autonomy/mission-executive, vehicle/landing-gnc |

**Expected vehicle response (step by step):**

1. New ephemeris data received → geometry calculation re-runs OTN (B1-EK: geometry update is OTN).
2. New calculation: has the previous landing window recommendation changed?
   - No (window unchanged): Information updated, operation continues.
   - Yes (window shifted or narrowing): Notification to ground control. Ground control approval — landing time change.
3. Ground control approves new window → `landing_window_validation.schema.yaml` updated.
4. Update: `sun_coverage_ok`, `earth_visibility_ok`, `comm_window_ok` re-validated.
5. Vehicle updates landing preparation according to new timing.

**Note:** Geometry improvement (calculation update) is OTN, but if the region or time decision derived from this update changes, ground control approval is required.

| Field | Content |
|------|--------|
| **Safety state transition** | No safety state transition in CRUISE phase; mission abort if landing window validation fails |
| **Ground control notification condition** | On window change detection; on approval received |
| **Acceptance criterion** | Geometry update correctly detected; window change approved by ground control; `landing_window_validation` fields consistent |
| **Test method** | SIL (ephemeris simulation), Analysis |

---

## SC-009: Observer Height Sensitivity (B2-EK)

| Field | Content |
|------|--------|
| **Scenario ID** | SC-009 |
| **Name** | Observer Height Sensitivity — Effect of 1m Height Difference |
| **Trigger condition** | Vehicle/antenna observation height differs from design value (repo note: "a mast a metre taller can halve the longest night") |
| **Starting phase** | Design validation (pre-launch) and SURFACE_EXPLORATION |
| **Responsible modules** | vehicle/localization, thermal, power, communication |

**Expected vehicle response (step by step):**

1. **Design phase:** Antenna/sensor height `observer_height_m` = TBD(source: §10 vehicle structure). This value feeds into horizon.py calculation.
2. **Sensitivity analysis:** How does a 1m height increase affect the longest night duration? (Repo: can halve it.)
3. **P1 validation:** `observer_height_m` varied by ±1m in simulator to calculate difference in longest night and Earth visibility window.
4. **Operational impact:** If height comes in lower than TBD value → `longest_outage_hours` increases → SC-007 parameter updated → safety budget recalculated.
5. **SURFACE_EXPLORATION:** Vehicle evaluates whether recalculation of longest night estimate is needed on sloped terrain (OTN — calculation update).

**Test parameters:** Comparison of longest night and Earth visibility window for `observer_height_m` = [0.5, 1.0, 1.5, 2.0] m.

| Field | Content |
|------|--------|
| **Safety state transition** | Ground notification if height deviation affects safety parameters |
| **Ground control notification condition** | If observer height deviates from design value; if significant change in longest night estimate |
| **Acceptance criterion** | Sensitivity analysis completed and results reflected in SC-007/thermal/energy budget; observer_height TBD frozen with §10 |
| **Test method** | Analysis (sensitivity), SIL (P1 simulator) |

---

## Scenario Summary Table

| Scenario | Phase | Safety Transition | Authority | Test |
|---------|-----|-----------------|---------|------|
| SC-001 | SURFACE_EXPLORATION | NOMINAL stays | OTN | SIL + HIL |
| SC-002 | SURFACE / PSR | NOMINAL→CAUTION or RETURN_REQUIRED | OTN / ACL | SIL + HIL |
| SC-003 | PSR_OPS | NOMINAL→RETURN_REQUIRED | ACL | SIL + HIL |
| SC-004 | SURFACE / PSR | NOMINAL→CAUTION→NOMINAL or RETURN_REQUIRED | FDIR | SIL + HIL |
| SC-005 | SURFACE / PSR / RETURN | →RETURN_REQUIRED or SURVIVAL | ACL / GCA | SIL + HIL |
| SC-006 | SURFACE / PSR | NOMINAL→CAUTION→RETURN_REQUIRED | ACL | SIL + HIL |
| SC-007 | SURFACE / PSR | SC-002 logic; RETURN_REQUIRED if duration exceeded | OTN / ACL | SIL + Analysis |
| SC-008 | CRUISE | No transition; GCA if window changes | OTN / GCA | SIL + Analysis |
| SC-009 | Design / SURFACE | Parametric impact notification | OTN | Analysis + SIL |

---

## Revision History

| Version | Date | Change |
|----------|-------|------------|
| 0.1 | 2026-11-14 | First draft — B2 task |
| 0.2 | 2026-11-14 | B2-EK: SC-007 (longest communication outage), SC-008 (window miss), SC-009 (observer height sensitivity) added |
