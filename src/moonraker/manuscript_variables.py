"""Manuscript ``{{TOKEN}}`` hydration for the DRAX manuscript.

Reads ``manuscript/config.yaml`` (identity, keywords, the ``mission:``
parameter block) and combines it with the deterministic mission results from
:mod:`moonraker.mission_results` to produce the full ``{{TOKEN}}`` → value map
used by the manuscript sections. Numeric metrics are ALWAYS computed — never
hand-authored in prose — so the manuscript stays accurate when config changes.

No wall clock is read anywhere in this module. The manuscript's date token is
``MANUSCRIPT_DATE``, sourced from the committed ``paper.date`` field of
``manuscript/config.yaml``, so regenerating the token map and the resolved
manuscript tree yields byte-identical files no matter when the generator runs.
``tests/test_regeneration_determinism.py`` binds that property.
"""

from __future__ import annotations

import json
import platform
from pathlib import Path
from typing import Any

import yaml

from .mission_results import MISSION_DEFAULTS, compute_mission_results

__all__ = [
    "UNDATED",
    "generate_variables",
    "save_variables",
    "load_mission_config",
    "write_resolved_manuscript_tree",
]

#: Value of ``MANUSCRIPT_DATE`` when ``manuscript/config.yaml`` omits ``paper.date``.
#: A literal placeholder rather than "today", so an undated config still
#: regenerates byte-identically.
UNDATED = "undated"


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
) -> dict[str, str]:
    """Return the full deterministic manuscript token map.

    The map is a pure function of ``manuscript/config.yaml`` and the running
    interpreter's identity. There is deliberately **no** ``now`` parameter and
    no wall-clock read: a date that varied per run would make the regenerated
    ``output/`` tree differ from the previous one, breaking the byte-identical
    re-run guarantee stated in ``manuscript/06_reproducibility.md``.

    Args:
        project_root: the package root (contains ``manuscript/`` and ``output/``).
        require_analysis_outputs: when True, raise ``FileNotFoundError`` if
            ``output/data/mission_results.json`` is absent (pipeline strict
            mode). Token values are still computed directly from the domain
            core, so the map is correct in either mode.

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

    manuscript_date = str(paper.get("date", UNDATED)) or UNDATED
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
        "CONFIG_LAUNCH_HORIZON_H": str(mission["launch_horizon_h"]),
        "CONFIG_PARK_ALTITUDE_KM": str(mission["park_altitude_km"]),
        "CONFIG_TRANSFER_ISP_S": str(mission["transfer_isp_s"]),
        "CONFIG_TRANSFER_DRY_MASS_KG": str(mission["transfer_dry_mass_kg"]),
        "CONFIG_DEORBIT_PERIGEE_KM": str(mission["deorbit_perigee_km"]),
        "CONFIG_RENDEZVOUS_INTERCEPT_S": str(mission["rendezvous_intercept_s"]),
        "CONFIG_CRASH_DEADLINE_MIN": str(mission["crash_deadline_min"]),
        "CONFIG_G_LIMIT": str(mission["g_limit"]),
        "CONFIG_DURATION_LIMIT_S": str(mission["duration_limit_s"]),
        "CONFIG_MARGIN_PCT": str(round(float(mission["centrifuge_margin_fraction"]) * 100.0, 1)),
        "CONFIG_RAMP_RATE_G_PER_S": str(mission["ramp_rate_g_per_s"]),
        "CONFIG_DECAY_RATE_G_PER_S": str(mission["decay_rate_g_per_s"]),
        "CONFIG_CREW": str(mission["crew"]),
        "CONFIG_CAPACITY_KG": str(mission["capacity_kg"]),
        "CONFIG_RATE_KG_PERSON_DAY": str(mission["rate_kg_per_person_day"]),
        "CONFIG_RESUPPLY_INTERVAL_DAYS": str(mission["resupply_interval_days"]),
        "CONFIG_TARGET_G": str(mission["centrifuge_target_g"]),
        "CONFIG_CENTRIFUGE_RADIUS_M": str(mission["centrifuge_radius_m"]),
        "CONFIG_SUSTAIN_S": str(mission["centrifuge_sustain_s"]),
        "CONFIG_TRAINING_DAILY_CAP_GS": str(mission["training_daily_cap_g_s"]),
        "CONFIG_TRAINING_WEEKLY_CAP_GS": str(mission["training_weekly_cap_g_s"]),
        "CONFIG_TRAINING_SESSIONS": str(mission["training_sessions_per_week"]),
        "MANUSCRIPT_DATE": manuscript_date,
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
