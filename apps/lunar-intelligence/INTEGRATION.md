# Lunar Landing Intelligence UI

This is a Three.js WebGL frontend that visualises lunar landing site evaluation for the
LUNA-AI project. It renders NASA moon textures, three craters (Shackleton, Haworth,
Nobile), four candidate landing zones per crater, and MCDA (Multi-Criteria Decision
Analysis) scores for each zone, giving mission planners an interactive 3-D overview of
candidate sites.

## Serving

**Standalone (Node):** from `apps/lunar-intelligence/`, run:
```
node serve.mjs
```
Then open http://localhost:3000 in a browser.

**Via FastAPI:** when the LUNA-AI Ground Control API is running (`uvicorn
apps.ground_control.api.main:app --reload` from the repo root), the UI is also available
at http://localhost:8000/lunar-ui — served by the `/lunar-ui` StaticFiles mount added to
`apps/ground_control/api/main.py`.

## Data and future work

The UI currently uses its own synthetic scoring data defined in `dist/data.js`. Connecting
it to live MCDA scores produced by the LUNA-AI backend pipeline is a planned future work
item.
