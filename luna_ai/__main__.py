"""
LUNA-AI pipeline CLI.

Usage:
    python -m luna_ai            # run demo with built-in estimated candidates
    python -m luna_ai --verbose  # show per-dimension scores
"""

from __future__ import annotations

import argparse
import sys


def _fmt_bar(score: float, width: int = 20) -> str:
    filled = round(score * width)
    return "[" + "#" * filled + "." * (width - filled) + f"] {score:.3f}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="luna_ai",
        description="LUNA-AI landing site evaluation pipeline demo",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show per-dimension scores for each ranked candidate",
    )
    args = parser.parse_args(argv)

    try:
        from luna_ai.pipeline import run_pipeline
        from luna_ai.sample_data import CANDIDATES
    except ImportError as exc:
        print(f"Import error: {exc}", file=sys.stderr)
        print("Run from the repo root: python -m luna_ai", file=sys.stderr)
        return 1

    print("=" * 62)
    print("  LUNA-AI  --  Lunar Landing Site Evaluation Pipeline")
    print("  Mode: estimated data demo (south-pole candidates)")
    print("=" * 62)
    print(f"\nInput candidates: {len(CANDIDATES)}")

    result = run_pipeline(CANDIDATES)

    # Hard-constraint filter report
    print("\n-- Hard Constraint Filter " + "-" * 36)
    print(f"  Passed : {result.passed_hc}/{result.total_candidates}")
    if result.rejection_summary:
        print(f"  Rejected ({result.rejected_hc}):")
        for cid, reason in result.rejection_summary:
            print(f"    FAIL  {cid}  ->  {reason}")

    # Ranked results
    print("\n-- Ranked Candidates " + "-" * 41)
    if not result.ranked:
        print("  No candidates survived hard constraint filtering.")
        return 0

    for rank, rc in enumerate(result.ranked, start=1):
        c = rc.candidate
        name = c.crater.name or c.candidate_id
        print(f"\n  #{rank}  {c.candidate_id}  ({name})")
        print(f"      Total score  {_fmt_bar(rc.total_score)}  +/- {rc.score_uncertainty:.3f}")
        if args.verbose:
            print(f"      Science      {_fmt_bar(rc.science_score)}")
            print(f"      Energy       {_fmt_bar(rc.energy_score)}")
            print(f"      Thermal      {_fmt_bar(rc.thermal_score)}")
            print(f"      Comms        {_fmt_bar(rc.communication_score)}")
            print(f"      Risk         {_fmt_bar(rc.risk_score)}")
        print(f"      Slope {c.max_slope_deg:.1f} deg  |  PSR {c.psr_access_fraction:.0%}"
              f"  |  Rocks {c.rock_abundance:.0%}")

    best = result.ranked[0]
    print(f"\n  Recommendation: {best.candidate.candidate_id}"
          f"  ({best.candidate.crater.name})"
          f"  score={best.total_score:.3f}")
    print("=" * 62)
    return 0


if __name__ == "__main__":
    sys.exit(main())
