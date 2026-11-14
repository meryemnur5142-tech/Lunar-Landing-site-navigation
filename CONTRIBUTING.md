# LUNA-AI Contribution Guide

## Development Environment Setup

Python 3.11 or later is required.

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .\.venv\Scripts\Activate.ps1  # Windows PowerShell

pip install -r requirements.txt
```

## Running Tests

```bash
# All tests
make test
# or
PYTHONPATH=. python -m pytest tests/ -v --tb=short

# Unit tests only
make test-unit

# Integration tests only
make test-integration
```

CI runs all tests automatically on every PR. Run `make test` locally before opening a PR.

## Lint

```bash
make lint
```

## Branch Strategy

- `main` — stable, protected branch; no direct pushes.
- `feature/<short-description>` — new features and improvements.
- `fix/<short-description>` — bug fixes.
- `docs/<short-description>` — documentation-only changes.

Open a new branch from `main` for every change and merge via PR. No self-merges; melek or the responsible engineer merges after CI is green.

## Commit Message Format

```
<type>: short description (≤72 characters)

Optional body: what you changed and why.
```

Types: `feat` / `fix` / `docs` / `chore` / `test` / `refactor`

Example:
```
feat: add HC-004 landing ellipse size constraint

ICD-003 parameters confirmed; HC-004 added to default_constraints()
with semi_major_m <= 750 m threshold.
```

## Compliance Notes Checklist

Review v1.1 compliance notes (1–8) before opening each PR:

| # | Topic | Check |
|---|-------|-------|
| 1 | Safety budget ownership in `power/` module | [ ] |
| 2 | Planner is consumer; makes no safety decisions | [ ] |
| 3 | Safety budget owned by `power/`; planner is consumer | [ ] |
| 4 | Landing GNC and surface nav separation maintained | [ ] |
| 5 | Weighted total alone does not make a safety decision | [ ] |
| 6 | Geometric visibility ≠ link planning separation | [ ] |
| 7 | HC elimination applied before ranking | [ ] |
| 8 | FDIR response times meet QAR thresholds | [ ] |

Provide justification in the PR description for any notes that do not apply.
