# Mission Intelligence

**v1.0 Reference:** §4.1 Mission Intelligence

Filters, ranks, and packages target crater candidates into mission packages.

## Sub-modules

- `candidate-filter/` — Hard constraint elimination (HC first, then ranking)
- `scoring/` — Multi-criteria weighted scoring (CandidateScorer)
- `science-objectives/` — Scientific objective definitions

## Compliance Note 5

A weighted total alone does not make a safety decision.
Candidate ranking is applied after hard constraint elimination.
See `domain/mission/constraints/hard_constraints_catalog.md`
