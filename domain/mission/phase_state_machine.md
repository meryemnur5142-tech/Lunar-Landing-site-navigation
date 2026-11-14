# status: draft
# owner: luna-ai-architecture
# depends_on:
#   - docs/architecture/SAFETY_STATE_MACHINE.md  (cross-reference; this file does NOT define safety state)
#   - domain/mission/constraints/hard_constraints_catalog.yaml
#   - docs/qar/QAR_TABLE.md  (QAR-NAV-002)
#   - interfaces/schemas/resource_state.schema.yaml
# open_items:
#   - PSR_OPS entry checklist item 4 threshold QAR-NAV-002.target TBD
#   - SURFACE_EXPLORATION->PSR_OPS authority level tied to B1 autonomy matrix TBD
#   - CRUISE->LANDING transition conditions tied to GNC interface TBD(source: §10)

# Mission Phase State Machine — LUNA-AI v1.1

## 1. Scope and Separation

**IMPORTANT (Compliance Note 1):** This file defines only the **mission phase axis**.

| Axis | Defined In | Role in This File |
|---|---|---|
| Mission phase | This file | Full definition |
| Safety state | `docs/architecture/SAFETY_STATE_MACHINE.md` | Referenced only in the cross-reference matrix in §5 |

The two axes are never merged. The phase machine's interaction with safety state is shown only in the §5 Cross-Reference Matrix.

---

## 2. Phase Definitions

| Phase | Definition | Vehicle Location |
|---|---|---|
| `CRUISE` | Pre-landing in orbit; GNC in lunar orbit | Space (orbit) |
| `LANDING` | Landing GNC active, prior to surface contact; powered descent | Descent path |
| `SURFACE_EXPLORATION` | Nominal surface exploration; non-PSR area | Surface, illuminated area |
| `PSR_OPS` | Operation inside PSR (Permanently Shadowed Region) | Permanent shadow |
| `RETURN` | Active return movement to safe haven | Surface, return route |
| `SAFE_STATE` | Charge/thermal recovery; communication window wait | Safe haven location |

---

## 3. Phase Transition Diagram

```
CRUISE
  │ landing corridor approved + HC-001 candidate passed
  ▼
LANDING
  │ surface contact confirmed + vehicle stable
  ▼
SURFACE_EXPLORATION ◄──────────────────────────────┐
  │ PSR_OPS approval + 6-item checklist OK           │
  ▼                                                  │
PSR_OPS ──► (return condition) ──► RETURN ──► SAFE_STATE
  │                                          │
  │ (charge + thermal + objectives complete)  │
  └──────────────────────────────────────────┘
  (emergency from any phase)
  RETURN ◄── (FDIR: emergency_autonomous)
  SAFE_STATE ◄── (survival mode)
```

---

## 4. Phase Details

### 4.1 CRUISE

**Permitted transitions:**
- CRUISE → LANDING (nominal)

**Transition conditions (CRUISE → LANDING):**
- Landing corridor calculated and approved
- Landing candidate passed HC-001, HC-002, HC-003 (pre-analysis)
- Vehicle fuel budget sufficient TBD(source: §10)
- Communication HC-014 satisfied

**Mandatory check on entry:**
- Navigation system active
- Telemetry nominal

**Exit condition:**
- Powered descent started; GNC switched to landing mode

---

### 4.2 LANDING

**Permitted transitions:**
- LANDING → SURFACE_EXPLORATION (successful landing)
- LANDING → SAFE_STATE (post-landing system check)

**Transition conditions (LANDING → SURFACE_EXPLORATION):**
- Surface contact and stability confirmed
- All HC-001..HC-005 landing site checks passed
- System health check nominal
- `landing_window_validated: true` (source: `interfaces/schemas/landing_window_product.schema.yaml` — lunar-navigator "when-to-land" output)
- `earth_visibility_confirmed: true` (source: `interfaces/schemas/earth_visibility_windows.schema.yaml`) — HC-018 requirement

**Mandatory check on entry:**
- GNC landing algorithm active
- Landing radar/lidar active

**Exit condition:**
- Vehicle in stable state on surface
- All landing constraints satisfied

---

### 4.3 SURFACE_EXPLORATION

**Permitted transitions:**
- SURFACE_EXPLORATION → PSR_OPS (approved PSR entry)
- SURFACE_EXPLORATION → RETURN (return condition satisfied)
- SURFACE_EXPLORATION → SAFE_STATE (charge/thermal requirement)

**Transition conditions (SURFACE_EXPLORATION → PSR_OPS):**
See §4.3.1 Pre-PSR_OPS Mandatory Checklist.

**Transition conditions (SURFACE_EXPLORATION → RETURN):**
- `resource_state.return_reserve_wh <= HC-006.threshold * 1.1` (early warning)
- or ground command (ground_approved)
- or FDIR trigger (emergency_autonomous)

**Mandatory check on entry:**
- Safe haven coordinate loaded
- HC-014 communication satisfied
- Navigation localisation system active

