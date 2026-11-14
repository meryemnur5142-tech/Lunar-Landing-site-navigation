---
status: draft
owner: luna-ai-architecture
depends_on:
  - domain/mission/constraints/hard_constraints_catalog.yaml  (A1-EK: HC-016..HC-018)
  - interfaces/schemas/environment_product.schema.yaml  (A2-EK: terrain_resolution, ephemeris_validity_range)
  - interfaces/schemas/earth_visibility_windows.schema.yaml
  - interfaces/schemas/multi_site_geometry_product.schema.yaml
  - interfaces/schemas/landing_window_product.schema.yaml
  - domain/mission/phase_state_machine.md  (A3-EK: LANDING entry conditions)
  - safety/safety_budget.md  (A4-EK: max_communication_outage_hours)
open_items:
  - repo submodule path TBD (direct submodule vs fork vs reference — integration decision)
  - production migration schedule TBD
  - GPU ray-marching browser→flight segment bridge TBD(source: §10 vehicle computer capacity)
---

# Repo Integration Map — lunar-navigator → LUNA-AI

**Source:** `daniel27-space/lunar-navigator` (NASA Space Apps Challenge 2026)
**Validation:** JPL Horizons ±0.001°, NASA GSFC r=0.988/0.993

**Strategy:** Reference implementation — not copied, linked.
The hackathon prototype provides a strong algorithmic foundation; it is not embedded
directly into the LUNA-AI production segment, but referenced and wrapped with vehicle-safe interfaces.

---

## 1. Component Map

| Repo Module | LUNA-AI Target | Integration Type | Adaptation Note |
|---|---|---|---|
| `pipeline/ephem/` (SPICE DE440) | `data-platform/processing/ephemeris/` | Reference | Taken unchanged |
| `pipeline/terrain/horizon.py` + `web/src/lib/horizon.ts` (720-ray) | `data-platform/processing/horizon/` | Reference | Taken unchanged |
| Sun/Earth disk visibility calculation | `data-platform/processing/visibility/` | Reference | Taken unchanged |
| 3D GPU shadow ray-marching | `apps/ground-control/` prototype UI | Prototype kept | Pre-production review required; browser-only → flight bridge TBD |
| Site finder (slope/sun/Earth/PSR) | `mission-intelligence/candidate-filter/` | Reference; ranking reorganised | Compliance Note 5: ranking does not make safety decisions; HC elimination comes first |
| "When to land" (7/14/30 days) | `mission-intelligence/landing-window-optimizer/` | Directly usable | Wrapped with `landing_window_product.schema.yaml` interface |
| Multi-site comparison (2–3) | `mission-intelligence/multi-site-time-comparator/` | Extended | 2–3 → 5 sites; `multi_site_geometry_product.schema.yaml` |
| 60-day sun/Earth window + longest night/outage | Safety budget §4.7 Communication + §4.5 Thermal | Directly usable | Compliance Note 6: visibility ≠ link planning |
| `docs/DATA_CONTRACT.md` | A2 data contracts (`interfaces/schemas/`) | Input | Derived; extended |
| `docs/VALIDATION.md` | B4 acceptance criteria | Validation evidence | JPL/NASA GSFC/Gläser references |

---

## 2. Taken Unchanged / Adapted / Rewritten

### Taken Unchanged
- `pipeline/ephem/` — SPICE DE440 ephemeris pipeline
- `pipeline/terrain/horizon.py` and `horizon.ts` — 720-ray horizon scan algorithm
- Sun/Earth disk visibility calculation
- "When to land" window calculation logic

### Adapted
- **Site finder ranking:** HC elimination applied first; weighted total only ranks passing candidates (Compliance Note 5)
- **Multi-site comparison:** Extended from 2–3 sites to 5; packaged with `multi_site_geometry_product.schema.yaml` interface
- **60-day window output:** Connected to `earth_visibility_windows.schema.yaml` and `safety_budget.md §6` interfaces

### Requiring Pre-Production Review
- **GPU ray-marching:** Browser-only prototype; flight segment bridge TBD (vehicle computer GPU capacity §10)

### Rewritten
- None (within v1.1 scope)

---

## 3. Repo's Known Limitations — How LUNA-AI Addresses Them

| Limitation | LUNA-AI Solution |
|---|---|
| Resolution: 80 m / 300 m / 2.7 km | A2 `terrain_resolution` field is required; declared openly to the planner; not hidden (Compliance Note 7) |
| Time range: 2024–2035 (SPICE DE440) | A2 `ephemeris_validity_range` field is required; product outside this range is rejected |
| Observer height sensitivity ("a mast a metre taller can halve the longest night") | B2 scenario; B3 risk register; operational vehicle height taken from §10 |
| Earth eclipse refraction ignored | B3 risk register; source of uncertainty; reflected in `uncertainty_minutes` field |
| Site finder 300 m cell resolution | B3 risk register; noted in A1 HC-001..HC-005 notes; 80 m validation may be needed |

---

## 4. Key Compliance Notes

| Compliance Note | Content | Reflection in This Document |
|---|---|---|
| **Compliance Note 5** | HC elimination first; ranking score cannot bypass elimination | §1 site finder row; §2 adaptation note |
| **Compliance Note 6** | "Is Earth visible above the horizon?" ≠ communication link planning | §1 60-day window row |
| **Compliance Note 7** | Resolution/time limits not hidden; required field in A2 | §3 first two rows |
| **Compliance Note 8** | Repo is a hackathon prototype; referenced, not copied verbatim | §2 strategy paragraph |

---

## 5. Integration Decisions (Open Items)

| Decision | Option | Status |
|---|---|---|
| Repo link type | git submodule / fork / API call | TBD — submodule path to be determined |
| GPU ray-marching migration | Keep browser-only / write flight bridge | TBD(source: §10 vehicle computer) |
| Production migration timing | M4 / M5 | TBD |
| Validation: longest night metric conversion to flight acceptance criterion | B4 acceptance test | TBD — B-series task |
