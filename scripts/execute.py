#!/usr/bin/env python3
"""DRAX — execute phase CLI (thin orchestrator)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))  # noqa: E402

from moonraker.mission import PROVIDER  # noqa: E402
from moonraker.mission_results import compute_mission_results  # noqa: E402


def main() -> int:
    """Run the DRAX plan and print the computed results."""
    brief = PROVIDER.brief()
    plan = PROVIDER.plan(brief)
    outcome = PROVIDER.execute(plan)
    print(f"success: {outcome.success}")
    if outcome.provenance:
        print(f"provenance: seed={outcome.provenance.seed}")
        print(f"  hash={outcome.provenance.input_hash[:16]}...")
    results = compute_mission_results()
    print("DRAX mission results:")
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