**Exit condition:**
- PSR entry approved (checklist) OR return condition satisfied

#### 4.3.1 Pre-PSR_OPS Mandatory Checklist

All **6** of the following items must be satisfied before transitioning to PSR_OPS phase:

1. **Return reserve:** `resource_state.return_reserve_wh >= HC-006.threshold`
   - Power Management approval required (Compliance Note 3)
2. **Thermal margin:** `resource_state.thermal_margin_c >= HC-007.threshold`
   - Thermal Management approval required
3. **Communication window:** `comm_window >= HC-014.threshold`
   - or pre-planned abort trigger defined (automatic RETURN when uplink severed)
4. **Localisation uncertainty:** `vehicle_pose.position_uncertainty_m <= QAR-NAV-002.target`
   - Navigation system approval required
5. **Scientific objective approval:** Ground segment approval (ground_approved)
   - or autonomous decision matrix (tied to B1 autonomy matrix TBD)
6. **Backup safe haven coordinate:** At least one HC-009..HC-015 approved candidate loaded

---

### 4.4 PSR_OPS

**Permitted transitions:**
- PSR_OPS → RETURN (return condition or FDIR)
- PSR_OPS → SAFE_STATE (emergency survival — FDIR emergency_autonomous)

**Transition conditions (PSR_OPS → RETURN):**
- `resource_state.return_reserve_wh <= HC-006.threshold * 1.1` (10% early warning threshold)
- or scientific objective complete
- or ground command (emergency_return)
- or FDIR trigger

**Transition conditions (PSR_OPS → SAFE_STATE — emergency):**
- FDIR only: `resource_state.power_mode == survival` and return energy insufficient
- When safety state is SURVIVAL (see cross-reference matrix §5)

**Mandatory check on entry:**
- §4.3.1 checklist completed and approved (vehicle_command.psr_entry_checklist_complete: true)

**Exit condition:**
- Return reserve reached 110% threshold OR objectives complete OR FDIR triggered

---

### 4.5 RETURN

**Permitted transitions:**
- RETURN → SAFE_STATE (safe haven reached)
- RETURN → SURFACE_EXPLORATION (return cancelled + sufficient energy; ground approval required)

**Transition conditions (RETURN → SAFE_STATE):**
- Vehicle reached safe haven coordinate (HC-015 distance satisfied)
- HC-009..HC-013 safe haven criteria confirmed satisfied

**Transition conditions (RETURN → SURFACE_EXPLORATION):**
- Ground segment approval (ground_approved)
- `resource_state.return_reserve_wh >= HC-006.threshold * 1.5` (safe margin)
- Thermal margin nominal

**Mandatory check on entry:**
- Return route calculated
- Safe haven coordinate loaded

**Exit condition:**
- Safe haven reached

---

### 4.6 SAFE_STATE

**Permitted transitions:**
- SAFE_STATE → SURFACE_EXPLORATION (recovery complete; ground approval)
- SAFE_STATE → LANDING (mission abort only; ground approval)

**Transition conditions (SAFE_STATE → SURFACE_EXPLORATION):**
- `resource_state.state_of_charge_pct >= HC-008.threshold` (TBD for full charge)
- `resource_state.thermal_margin_c >= HC-007.threshold`
- Ground segment sent new mission package (mission_package.schema.yaml)
- HC-014 communication window active

**Mandatory check on entry:**
- Safe haven HC-009..HC-015 criteria satisfied
- Charging system active

**Exit condition:**
- Ground segment approval + energy/thermal recovery complete

---

## 5. Safety State Cross-Reference Matrix (Compliance Note 1)

Safety states are defined in `docs/architecture/SAFETY_STATE_MACHINE.md`.
This table shows only the phase–state interaction.

| Phase \ Safety State | NOMINAL | CAUTION | RETURN_REQUIRED | SURVIVAL |
|---|---|---|---|---|
| CRUISE | Valid | Valid | Valid | Valid |
| LANDING | Valid | Valid | Mandatory Transition: abort landing + return to orbit | Mandatory Transition: emergency abort |
| SURFACE_EXPLORATION | Valid | Valid; science restricted | Mandatory Transition: → RETURN | Mandatory Transition: → SAFE_STATE |
| PSR_OPS | Valid | Valid; early warning | Mandatory Transition: → RETURN (emergency) | Mandatory Transition: → RETURN or → SAFE_STATE (if energy insufficient) |
| RETURN | Valid | Valid; increase speed | Valid; continue | Mandatory: speed+heater optimisation |
| SAFE_STATE | Valid | Valid; charge priority | Valid; continue charging | Valid; minimum power mode |

**Mandatory Transition Examples:**

- PSR_OPS + SURVIVAL → If return energy sufficient: → RETURN; if insufficient: → SAFE_STATE (nearest)
- SURFACE_EXPLORATION + RETURN_REQUIRED → immediately → RETURN (planner drops mission)
- LANDING + RETURN_REQUIRED → landing abort command (pull back to orbit if fuel sufficient)
