# status: draft
# owner: luna-ai-architecture
# depends_on: [docs/conops/CONOPS.md, docs/qar/QAR_TABLE.md, docs/adr/ADR-001..ADR-006, docs/architecture/SAFETY_STATE_MACHINE.md]
# open_items: [HC-001 vehicle slope limit TBD(source: §10), HC-002 roughness RMS TBD(source: §10), HC-004 flatness variance TBD(source: §10), HC-005 climb angle TBD(source: §10), HC-006 return reserve Wh TBD(source: §10), HC-007 thermal margin threshold TBD(source: §10 thermal model), HC-008 PSR battery SoC TBD(source: §10), HC-009 min illumination duration TBD(source: §10), HC-010 max darkness interval TBD(source: §10), HC-011 recharge opportunity threshold TBD(source: §10), HC-013 thermal limit TBD(source: §10), HC-014 visibility angle/window TBD(source: §10), HC-015 emergency access distance TBD(source: §10), HC-016 site finder min sun fraction TBD(source: §10), HC-017 site finder min Earth visibility fraction TBD(source: §10), HC-018 landing time Earth visibility window confirmed]

# Hard Constraint Catalogue — LUNA-AI v1.1

## 1. Purpose and Scope

This catalogue defines the elimination-level (pass/fail) hard constraints of the LUNA-AI mission system.
If a criterion is marked **Hard** in this list, no multi-criteria ranking score may override it.
Soft-classified criteria incur a performance penalty; they do not require elimination.

> **Compliance Note 5:** Hard constraints are applied first; ranking score operates only on passing candidates.
> **Compliance Note 3:** Energy/thermal thresholds are computed by the Power Management module and reported to the planner.
>   The planner enforces these values as hard constraints — it never computes them independently.

---

## 2. Constraint Table

### 2.1 Terrain / Landing Constraints

| ID | Name | Parameter | Operator | Threshold | Unit | Source / Rationale | Phase | Verification Method |
|---|---|---|---|---|---|---|---|---|
| HC-001 | Maximum Landing Site Slope | `max_slope_deg` | ≤ | 15.0 TBD(source: §10) | deg | v1.0 §4.1, QAR-MOB-001 — vehicle rollover stability | landing | analysis |
| HC-002 | Maximum Surface Roughness RMS | `surface_roughness_rms_m` | ≤ | 0.30 TBD(source: §10) | m | v1.0 §4.1, QAR-LND-002 — landing leg design limit | landing | simulation + test |
| HC-003 | Maximum Rock / Obstacle Density | `obstacle_fraction` | ≤ | 0.20 | fraction (0–1) | v1.0 §4.3, QAR-LND-003 — rock avoidance performance limit | landing, surface_exploration | analysis |
| HC-004 | Minimum Landing Ellipse Flatness | `slope_variance_deg2` | ≤ | TBD(source: §10) | deg² | v1.0 §4.1 — slope variance inside landing ellipse; irregular areas eliminated | landing | analysis |
| HC-005 | Vehicle Accessibility Slope | `approach_slope_deg` | ≤ | TBD(source: §10) | deg | v1.0 §4.3, QAR-MOB-002 — approach profile slope ≤ max climb angle | surface_exploration, psr_ops | simulation |

### 2.2 Energy / Thermal Constraints

| ID | Name | Parameter | Operator | Threshold | Unit | Source / Rationale | Phase | Verification Method |
|---|---|---|---|---|---|---|---|---|
| HC-006 | Minimum Return Energy Reserve | `return_reserve_wh` | ≥ | TBD(source: §10) | Wh | Compliance Note 3 — Power Mgmt computes, planner enforces; linked to HC-012 | surface_exploration, psr_ops, return | analysis + simulation |
| HC-007 | Minimum Safe Darkness Tolerance Margin | `thermal_margin_c` | ≥ | TBD(source: §10 thermal model) | °C | Thermal model dependent; VIPER 50s threshold not universal — vehicle-design specific | psr_ops, return, safe_state | analysis |
| HC-008 | Minimum Battery SoC at PSR Entry | `battery_soc_pct` | ≥ | TBD(source: §10) | % | v1.0 §5.2, QAR-PWR-001 — communication + heating guarantee inside PSR | psr_ops | test + analysis |

### 2.3 Safe Haven Constraints — 7 Criteria (Compliance Note 2)

> **Compliance Note 2:** Safe haven evaluation uses exactly the following 7 criteria.
> No criteria are added to or removed from this set of 7.

