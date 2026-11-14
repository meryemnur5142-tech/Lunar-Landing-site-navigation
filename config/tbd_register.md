# status: draft
# owner: luna-ai-architecture
# depends_on: [config/open_inputs.md, domain/environment/uncertainty_policy.md, infrastructure/risk_register.md]
# open_items: [TBDs will be closed as §10 vehicle data arrives; Priority 1 TBDs are P1 gate conditions]

# TBD Register — LUNA-AI v1.1

## Purpose

Collects all `TBD(source: §10)` and related uncertain parameters in one place. As §10 vehicle data arrives, TBDs are closed from this document and affected modules are updated.

## Priority Definitions

- **P-CRIT:** Blocking — P1/P2 cannot start until resolved
- **P-HIGH:** Must be calibrated during P1 simulation phase
- **P-MED:** Must be confirmed during P2 prototype phase
- **P-LOW:** Can be deferred until P3 integration phase

---

## TBD Table

| ID | Parameter | Default / Range | §10 Source | Affected Files | Priority |
|----|-----------|--------------------|-----------|--------------------|---------|
| TBD-BAT-001 | Battery capacity (Wh) | 500–1500 Wh | §10 energy subsystem | power/, HC-006, config/open_inputs.md | P-HIGH |
| TBD-BAT-002 | Battery chemistry and charge/discharge limits | — | §10 energy subsystem | power/, thermal/, HC-006, HC-007 | P-CRIT |
| TBD-SOL-001 | Solar panel nominal power (W) | 300–800 W | §10 energy subsystem | power/, HC-009 | P-HIGH |
| TBD-TRV-001 | Nominal traversal speed (m/s) | 0.05–0.15 m/s | §10 mobility subsystem | autonomy/global-planner, route duration estimate | P-HIGH |
| TBD-TRV-002 | Max climb angle (°) | 20–30° | §10 mobility subsystem | HC-001, HC-005, autonomy/global-planner | P-HIGH |
| TBD-MAS-001 | Vehicle mass (kg) | 100–300 kg | §10 structure subsystem | vehicle/mobility-control, energy/kg consumption | P-MED |
| TBD-SNS-001 | Sensor package (type, configuration) | — | §10 perception subsystem | vehicle/localization, QAR-NAV-002, FDIR thresholds | P-CRIT |
| TBD-SNS-002 | IMU noise parameters (σ_drift) | — | §10 perception subsystem | domain/environment/uncertainty_policy.md §3.1 | P-CRIT |
| TBD-SNS-003 | Odometry error parameters (σ_odo) | — | §10 perception subsystem | domain/environment/uncertainty_policy.md §3.1 | P-CRIT |
| TBD-THM-001 | Thermal mass and insulation configuration | — | §10 thermal subsystem | thermal/, HC-007, SC-006, RR-003 | P-CRIT |
| TBD-THM-002 | Thermal model deviation tolerance (±%) | ±TBD% | §10 thermal subsystem | tests/acceptance_criteria.md P1-AC-03, RR-003 | P-HIGH |
| TBD-THM-003 | Critical thermal margin threshold (°C) | 0°C (warning: 5°C) | §10 thermal subsystem | SC-006, thermal/, FDIR | P-HIGH |
| TBD-COM-001 | Communication hardware (antenna, bandwidth) | — | §10 communication subsystem | communication/, HC-014, SC-002, SC-007 | P-CRIT |
| TBD-COM-002 | Link timeout duration (s) | — | §10 communication subsystem | autonomy/autonomy_matrix.md ABT-004, SC-002 | P-HIGH |
| TBD-COM-003 | Link recovery window duration (s) | — | §10 communication subsystem | SC-002 ABT-004 wait duration | P-HIGH |
| TBD-GNC-001 | Landing GNC requirements | — | §10 GNC subsystem | vehicle/landing-gnc, P3-AC-03 | P-CRIT |
| TBD-NAV-001 | Localisation bootstrap σ_pos initial value | — | §10 GNC subsystem | vehicle/localization, RR-007 | P-HIGH |
| TBD-ENE-001 | Energy consumption model uncertainty σ_energy_pct | — | §10 vehicle profile | domain/environment/uncertainty_policy.md §2.3 | P-HIGH |
| TBD-ENE-002 | Return reserve threshold HC-006 (Wh) | — | §10 energy subsystem | HC-006, SC-003, ABT-001, power/ | P-CRIT |
| TBD-HEIGHT-001 | Observer height (antenna/sensor mast height, m) | 0.5–2.0 m | §10 structure subsystem | simulation/environment-model, communication, SC-009, RR-013 | P-HIGH |
| TBD-TIME-001 | Mission start date (UTC) | 2024–2035 range | Mission authority | simulation/environment-model, apps/ground-control, RR-012 | P-CRIT |
| TBD-REPO-001 | lunar-navigator integration method (submodule vs reference directory) | — | Project decision | infrastructure/repo_placement.md, DR-INT-001 | P-MED |
| TBD-REPO-002 | GPU ray-marching flight segment bridge architecture | — | P2 design decision | apps/ground-control, infrastructure/repo_placement.md | P-LOW |
| TBD-VIS-001 | Marginal Earth visibility elevation threshold (°) | — | Environment model analysis | domain/environment/uncertainty_policy.md §7.1, communication/ | P-HIGH |
| TBD-NAV-002 | EKF process noise covariance Q (IMU) | — | §10 perception subsystem (after TBD-SNS-002) | vehicle/localization/navigation_architecture.md §1.3 | P-HIGH |
| TBD-NAV-003 | EKF measurement noise covariance R (odometry/VO) | — | §10 perception subsystem (after TBD-SNS-003) | vehicle/localization/navigation_architecture.md §1.3 | P-HIGH |
| TBD-NAV-004 | LiDAR range and resolution specifications | — | §10 perception subsystem | vehicle/localization/navigation_architecture.md §3, autonomy/ | P-CRIT |
| TBD-NAV-005 | Visual odometry feature extraction parameters | — | §10 perception subsystem | vehicle/localization/navigation_architecture.md §1.1 | P-HIGH |
| TBD-NAV-006 | Sun sensor accuracy specifications | — | §10 perception subsystem | vehicle/localization/navigation_architecture.md §1.1 | P-MED |
| TBD-NAV-007 | Orbital DEM resolution and update frequency | — | Orbital mission data | vehicle/localization/navigation_architecture.md §4.1 | P-HIGH |
| TBD-NAV-008 | PSR navigation max distance from last known good position | — | §10 vehicle power model | vehicle/localization/navigation_architecture.md §3.3 | P-HIGH |
| TBD-FDIR-001 | IMU/VO cross-check inconsistency threshold (σ_imu_vo_diff) | — | §10 perception subsystem | safety/fdir_implementation.md §1.1, safety/fdir_decision_tree.md | P-HIGH |
| TBD-FDIR-002 | Wheel encoder vs command deviation threshold (motor stall detection) | — | §10 mobility subsystem | safety/fdir_implementation.md §2.1, safety/fdir_decision_tree.md | P-HIGH |
| TBD-FDIR-003 | Battery SoC deviation anomaly threshold | — | §10 energy subsystem | safety/fdir_implementation.md §3.1 | P-HIGH |
| TBD-FDIR-004 | Cell imbalance threshold (mV difference) | — | §10 energy subsystem | safety/fdir_implementation.md §3.1 | P-HIGH |
| TBD-FDIR-005 | FDIR main loop frequency (Hz); hardware dependent | — | §10 OBC/RTOS configuration | safety/fdir_implementation.md §6.2, docs/architecture/SAFETY_STATE_MACHINE.md §3 | P-HIGH |
| TBD-FDIR-006 | Communication loss link_timeout threshold (s); overlaps TBD-COM-002 | — | §10 communication subsystem | safety/fdir_implementation.md §4.1, safety/fdir_decision_tree.md | P-HIGH |
| TBD-FDIR-007 | Localisation loss position uncertainty threshold (m) | 2.0 m (QAR-NAV-004 reference) | §10 perception subsystem | safety/fdir_implementation.md §5.1 | P-HIGH |
| TBD-FDIR-008 | Localisation recovery wait duration (s) | — | §10 mission parameter | safety/fdir_implementation.md §5.3, safety/fdir_decision_tree.md | P-HIGH |
| TBD-PLAN-001 | Weighted A* heuristic weight factor (w) | 1.0–3.0 | §10 compute budget + QAR-PLAN-001 | autonomy/mission_planner.md §1.3, autonomy/global_planner_pseudocode.py | P-MED |
| TBD-PLAN-002 | Maximum local replanning iteration count | — | §10 OBC compute capacity | autonomy/mission_planner.md §3.2 | P-MED |
| TBD-PLAN-003 | Energy consumption model by terrain type (Wh/m) | — | §10 energy + mobility model | autonomy/mission_planner.md §2.3, autonomy/global_planner_pseudocode.py | P-HIGH |
| TBD-PLAN-004 | Thermal cost coefficient (cost function) | — | §10 thermal model | autonomy/mission_planner.md §2.3, autonomy/global_planner_pseudocode.py | P-MED |
| TBD-PLAN-005 | Risk cost coefficient (slope, obstacle proximity) | — | §10 terrain data | autonomy/mission_planner.md §2.3, autonomy/global_planner_pseudocode.py | P-MED |
| TBD-PLAN-006 | Safe haven minimum illumination threshold (hours) | — | Orbital mechanics sim (SHV-001) | autonomy/mission_planner.md §5.2, HC-009 | P-HIGH |
| TBD-PLAN-007 | Safe haven minimum recharge capacity (Wh/sol) | — | §10 energy + orbital | autonomy/mission_planner.md §5.2, HC-011 | P-HIGH |
| TBD-PLAN-008 | Communication loss wait duration — planner behaviour (s) | — | §10 communication subsystem (TBD-COM-002) | autonomy/mission_planner.md §6.3 | P-HIGH |
| TBD-PLAN-009 | Science scheduler priority weights | — | Science team priority decision | autonomy/mission_planner.md §7.3, autonomy/global_planner_pseudocode.py | P-MED |
| TBD-COM-004 | Frequency band selection (X-band vs Ka-band) | X-band recommended | §10 power/mass budget + DSN access plan | communication/comm_architecture.md §1.1, communication/link_budget_template.yaml | P-CRIT |
| TBD-COM-005 | TX power (W) | — | §10 power subsystem | communication/comm_architecture.md §1.3, communication/link_budget_template.yaml | P-HIGH |
| TBD-COM-006 | HGA gain (dBi) | DSN 34m ~68 dBi typical (ground side) | §10 structure subsystem (vehicle antenna) | communication/comm_architecture.md §1.3, communication/link_budget_template.yaml | P-HIGH |
| TBD-COM-007 | Target link margin (dB) | ≥ 3 dB recommended | §10 communication subsystem + link budget | communication/comm_architecture.md §1.3, communication/link_budget_template.yaml | P-HIGH |
| TBD-COM-008 | Uplink command data rate (bps) | — | §10 communication subsystem | communication/comm_architecture.md §1.3, communication/link_budget_template.yaml | P-HIGH |
| TBD-COM-009 | Downlink telemetry data rate (bps) | Sized by QAR-COM-002 (≤ 10 s period) | §10 communication subsystem | communication/comm_architecture.md §1.3, communication/link_budget_template.yaml | P-HIGH |
| TBD-COM-010 | Downlink science data rate (bps) | — | §10 science package + communication | communication/comm_architecture.md §1.3, communication/link_budget_template.yaml | P-MED |
| TBD-COM-011 | SCLK-UTC drift tolerance (ms) | — | §10 OBC oscillator specifications | communication/comm_architecture.md §6.2 | P-HIGH |
| TBD-COM-012 | UTC synchronisation frequency (every link window / X times per day) | Every link window | §10 mission operations plan | communication/comm_architecture.md §6.2 | P-MED |
| TBD-COM-013 | South pole Earth blackout max duration (hours) | — | Orbital mechanics sim (SPICE DE440) | communication/comm_architecture.md §2.3, earth_visibility_windows.schema.yaml | P-HIGH |
| TBD-COM-014 | Command authentication mechanism details (key management) | HMAC-SHA256 recommended | §10 security analysis | communication/comm_architecture.md §7.2 | P-MED |

