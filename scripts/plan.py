#!/usr/bin/env python3
"""DRAX — plan phase CLI (thin orchestrator)."""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))  # noqa: E402

from moonraker.mission import PROVIDER  # noqa: E402


def main() -> int:
    """Print the DRAX mission execution plan."""
    plan = PROVIDER.plan(PROVIDER.brief())
    print(f"plan steps ({len(plan.steps)}):")
    for step in plan.steps:
        print(f"  - {step.name} :: {step.action} {step.params}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
