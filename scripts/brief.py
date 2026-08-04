#!/usr/bin/env python3
"""DRAX — brief phase CLI (thin orchestrator)."""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))  # noqa: E402

from moonraker.mission import PROVIDER  # noqa: E402


def main() -> int:
    """Print the DRAX mission brief."""
    brief = PROVIDER.brief()
    print(f"film: {brief.film}")
    print(f"codename: {brief.codename}")
    print(f"objectives ({len(brief.objectives)}):")
    for ob in brief.objectives:
        print(f"  - {ob}")
    print(f"assets ({len(brief.assets)}):")
    for a in brief.assets:
        print(f"  - {a.kind}/{a.name}: {a.payload}")
    print(f"constraints ({len(brief.constraints)}):")
    for c in brief.constraints:
        print(f"  - {c.kind}: {c.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
