# status: draft
# owner: luna-ai-architecture
# depends_on: [mission-intelligence/constraints/hard_constraints.py, docs/adr/, docs/conops/]
# open_items: [DL-002 safe haven 5+2 split not yet finalised — ADR required]

# Decision Log — LUNA-AI v1.1

## Purpose

This document records the architectural and design decisions taken within the LUNA-AI v1.1 scope, together with their rationale and v1.0 references.

---

## Decision Table

| ID | Date | Decision | Rationale | v1.0 Reference | Status |
|----|------|----------|-----------|----------------|--------|
| DL-001 | 2026-11-14 | HC-001..015 classified as hard constraints; soft constraint list kept separate | A hard constraint violation endangers mission safety and can never be overridden. A soft constraint is an optimisation target; violation is acceptable but recorded. | v1.0 §2, §6 | CLOSED |
| DL-002 | 2026-11-14 | Safe haven criteria: 5 hard + 2 soft split under evaluation — not yet finalised | Classifying all 7 criteria as hard constraints may be overly restrictive; emergency access and darkness interval tolerance could be considered soft. ADR to be prepared. | v1.0 §4.8, Compliance Note 2 | OPEN |
| DL-003 | 2026-11-14 | Mission phase (CRUISE/LANDING/SURFACE_EXPLORATION/PSR_OPS/RETURN/SAFE_STATE) and safety state (NOMINAL/CAUTION/RETURN_REQUIRED/SURVIVAL) defined as SEPARATE axes | Mixing the two produces an ambiguous state machine; the phase axis defines the autonomy matrix, the safety state axis defines abort logic. Cross-effects are documented and traceable. | Compliance Note 1, v1.0 §4.3, §4.6 | CLOSED |
| DL-004 | 2026-11-14 | Safety budget flow direction: Power Management owns it, Planner consumes it | Power Mgmt knows the energy policy; allowing the Planner to independently set energy policy produces inconsistent behaviour. Single-source principle. | Compliance Note 3, v1.0 §5 | CLOSED |
| DL-005 | 2026-11-14 | `temporal_class` field defined as a required field in all environment product TypedDicts | Mixing historical and predicted data in the same field carries a validation error risk. Required field, None rejected, zero mixing target. | v1.0 §6, data-type mixing risk noted in Compliance Notes | CLOSED |
| DL-006 | 2026-11-14 | JSON Schema defined separately in addition to Python TypedDict for ground-vehicle interoperability | Ground control software may not use Python; JSON Schema provides a language-independent contract. TypedDict for intra-Python validation, JSON Schema for inter-service contracts. | v1.0 §3 (ICD) | CLOSED |

---

## v1.2 Integration Decisions (C6 — lunar-navigator integration)

### DR-INT-001: Repo Taken as Reference Implementation

| Field | Value |
|-------|-------|
| **Date** | 2026-11-14 |
| **Decision** | daniel27-space/lunar-navigator is not copied; it is linked as a reference implementation (git submodule or reference directory — TBD-REPO-001). |
| **Rationale** | Rewriting is unnecessary work; copying produces technical debt; wrapping as a service loses the browser-GPU advantage. Code is not changed, only referenced. |
| **v1.0 Reference** | — (New integration decision) |
| **Status** | OPEN (submodule vs. reference directory TBD) |

### DR-INT-002: Site Finder Ranking Does Not Make Safety Decisions

| Field | Value |
|-------|-------|
| **Date** | 2026-11-14 |
| **Decision** | A weighted total (site finder weighted score) alone does not make a safety decision; hard constraints are checked first. |
| **Rationale** | Systems that delegate safety decisions to a ranking algorithm can hide HC violations. HC set always first; ranking after. |
| **v1.0 Reference** | Compliance Note 5; v1.0 §2, §6 |
| **Status** | CLOSED |

### DR-INT-003: Earth Visibility ≠ Communication Link Planning

| Field | Value |
|-------|-------|
| **Date** | 2026-11-14 |
| **Decision** | The repo's "is Earth visible above the horizon?" calculation (geometric visibility) and §4.7 communication link planning (data rate, queue management, window assignment) are separate layers. They are not combined in the UI. |
| **Rationale** | Geometric visibility is a necessary but not sufficient condition; link budget, queue state, and window assignment are separate calculations. Mixing them can lead to a false "link ready" decision. |
| **v1.0 Reference** | v1.0 §4.7, Compliance Note 6 |
| **Status** | CLOSED |

### DR-INT-004: Resolution and Time Range Limits as Required Fields

| Field | Value |
|-------|-------|
| **Date** | 2026-11-14 |
| **Decision** | `terrain_resolution` and `ephemeris_validity_range` are defined as required fields in A2 schemas; they are not hidden when data is retrieved. |
| **Rationale** | Hiding from the user at what resolution and in what time range valid data is served creates false confidence. Limits must be transparent and always visible. |
| **v1.0 Reference** | Compliance Note 7 |
| **Status** | CLOSED |

---

## DR-README-001: README Section Reference Corrections
Date: 2026-11-14
Changes:
- `vehicle/README.md`: §4.2 → §4.6 (Navigation & Mobility); Compliance Note 4 added (landing GNC / surface nav separation)
- `safety/README.md`: §4.6 → §4.8 (Flight Safety & Fault Management); Compliance Note 3 added (safety budget ownership)
- `infrastructure/README.md`: §1 → §10 (Vehicle Parameters / General)
- `simulation/README.md`: Lunar-Navigator integration note added (SPICE, horizon, visibility pipeline references)
- Missing READMEs (mission_intelligence, apps/ground-control, vehicle/localization, vehicle/mobility-control): files absent; not created per rule; note added to open_items.

---

## Revision History

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-11-14 | Initial draft — C2 task, DL-001..006 |
| 0.2 | 2026-11-14 | C6 appendix: DR-INT-001..004 — lunar-navigator integration decisions |
| 0.3 | 2026-11-14 | DR-README-001: README section references and compliance notes corrected |
