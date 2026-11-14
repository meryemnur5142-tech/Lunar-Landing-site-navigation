# status: draft
# owner: luna-ai-architecture
# depends_on: [interfaces/schemas/vehicle_command.schema.yaml, mission-intelligence/constraints/hard_constraints.py, docs/conops/]
# open_items: [authority_level field alignment with vehicle_command.schema.yaml pending schema finalization, ACL timeout durations TBD(source: §10)]

# Autonomy Matrix — LUNA-AI v1.1

## Purpose

This document defines under what conditions the LUNA-AI vehicle takes decisions autonomously (OTN), awaits ground approval (GCA), that an operation is prohibited in that phase (YAS), or activates only in an FDIR abort scenario (ACL).

**Important:** Mission phases (CRUISE/LANDING/SURFACE_EXPLORATION/PSR_OPS/RETURN/SAFE_STATE) and safety states (NOMINAL/CAUTION/RETURN_REQUIRED/SURVIVAL) are SEPARATE axes. This matrix uses the mission phase axis.

---

## Symbol Definitions

| Symbol | Meaning | Description |
|--------|-------|----------|
| **OTN** | Autonomous | Vehicle decides independently, no ground approval required |
| **GCA** | Ground-Control Approved | Awaits command; on timeout, wait or move to safe haven |
| **YAS** | Prohibited | This decision type is not applicable in this mission phase |
| **ACL** | Emergency-Autonomous | Only in FDIR abort scenario; GCA or YAS in normal operations |

---

## Main Matrix — Normal Operations

> **Note:** Hard constraints (HC-001..015) are always evaluated first. The matrix shows the authority level after the HC set is passed.

| Mission Phase | Route Change | Science Target Abandon | PSR Entry | Safe Haven Change | Emergency Return | Science Payload On/Off | Mode Change |
|------------|-----------------|---------------------|------------|----------------------|------------|------------------------|-----------------|
| **CRUISE** | YAS | YAS | YAS | YAS | ACL | YAS | GCA |
| **LANDING** | YAS | YAS | YAS | YAS | ACL | YAS | ACL |
| **SURFACE_EXPLORATION** | OTN | OTN | GCA | GCA | ACL | OTN | OTN |
| **PSR_OPS** | OTN¹ | GCA | YAS² | GCA³ | ACL | GCA | OTN |
| **RETURN** | OTN | YAS | YAS | GCA | ACL | OTN | OTN |
| **SAFE_STATE** | YAS | YAS | YAS | GCA | ACL | YAS | GCA |

**Footnotes:**

¹ PSR_OPS route change: OTN only within pre-approved PSR map boundaries; going outside boundaries requires GCA.

² PSR entry: Entry prohibited without return reserve (HC-006) verification. Transition from SURFACE_EXPLORATION to PSR_OPS is always GCA.

³ Safe haven change inside PSR: Coordinates or primary route cannot be updated (orbital map update not possible inside PSR). Backup safe haven selection (if SC-005 triggered) is ACL.

---

## Communication Loss Matrix

Authority levels for the same decision types when telemetry link is lost:

| Mission Phase | Route Change | Science Target Abandon | PSR Entry | Safe Haven Change | Emergency Return | Science Payload On/Off | Mode Change |
|------------|-----------------|---------------------|------------|----------------------|------------|------------------------|-----------------|
| **CRUISE** | YAS | YAS | YAS | YAS | ACL | YAS | ACL |
| **LANDING** | YAS | YAS | YAS | YAS | ACL | YAS | ACL |
| **SURFACE_EXPLORATION** | OTN | OTN | WAIT⁴ | OTN⁵ | ACL | OTN | OTN |
| **PSR_OPS** | OTN⁶ | ACL⁷ | YAS | ACL⁸ | ACL | ACL | OTN |
| **RETURN** | OTN | YAS | YAS | OTN | ACL | OTN | OTN |
| **SAFE_STATE** | YAS | YAS | YAS | ACL | ACL | YAS | ACL |

**Footnotes (Communication Loss):**

⁴ PSR entry during link loss: Vehicle waits (if no pre-planned abort trigger). Wait duration: TBD(source: §10 — link recovery window). On timeout, PSR entry cancelled, wait safely.

