# LUNA-AI — Lunar Crater Exploration and Autonomous Mission System

An autonomous mission system that evaluates lunar craters with scientific and operational data,
provides access to PSRs, and manages safe return under energy-thermal constraints.

## Architecture Segments

| Segment | Responsibility |
|---|---|
| **Ground Segment** | Scientific analysis, mission design, operator interface |
| **Flight Segment** | Real-time navigation, safety, motion control |
| **Simulation & Validation** | Digital twin, scenario tests, fault injection |

## Folder Structure

```
docs/           — Architecture documents (ConOps, QAR, FMEA, ADR)
domain/         — Domain models (crater, environment, mission, resources)
data-platform/  — Planetary data ingestion and processing pipeline
mission-intelligence/ — Candidate filtering, ranking, scientific objectives
interfaces/     — Versioned data contracts (ICD)
tests/          — Unit, integration, system tests
```

## Development Status

Aerospace hardware data pending (battery, panel, thermal parameters).
Until that data arrives: architecture documents + scientific data platform are under development.

## Reference

Architecture prompt file: `LUNA-AI_Mimari_Prompt_Dosyasi.md`
