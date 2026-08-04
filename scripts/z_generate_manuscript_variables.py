#!/usr/bin/env python3
"""DRAX — generate/inject manuscript variables (thin orchestrator).

Writes ``output/data/manuscript_variables.json`` and substitutes ``{{TOKEN}}``
markers into ``output/manuscript/``. Strict mode (default) requires
``output/data/mission_results.json`` to exist; ``--allow-draft`` relaxes that.

Exit codes:
    0   variables written and injected successfully
    2   strict mode could not find the analysis outputs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))  # noqa: E402

from moonraker.manuscript_variables import (  # noqa: E402
    generate_variables,
    save_variables,
    write_resolved_manuscript_tree,
)


def main() -> int:
    """Generate manuscript variables for the DRAX manuscript."""
    parser = argparse.ArgumentParser(
        description="Generate manuscript variables for moonraker/DRAX"
    )
    parser.add_argument(
        "--allow-draft",
        action="store_true",
        help="Allow draft mode when output/data/mission_results.json is missing",
    )
    args = parser.parse_args()

    variables = generate_variables(_PROJECT_ROOT, require_analysis_outputs=not args.allow_draft)
    out_path = _PROJECT_ROOT / "output" / "data" / "manuscript_variables.json"
    save_variables(variables, out_path)
    write_resolved_manuscript_tree(_PROJECT_ROOT, variables)
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
