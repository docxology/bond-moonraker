"""Tests for moonraker.manuscript_variables — token hydration + live cross-ref."""

import json
import re
from pathlib import Path

import pytest
import yaml

from moonraker.manuscript_variables import (
    UNDATED,
    generate_variables,
    load_mission_config,
    save_variables,
    write_resolved_manuscript_tree,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_MANUSCRIPT = PROJECT_ROOT / "manuscript"


def _tokens_in(text: str) -> set[str]:
    return set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", text))


class TestGenerateVariables:
    def test_result_tokens_present(self) -> None:
        variables = generate_variables(PROJECT_ROOT)
        for key in (
            "SHUTTLE_TOTAL_MIN",
            "ORBIT_PERIOD_S",
            "CENTRIFUGE_PEAK_G",
            "BOND_TITLE",
            "CONFIG_CODENAME",
        ):
            assert key in variables

    def test_values_are_strings(self) -> None:
        variables = generate_variables(PROJECT_ROOT)
        assert all(isinstance(v, str) for v in variables.values())

    def test_deterministic_across_calls(self) -> None:
        """No injected clock: the map must be a pure function of the config.

        The predecessor of this test passed a fixed ``now`` into both calls,
        which made it structurally incapable of failing on the wall clock the
        module actually read. See ``tests/test_regeneration_determinism.py``.
        """
        v1 = generate_variables(PROJECT_ROOT)
        v2 = generate_variables(PROJECT_ROOT)
        assert v1 == v2

    def test_manuscript_date_is_the_committed_config_date(self) -> None:
        config = yaml.safe_load((_MANUSCRIPT / "config.yaml").read_text(encoding="utf-8"))
        variables = generate_variables(PROJECT_ROOT)
        assert variables["MANUSCRIPT_DATE"] == str(config["paper"]["date"])

    def test_manuscript_date_falls_back_when_config_omits_it(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "config.yaml").write_text("paper:\n  title: Moonraker\n", encoding="utf-8")
        assert generate_variables(tmp_path)["MANUSCRIPT_DATE"] == UNDATED


class TestLiveCrossReference:
    def test_all_manuscript_tokens_are_generated(self) -> None:
        """Every {{TOKEN}} used in numbered prose sections must exist in the map."""
        variables = generate_variables(PROJECT_ROOT)
        for section in sorted(_MANUSCRIPT.glob("[0-9]*.md")):
            used = _tokens_in(section.read_text(encoding="utf-8"))
            missing = used - set(variables)
            assert not missing, f"{section.name} uses missing tokens: {sorted(missing)}"


class TestStrictMode:
    def test_strict_requires_analysis_outputs(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "config.yaml").write_text("paper: {}\n", encoding="utf-8")
        with pytest.raises(FileNotFoundError):
            generate_variables(tmp_path, require_analysis_outputs=True)

    def test_draft_mode_works_without_outputs(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "config.yaml").write_text(
            yaml.safe_dump(
                {
                    "paper": {"title": "Moonraker"},
                    "authors": [{"name": "A"}],
                    "keywords": ["k"],
                    "mission": {"deadline_min": 60.0},
                }
            ),
            encoding="utf-8",
        )
        variables = generate_variables(tmp_path, require_analysis_outputs=False)
        assert variables["SHUTTLE_FEASIBLE"] == "yes"
        # Missing keys fall back to defaults.
        assert variables["CONFIG_STATION_ALTITUDE_KM"] == "350.0"


class TestSaveAndResolve:
    def test_save_variables(self, tmp_path: Path) -> None:
        out = save_variables({"A": "1", "B": "2"}, tmp_path / "data" / "vars.json")
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data == {"A": "1", "B": "2"}

    def test_write_resolved_tree(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "00_x.md").write_text("dur {{SHUTTLE_TOTAL_MIN}} ok\n", encoding="utf-8")
        out = write_resolved_manuscript_tree(tmp_path, {"SHUTTLE_TOTAL_MIN": "57.0"})
        resolved = (out / "00_x.md").read_text(encoding="utf-8")
        assert resolved == "dur 57.0 ok\n"

    def test_load_mission_config_defaults(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "config.yaml").write_text(
            "mission:\n  deadline_min: 99.0\n", encoding="utf-8"
        )
        cfg = load_mission_config(tmp_path)
        assert cfg["deadline_min"] == 99.0
        assert cfg["capacity_kg"] == 5400.0  # default fallback
