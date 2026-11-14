# status: draft
# owner: luna-ai-architecture
# depends_on: [infrastructure/decision_log.md (DR-INT-001), config/tbd_register.md (TBD-REPO-001, TBD-REPO-002)]
# open_items: [TBD-REPO-001: submodule vs reference directory decision pending (before M3), TBD-REPO-002: GPU ray-marching flight bridge architecture is a P2 design decision]

# Repo Placement Plan — lunar-navigator

**Source:** daniel27-space/lunar-navigator (2026 NASA Space Apps Challenge)
**Decision (DR-INT-001):** Taken as a reference implementation; not copied verbatim. Code is not modified, only referenced.

---

## Directory Structure

```
luna-ai/
└── reference/
    └── lunar-navigator/     ← git submodule OR reference directory (TBD-REPO-001)
```

**TBD-REPO-001:** `git submodule` or a separate reference directory? Decision to be made before M3.

### Link Map (Code Unchanged — Referenced)

| Reference source | LUNA-AI target | Method |
|----------------|--------------|--------|
| `reference/lunar-navigator/pipeline/` | `data-platform/processing/` | Reference (service wrapper) |
| `reference/lunar-navigator/web/` | `apps/ground-control/` | Prototype (B6 UI_INTEGRATION.md) |

### Used as Input (For Schema Definitions)

| Reference document | LUNA-AI usage |
|-------------------|--------------|
| `reference/lunar-navigator/docs/DATA_CONTRACT.md` | Source reference for A2 schemas (interfaces/) |
| `reference/lunar-navigator/docs/VALIDATION.md` | Source for B4 acceptance criteria (AC-VAL-001..005) |

---

## Production Migration Plan (P0/P1/P2)

| Module | P0 | P1 | P2 |
|--------|----|----|-----|
| `pipeline/ephem/` | Reference | Reference | Reference |
| `horizon.py` | Reference | Reference | Production integrated |
| Disk visibility | Reference | Reference | Production integrated |
| GPU ray-marching (browser) | Prototype | Prototype | Flight bridge TBD-REPO-002 |
| Site finder | Reference (adapted) | Integrated | Integrated |
| When-to-land | Reference | Integrated | Integrated |

**Note:** "Reference" = code is not modified; used via service wrapper or direct call. "Integrated" = data flow connected within the LUNA-AI pipeline.

---

## Limitations and Risks

| Limitation | Source | Impact | Risk |
|------------|--------|--------|------|
| Time range: 2024–2035 | Ephemeris validity | Invalid if mission date is outside | RR-012 |
| DEM resolution: 80 m nominal, 300 m site finder | Source data limit | Small obstacle miss risk | RR-011, RR-015 |
| Observer height sensitivity | 1 m difference can change longest night | SC-009 sensitivity test needed | RR-013 |
| Earth eclipse refraction | Repo does not calculate it | Low confidence for marginal windows | RR-014 |
| Validation range | JPL Horizons ±0.001°, NASA GSFC r≥0.988 | Production value | AC-VAL-001..003 |

---

## Open TBDs

| ID | Parameter | Target Decision Date |
|----|-----------|---------------------|
| TBD-REPO-001 | git submodule vs reference directory | Before M3 |
| TBD-REPO-002 | GPU ray-marching flight segment bridge architecture | P2 start |

---

## Revision History

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-11-14 | Initial draft — C5 task |
