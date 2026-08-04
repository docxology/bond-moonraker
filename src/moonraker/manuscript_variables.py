"""Manuscript ``{{TOKEN}}`` hydration for the DRAX manuscript.

Reads ``manuscript/config.yaml`` (identity, keywords, the ``mission:``
parameter block) and combines it with the deterministic mission results from
:mod:`moonraker.mission_results` to produce the full ``{{TOKEN}}`` → value map
used by the manuscript sections. Numeric metrics are ALWAYS computed — never
hand-authored in prose — so the manuscript stays accurate when config changes.
"""

from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .mission_results import MISSION_DEFAULTS, compute_mission_results

__all__ = [
    "generate_variables",
    "save_variables",
    "load_mission_config",
    "write_resolved_manuscript_tree",
]


def load_mission_config(project_root: Path) -> dict[str, Any]:
    """Load the ``mission:`` parameter block from ``manuscript/config.yaml``.

    Falls back to :data:`MISSION_DEFAULTS` for any key the config omits, so the
    generator is robust to config edits.
    """
    config_path = Path(project_root) / "manuscript" / "config.yaml"
    with config_path.open("r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh) or {}
    mission = config.get("mission", {})
    return {**MISSION_DEFAULTS, **(mission if isinstance(mission, dict) else {})}


def generate_variables(
    project_root: Path,
    require_analysis_outputs: bool = False,
    now: datetime | None = None,
) -> dict[str, str]:
    """Return the full deterministic manuscript token map.

    Args:
        project_root: the package root (contains ``manuscript/`` and ``output/``).
        require_analysis_outputs: when True, raise ``FileNotFoundError`` if
            ``output/data/mission_results.json`` is absent (pipeline strict
            mode). Token values are still computed directly from the domain
            core, so the map is correct in either mode.
        now: optional timestamp override (deterministic tests); defaults to the
            current UTC time.

    Returns:
        A mapping of ``{{TOKEN}}`` names to string values.
    """
    project_root = Path(project_root)
    if require_analysis_outputs:
        results_file = project_root / "output" / "data" / "mission_results.json"
        if not results_file.is_file():
            msg = (
                "strict mode requires "
                + str(results_file)
                + "; run scripts/execute.py first (or pass --allow-draft)"
            )
            raise FileNotFoundError(msg)

    config_path = project_root / "manuscript" / "config.yaml"
    with config_path.open("r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh) or {}
    paper = config.get("paper", {}) if isinstance(config.get("paper"), dict) else {}
    authors = config.get("authors", []) if isinstance(config.get("authors"), list) else []
    keywords = config.get("keywords", []) if isinstance(config.get("keywords"), list) else []
    mission = load_mission_config(project_root)

    stamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M UTC")
    results = compute_mission_results(mission)

    variables: dict[str, str] = {
        "BOND_TITLE": str(paper.get("title", "Moonraker: DRAX")),
        "BOND_SUBTITLE": str(paper.get("subtitle", "Special-Agent Mission Software")),
        "BOND_VERSION": str(paper.get("version", "0.2.0")),
        "CONFIG_AUTHOR": str(authors[0].get("name", "Daniel Ari Friedman"))
        if authors
        else "Daniel Ari Friedman",
        "CONFIG_KEYWORDS": ", ".join(str(k) for k in keywords),
        "CONFIG_FILM": str(config.get("film", "Moonraker")),
        "CONFIG_CODENAME": str(config.get("codename", "DRAX")),
        "CONFIG_DEADLINE_MIN": str(mission["deadline_min"]),
        "CONFIG_STATION_ALTITUDE_KM": str(mission["station_altitude_km"]),
        "CONFIG_CREW": str(mission["crew"]),
        "CONFIG_CAPACITY_KG": str(mission["capacity_kg"]),
        "CONFIG_RATE_KG_PERSON_DAY": str(mission["rate_kg_per_person_day"]),
        "CONFIG_RESUPPLY_INTERVAL_DAYS": str(mission["resupply_interval_days"]),
        "CONFIG_TARGET_G": str(mission["centrifuge_target_g"]),
        "CONFIG_CENTRIFUGE_RADIUS_M": str(mission["centrifuge_radius_m"]),
        "CONFIG_SUSTAIN_S": str(mission["centrifuge_sustain_s"]),
        "GENERATION_TIMESTAMP": stamp,
        "PYTHON_VERSION": platform.python_version(),
        "PLATFORM": platform.system(),
    }
    variables.update({k: str(v) for k, v in results.items()})
    return variables


def save_variables(variables: dict[str, str], out_path: Path) -> Path:
    """Write the token map to a JSON file (byte-deterministic key order)."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(variables, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out_path


def write_resolved_manuscript_tree(project_root: Path, variables: dict[str, str]) -> Path:
    """Substitute every ``{{TOKEN}}`` in the numbered manuscript sections.

    Reads ``manuscript/[0-9]*.md`` and writes the resolved copies into
    ``output/manuscript/`` so rendering consumes substituted text (mirroring
    the exemplar pipeline without requiring infrastructure). Guide files
    (AGENTS.md, SYNTAX.md, README.md) are intentionally left untouched so their
    literal ``{{TOKEN}}`` examples cannot leak into the rendered prose.
    """
    project_root = Path(project_root)
    src_dir = project_root / "manuscript"
    out_dir = project_root / "output" / "manuscript"
    out_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(text: str) -> str:
        resolved = text
        for token, value in variables.items():
            resolved = resolved.replace("{{" + token + "}}", value)
        return resolved

    for section in sorted(src_dir.glob("[0-9]*.md")):
        out_file = out_dir / section.name
        out_file.write_text(_resolve(section.read_text(encoding="utf-8")), encoding="utf-8")
    return out_dir


def _environment_probe() -> str:
    """Surface Python/sys info for the generated environment token."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