---

## Closure Procedure

When a TBD's §10 data arrives:

1. The `Status` column in this table is marked CLOSED.
2. The TBD placeholder in affected modules is replaced with the real value.
3. The change is referenced in the commit message with `closes TBD-XXX-YYY`.
4. P-CRIT TBDs must be closed before the relevant phase gate opens.

---

## P-CRIT TBDs Summary

The following TBDs must be closed before the P1 → P2 transition gate can open:

| TBD ID | Parameter |
|--------|-----------|
| TBD-BAT-002 | Battery chemistry |
| TBD-SNS-001 | Sensor package |
| TBD-SNS-002 | IMU noise |
| TBD-SNS-003 | Odometry error |
| TBD-THM-001 | Thermal mass + insulation |
| TBD-COM-001 | Communication hardware |
| TBD-GNC-001 | Landing GNC requirements |
| TBD-ENE-002 | HC-006 return reserve threshold |
| TBD-TIME-001 | Mission start date |
| TBD-NAV-004 | LiDAR range and resolution specifications |
| TBD-COM-004 | Frequency band selection (X-band vs Ka-band) |

---

## Revision History

| Version | Date | Change |
|----------|-------|------------|
| 0.1 | 2026-11-14 | First draft — C3 task, 24 TBD entries |
| 0.2 | 2026-11-14 | Agent D (D1-D2-D3): NAV-002..008, FDIR-001..008, PLAN-001..009 added (25 new entries) |
| 0.3 | 2026-11-14 | Agent D (D4): COM-004..014 added (11 new entries) |
