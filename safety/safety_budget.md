# status: draft
# owner: luna-ai-architecture
# depends_on:
#   - domain/mission/constraints/hard_constraints_catalog.yaml  (HC-006, HC-007, HC-008)
#   - interfaces/schemas/resource_state.schema.yaml
#   - interfaces/schemas/earth_visibility_windows.schema.yaml  (A4-EK: communication outage budget)
#   - docs/architecture/SAFETY_STATE_MACHINE.md
# open_items:
#   - return_reserve_wh calculation model TBD(source: §10 Power Mgmt vehicle parameters)
#   - thermal_margin_c critical component list TBD(source: §10)
#   - uncertainty_margin_pct value TBD (estimated +20%, to be confirmed from vehicle testing)
#   - update_period TBD (synchronised with navigation update period)
#   - max_communication_outage_hours TBD(source: hardware + repo lunar-navigator 60-day window data)

# Safety Budget Mechanism — LUNA-AI v1.1

## 1. Mechanism Definition and Ownership (Compliance Note 3)

```
Power Management  ──calculates──►  Reports to planner (resource_state.schema.yaml)
                                          │
                                          ▼
                             Planner applies as hard constraint
                             (HC-006, HC-007 — Compliance Note 5)
```

**The planner does NOT calculate the budget.** It only applies the values
received from the `resource_state` message as hard constraints.

Two budget dimensions are defined:
1. **Return Energy Reserve** — owned by Power Management
2. **Thermal Margin** — owned by Thermal Management (integrated with Power Management)
3. **Maximum Communication Outage Duration** — reported by Communication Management (A4-EK)

---

## 2. Return Energy Reserve

### 2.1 Calculation Formula

```
return_reserve_wh =
    f(distance_m, terrain_resistance, speed_ms, heater_load_w, uncertainty_margin)

= (distance_m × energy_per_m_wh/m)
  + (heater_load_w × estimated_return_duration_s / 3600)
  + uncertainty_margin_wh

Where:
  energy_per_m_wh/m  = TBD(source: §10 vehicle wheel/motor parameters)
  heater_load_w      = resource_state.heater_power_w (provided by Power Mgmt)
  uncertainty_margin = return_reserve_wh * uncertainty_pct
  uncertainty_pct    = TBD(source: §10 vehicle testing) — estimated +20%
```

### 2.2 Input Sources

| Parameter | Providing Module | Schema/Reference |
|---|---|---|
| `distance_m` (current position → safe haven) | Navigation | `vehicle_pose.schema.yaml` |
| `terrain_resistance` (terrain map) | Planetary Data | `environment_product.schema.yaml` |
| `heater_load_w` | Power Management | `resource_state.schema.yaml` |
| `uncertainty_margin` | Power Management | §10 vehicle test parameter |

### 2.3 Update Rule

Recalculated synchronously with every navigation update.
Update period: TBD(source: §10 navigation system frequency).

As distance increases, position uncertainty grows → reserve estimation error grows →
uncertainty margin must be dynamically updated:

```
uncertainty_margin_wh(t) = base_margin_wh + k × position_uncertainty_m(t)
  k = TBD(source: §10)
```

### 2.4 Relationship with HC-006

The `resource_state.return_reserve_wh` field is compared against the HC-006 threshold.
The HC-006 threshold is set by Power Management (TBD §10).
The planner performs the comparison and applies it as a hard constraint.

---

## 3. Thermal Margin

### 3.1 Calculation Formula

```
thermal_margin_c = min(T_limit_c[i] - T_current_c[i])  for i in critical_components

Critical components:
  - battery           (T_limit: TBD §10)
  - main_computer     (T_limit: TBD §10)
  - motor_drivers     (T_limit: TBD §10)
```

Thermal model: vehicle-design-specific. VIPER 50 s tolerance is not directly transferred. TBD(source: §10).

### 3.2 Relationship with HC-007

The `resource_state.thermal_margin_c` field is compared against the HC-007 threshold.
At PSR_OPS entry, HC-007 is item 2 of the mandatory checklist (phase_state_machine.md §4.3.1).

---

## 4. Budget Violation → FDIR Trigger

| Condition | Threshold | FDIR Action | Safety State Transition |
|---|---|---|---|
| `return_reserve_wh < HC-006.threshold × 1.1` | Early warning (110%) | Notify planner; continue current phase | CAUTION |
| `return_reserve_wh <= HC-006.threshold` | Critical | Trigger mandatory RETURN phase | RETURN_REQUIRED |
| `thermal_margin_c < 5°C` | Warning (threshold TBD §10) | Heater prioritisation | CAUTION |
| `thermal_margin_c <= 0°C` | Critical | Survival mode; all science disabled | SURVIVAL |
| `comm_outage_elapsed_hr >= max_communication_outage_hours × 0.9` | Early warning | Notify planner | CAUTION |
| `comm_outage_elapsed_hr >= max_communication_outage_hours` | Critical | RETURN or SAFE_STATE | RETURN_REQUIRED |

> **Note:** Safety state transitions are defined in `docs/architecture/SAFETY_STATE_MACHINE.md`.
> This table shows only the FDIR actions triggered by a budget violation.

---

## 5. Uncertainty Accumulation Model

```
As time / distance increases:
  position_uncertainty_m(t) ↑
    → distance estimation error ↑
      → return_reserve_wh calculation error ↑
        → safety margin must be dynamically updated

Update rule: recalculate on every navigation update.
After a localisation correction (landmark, region detection), uncertainty is reset.
```

---

## 6. Maximum Communication Outage Duration (A4-EK)

**Owner:** Communication Management — calculates and reports.
**Consumer:** Power Management and Planner — applies as hard constraint (Compliance Note 3 is maintained).

```
max_communication_outage_hours = TBD(source: hardware + repo lunar-navigator 60-day window data)
```

**Source:** `daniel27-space/lunar-navigator` — 60-day sun/Earth window analysis,
"longest night/communication gap" metric.

**Schema reference:** `interfaces/schemas/earth_visibility_windows.schema.yaml`
(longest outage duration: `longest_outage_duration_hours` field).

**Why TBD:** The actual value depends on vehicle hardware (receiver/transmitter) sensitivity.
The repo metric is a reference ceiling; the operational threshold will be set with §10 hardware data.

---

## 7. HC References

| HC ID | Related Parameter | Role in This File |
|---|---|---|
| HC-006 | `return_reserve_wh` | Calculation output of §2; critical threshold |
| HC-007 | `thermal_margin_c` | Calculation output of §3; critical threshold |
| HC-008 | `battery_soc_pct` | SoC check before PSR entry |
| HC-014 | `comm_visibility_deg` / window | Related to §6 communication outage budget |
