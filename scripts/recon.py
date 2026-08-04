#!/usr/bin/env python3
"""DRAX — recon phase CLI (thin orchestrator)."""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))  # noqa: E402

from bond_api.protocol import ReconRequest  # noqa: E402

from moonraker.mission import PROVIDER  # noqa: E402

_DEFAULT_GOAL = "assess shuttle-hijack intercept feasibility"


def main() -> int:
    """Run reconnaissance against the default (or argv-supplied) goal."""
    goal = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_GOAL
    report = PROVIDER.recon(ReconRequest(goal=goal))
    print(f"recon goal: {goal}")
    for finding in report.findings:
        print(f"  [{finding.label}] {finding.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
