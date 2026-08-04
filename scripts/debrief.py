#!/usr/bin/env python3
"""DRAX — debrief phase CLI (thin orchestrator)."""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))  # noqa: E402

from bond_api.protocol import ReconRequest, run_mission  # noqa: E402

from moonraker.mission import PROVIDER  # noqa: E402


def main() -> int:
    """Run the full mission and print the debrief lessons."""
    debrief = run_mission(PROVIDER, ReconRequest("full DRAX mission check"))
    print(f"success: {debrief.outcome.success}")
    print("lessons:")
    for lesson in debrief.lessons:
        print(f"  - {lesson}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