| ID | Name | Parameter | Operator | Threshold | Unit | Safe Haven Criterion | Phase | Verification Method |
|---|---|---|---|---|---|---|---|---|
| HC-009 | Minimum Continuous Illumination Duration | `continuous_illumination_hr` | ≥ | TBD(source: §10) | hours | Criterion 1: continuous illumination | safe_state | orbit analysis |
| HC-010 | Maximum Acceptable Darkness Interval | `max_darkness_interval_hr` | ≤ | TBD(source: §10) | hours | Criterion 2: darkness interval | safe_state | orbit analysis |
| HC-011 | Recharge Opportunity | `recharge_capacity_wh_per_sol` | ≥ | TBD(source: §10) | Wh/sol | Criterion 3: recharge — illumination_duration × panel_efficiency ≥ threshold | safe_state | analysis |
| HC-012 | Return Energy Adequacy | `return_energy_budget_wh` | ≥ | distance_m × consumption_wh/m + uncertainty_margin | Wh | Criterion 4: return energy — safe_haven→origin distance × consumption ≤ reserve | return, safe_state | simulation |
| HC-013 | Thermal Safety (Safe Haven) | `surface_temp_c`, `solar_angle_deg` | within | TBD(source: §10) | °C, deg | Criterion 5: thermal safety — solar angle and surface temperature limits | safe_state | thermal analysis |
| HC-014 | Communication Visibility Opportunity | `comm_visibility_deg` or `comm_window_min_per_sol` | ≥ | TBD(source: §10) ° or TBD(source: §10) min/sol | deg / min | Criterion 6: communication — Earth/relay visibility angle or window adequacy | all phases | link analysis |
| HC-015 | Emergency Access Distance | `emergency_route_distance_m` | ≤ | TBD(source: §10) | m | Criterion 7: emergency access — safe route distance ≤ limit | surface_exploration, psr_ops, return | simulation |

---

## 3. Hard vs Soft Classification Table

| ID | Class | Rationale |
|---|---|---|
| HC-001 | **Hard** | Vehicle rollover risk — recovery not possible |
| HC-002 | **Hard** | Landing leg damage risk — mission loss |
| HC-003 | **Hard** | Rock avoidance algorithm operates outside guarantee bounds |
| HC-004 | **Hard** | Irregularity inside landing ellipse exceeds landing GNC error budget |
| HC-005 | **Hard** | Vehicle entrapment risk — recovery impossible |
| HC-006 | **Hard** | If vehicle return energy insufficient, mission loss; Compliance Note 3 |
| HC-007 | **Hard** | If thermal margin drops below zero, battery/component damage is permanent |
| HC-008 | **Hard** | If insufficient energy inside PSR, communication + heating severed |
| HC-009 | **Hard** | If charge window insufficient, safe haven is invalid |
| HC-010 | **Hard** | If darkness tolerance exceeded, thermal survival is compromised |
| HC-011 | **Hard** | If no recharge opportunity, safe haven is unsustainable |
| HC-012 | **Hard** | If return energy insufficient, vehicle cannot return — overlaps with HC-006 |
| HC-013 | **Hard** | If thermal limit exceeded, component failure is inevitable |
| HC-014 | **Hard** | If communication severed, ground intervention not possible; autonomous decisions restricted |
| HC-015 | **Hard** | A safe haven without emergency access is non-functional in crisis scenarios |

---

## 4. Classification Note

Examples of soft constraints (not in this catalogue; handled in ranking score):
- Scientific value score
- Surface sample diversity
- Telemetry quality
- Communication bandwidth preference

---

## 4b. Site Finder Metrics — Additional Hard Constraints (A1-EK)

> **Source:** `daniel27-space/lunar-navigator` site finder module (slope/sun/Earth/PSR metrics).
> **Compliance Note 5 reminder:** Site finder ranking does not make safety decisions.
> The weighted sum (sun × w1 + earth × w2 + ...) alone cannot make a safety decision.
> Site finder output is used only to rank candidates that have passed HC.

| ID | Name | Parameter | Operator | Threshold | Unit | Source / Rationale | Phase | Verification Method |
|---|---|---|---|---|---|---|---|---|
| HC-016 | Site Finder Min Sun Fraction | `site_sun_fraction` | ≥ | TBD(source: §10) | fraction (0–1) | lunar-navigator site finder; sun fraction < threshold → charging insufficient | surface_exploration, safe_state | orbit analysis |
| HC-017 | Site Finder Min Earth Visibility Fraction | `site_earth_fraction` | ≥ | TBD(source: §10) | fraction (0–1) | lunar-navigator site finder; Earth visibility < threshold → communication risk | surface_exploration, safe_state | orbit analysis |
| HC-018 | Landing Time Earth Visibility Window | `earth_visibility_confirmed` | == | true | bool | Earth visibility window confirmed [source: earth_visibility_windows.schema.yaml]; mandatory in landing time planning | landing | link analysis |

**Hard vs Soft:** HC-016, HC-017, HC-018 → **Hard** (elimination). Site finder ranking score → Soft (penalty).

---

## 5. Version and Change Management

Whenever a HC threshold changes, `hard_constraints_catalog.yaml` is updated and `schema_version` MINOR is incremented.
Adding a new HC is a MINOR version change; removing an existing HC is a MAJOR version change.
