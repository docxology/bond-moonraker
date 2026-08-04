#!/usr/bin/env python3
"""DRAX — flagship runner: full mission flow + regenerable artifacts.

Runs the five-stage BOND-API mission, recomputes the deterministic mission
results, writes ``output/data/mission_results.json``, renders all three
figures, and resolves the manuscript token tree. Everything written under
``output/`` is regenerable and git-ignored, so re-runs are byte-identical.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))  # noqa: E402

from bond_api.protocol import ReconRequest, run_mission  # noqa: E402

from moonraker import figures  # noqa: E402
from moonraker.mission import PROVIDER  # noqa: E402
from moonraker.mission_results import compute_mission_results  # noqa: E402


def main() -> int:
    """Run the full DRAX mission and regenerate all artifacts."""
    report = run_mission(PROVIDER, ReconRequest("full DRAX mission check"))
    outcomes_stack = report

    results = compute_mission_results()
    data_dir = _PROJECT_ROOT / "output" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "mission_results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    figures.render_timeline_figure()
    figures.render_orbit_figure()
    figures.render_centrifuge_figure()

    print(f"DRAX mission success: {outcomes_stack.outcome.success}")
    print(f"steps: {outcomes_stack.outcome.results.get('steps_completed')}")
    print(f"input hash: {outcomes_stack.outcome.provenance.input_hash[:16]}...")
    print("artifacts written under output/data and output/figures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