⁵ Safe haven change (SURFACE_EXPLORATION, no link): OTN selection from pre-planned backup safe haven list. If not in list, wait at current coordinates.

⁶ PSR_OPS route change (no link): Continue within pre-approved boundaries OTN. If energy warning triggered, ACL return.

⁷ Science target abandon (PSR, no link + FDIR warning): ACL — return has priority.

⁸ Safe haven change (PSR, no link): ACL backup safe haven selection only if energy critical + primary route blocked.

**Special Case: Link lost inside PSR + energy critical:**
→ ACL emergency return triggered. FDIR → RETURN_REQUIRED transition → Power Mgmt confirms return reserve → Planner generates route.

---

## Pre-Planned Abort Trigger List

When any of the following conditions occur, the vehicle applies the specified action without waiting for ground approval:

| Trigger ID | Condition | Action | Phase |
|------------|-------|-------|-----|
| ABT-001 | `return_reserve_wh < HC-006_threshold` | ACL emergency return initiation | PSR_OPS, SURFACE_EXPLORATION |
| ABT-002 | `position_uncertainty_m > QAR-NAV-002_threshold` | Stop, search landmark, return if unsuccessful | SURFACE_EXPLORATION, PSR_OPS |
| ABT-003 | `thermal_margin_c < 0` | ACL max heater + return evaluation | All surface phases |
| ABT-004 | `link_timeout > TBD(source: §10)` AND phase=PSR_OPS AND `energy_critical=true` | ACL emergency return | PSR_OPS |
| ABT-005 | `safe_haven_route_blocked=true` AND `backup_safe_haven=none` | SURVIVAL mode preparation | All surface phases |
| ABT-006 | `fdir_abort_flag=true` | ACL action per mission (§4 FDIR tree) | All phases |

---

## Decisions Requiring Operator Approval (GCA Cells)

The following decisions always require ground operator approval:

1. **PSR entry** (from all phases) — Cannot enter without verifying return reserve, thermal status, communication window
2. **Safe haven change** (in SURFACE_EXPLORATION, PSR_OPS, RETURN, SAFE_STATE) — 7-criteria validation is ground-side responsibility
3. **Science target abandon** (in PSR_OPS) — Science priority change is mission authority decision
4. **Mode change** (in CRUISE, SAFE_STATE) — Critical phase transitions require manual approval
5. **PSR_OPS route change** (outside boundaries) — Map update requires ground-side validation

---

## Cross-Reference: vehicle_command.schema.yaml

Authority levels in this matrix are aligned with `interfaces/schemas/vehicle_command.schema.yaml` → `authority_level` field:
- `OTN` → `authority_level: "autonomous"`
- `GCA` → `authority_level: "ground_approved"`
- `ACL` → `authority_level: "emergency_autonomous"`
- `YAS` → command submission rejected in `authority_level` validation

---

---

## Mission Planning Decisions — Ground Approval Required (B1-EK)

The following decisions, outside the autonomy matrix but within v1.2 integration scope, are additional decision types requiring operator approval (GCA):

| Decision Type | Authority | Justification |
|-----------|---------|---------|
| **Site finder decision** | GCA | Final landing region selection is a mission authority decision; algorithmic ranking (site finder weighted score) provides input, does not decide |
| **"When to land" / landing window selection** | GCA | Sun/Earth geometry proposes a window; landing time selection requires ground control approval even for unmanned missions |
| **Multi-region comparison / region selection** | GCA | Final selection from 2–5 regions is a mission authority decision |
| **Geometry update (prediction improvement)** | OTN | Calculation improvement (JPL Horizons update etc.) can be autonomous; no approval required if region or time selection is not changed |

**Important distinction:** Site finder algorithm and "when to land" analysis produce a decision *proposal*. Final region-time selection is always GCA. Geometric calculation update (e.g. recalculation with new ephemeris data) can be OTN.

---

## Revision History

| Version | Date | Change |
|----------|-------|------------|
| 0.1 | 2026-11-14 | First draft — B1 task |
| 0.2 | 2026-11-14 | B1-EK: Site finder, landing window, multi-region comparison GCA decisions added |
