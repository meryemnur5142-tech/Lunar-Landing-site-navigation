# status: draft
# owner: luna-ai-architecture
# depends_on: [interfaces/earth_visibility.schema.yaml, interfaces/multi_site_comparison.schema.yaml, interfaces/landing_window_validation.schema.yaml, infrastructure/repo_placement.md]
# open_items: [GPU ray-marching browser bridge TBD (P2 design decision — TBD-REPO-002), 5-site comparison layout UX design pending]

# Ground Control UI Integration Plan — lunar-navigator → LUNA-AI

Source: daniel27-space/lunar-navigator UI components (2026 NASA Space Apps Challenge)

---

## Components and Integration

### Earth Visibility Layer

- **Source:** lunar-navigator repo directly (reference)
- **Display:** "Is Earth visible on the horizon? When does it change?" indicator
- **Data source:** `interfaces/earth_visibility.schema.yaml`
- **Update:** Live update when time slider moves

**CRITICAL (Compliance Note 6):** This layer shows geometric visibility only — whether Earth is on the horizon. §4.7 communication link planning (data rate, queue management, window assignment) is a SEPARATE layer. They are not merged in the UI, and are not shown in the same panel.

---

### Site Card

- **Content:** Solar geometry + Earth visibility + visibility change time
- **Data source:** `interfaces/multi_site_comparison.schema.yaml`
- **Shown per site:** `sun_fraction`, `earth_fraction`, `longest_night_hours`, `longest_outage_hours`, `terrain_resolution`

---

### "When to Land" Panel

- **Source:** lunar-navigator landing-window (7/14/30-day stay analysis)
- **UI role:** Landing time recommendation — operator decision input screen
- **Important:** This panel provides a recommendation; final landing time selection is GCA (operator approval) — aligned with B1-EK
- **Link to phase machine:** Approved window is passed to mission execution layer via `interfaces/landing_window_validation.schema.yaml`

---

### Multi-Site Comparison

- **Repo capacity:** 2–3 sites
- **LUNA-AI extension:** 5-site comparison
- **Columns per site:**

| Column | Source field | Description |
|--------|-------------|-------------|
| Sun fraction | `sun_fraction` | 0.0–1.0 |
| Earth visibility fraction | `earth_fraction` | 0.0–1.0 |
| Longest night | `longest_night_hours` | Hours |
| Longest communication outage | `longest_outage_hours` | Hours |
| DEM resolution | `terrain_resolution` | 80m / 300m / 2700m |

---

### Polar Horizon Chart

- **Display:** Position of Sun and Earth relative to the local horizon (720-ray horizon profile)
- **Source:** lunar-navigator `pipeline/terrain/horizon.py`
- **Observer height input:** `observer_height_m` = TBD-HEIGHT-001 (aligned with SC-009 sensitivity)

---

### Time Slider

- Table and chart update live as user changes time
- **temporal_class rule (aligned with B5-EK):**
  - Past time → `temporal_class: historical`
  - Future time → `temporal_class: predicted`
- When slider position changes, `temporal_class` updates automatically; warning label is shown

---

## GPU Ray-Marching Note

- Lunar-navigator 3D GPU shadow ray-marching runs in-browser
- **LUNA-AI flight segment bridge:** TBD-REPO-002 (P2 design decision)
- **For now:** Kept as a prototype under `apps/ground-control/`; production integration will be scoped to P2

---

## Connection Map

| UI Component | Schema | Producer Module |
|--------------|--------|----------------|
| Earth Visibility Layer | `interfaces/earth_visibility.schema.yaml` | communication/ |
| Site Card / Comparison | `interfaces/multi_site_comparison.schema.yaml` | simulation/environment-model |
| When to Land Panel | `interfaces/landing_window_validation.schema.yaml` | apps/ground-control → autonomy/mission-executive |
| Polar Horizon Chart | — | simulation/environment-model (horizon.py) |

---

## Revision History

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-11-14 | Initial draft — B6 task |
