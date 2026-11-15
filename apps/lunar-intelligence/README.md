# Lunar Landing Intelligence

English, buildless ES-module frontend using the existing local Three.js distribution. The Python backend is unchanged. No dependency installation is required.

From this directory run `node serve.mjs`, then open http://127.0.0.1:5173 . A generic static HTTP server serving `dist/` also works. Do not open the HTML through file://.

## Structure

- `dist/data.js`: crater metadata and deterministic synthetic site measurements; four nearby sites per crater.
- `dist/scoring.js`: independent normalization, weighted MCDA ranking and synthetic cross-sections.
- `dist/components.js`: crater information, zone list, cluster map, analysis criteria, terrain profile and modal views.
- `dist/moon.js`: WebGL Moon, actual NASA color/height textures, Tycho local mosaic, camera approach and geographic markers.
- `dist/app.js`: synchronized application state and user events.
- `dist/assets/SOURCES.md`: texture source URLs and attribution.

## Model

Weights: smoothness 25%, slope 20%, rock suitability 15%, hazard avoidance 20%, rim clearance 10%, stability 10%. Total is the sum of normalized criterion score times weight; the UI explains each normalization and contribution. This score is NOT a calibrated probability of landing success. Fixture inputs do not constitute NASA measurements or operational thresholds. The analysis is deterministic and does not model date-dependent illumination.

The 4K global mosaic is for visualization. Tycho approach adds an approximately draped 130-km LROC mosaic with baked illumination. Other craters use the global map with lower close-up detail. Candidate locations, crater circles and the local plan are illustrative, not a georeferenced landing product. Candidate proximity and crater containment are verified against the approximate circular metadata boundary.

## Checks

`node check-flow.mjs` validates weight totals, reference calculation, ranking, determinism, candidate containment/proximity, profile changes, invalid input handling and slope sensitivity.

`node browser-check.mjs` uses the locally installed Edge in headless mode. Start `node serve.mjs` first. It validates WebGL and texture loading, all four candidates, synchronized score/profile, details and criterion dialogs, camera approach, crater switching, re-analysis and mobile overflow. Screenshots are written to ignored `outputs/`. This script is Windows-specific and uses debug port 9334.

Google Fonts is optional; system fallbacks are provided. All imagery and Three.js runtime assets are local. WebGL failure leaves the analysis controls usable.
