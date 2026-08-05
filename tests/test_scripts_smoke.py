"""Subprocess smoke tests for the DRAX scripts (thin CLIs)."""

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _run(*args: str, cwd: Path = PROJECT_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(cwd / "scripts" / args[0]), *args[1:]],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        check=False,
    )


def _isolated_tree(tmp_path: Path) -> Path:
    """Copy the scripts, sources and manuscript into a tree with **no** output/.

    The draft-mode assertion is only meaningful where the analysis outputs are
    genuinely absent. Run against the package root they are always present —
    the flagship runner writes them — so the test would pass whether or not
    ``--allow-draft`` did anything. It also keeps the package's real ``output/``
    tree out of the test's blast radius.
    """
    root = tmp_path / "package"
    for name in ("scripts", "src", "manuscript"):
        shutil.copytree(PROJECT_ROOT / name, root / name)
    assert not (root / "output").exists()
    return root


class TestPhaseScripts:
    def test_brief(self) -> None:
        result = _run("brief.py")
        assert result.returncode == 0
        assert "codename: DRAX" in result.stdout

    def test_recon(self) -> None:
        result = _run("recon.py")
        assert result.returncode == 0
        assert "recon goal:" in result.stdout

    def test_plan(self) -> None:
        result = _run("plan.py")
        assert result.returncode == 0
        assert "shuttle_timeline" in result.stdout

    def test_execute(self) -> None:
        result = _run("execute.py")
        assert result.returncode == 0
        assert "DRAX mission results" in result.stdout

    def test_debrief(self) -> None:
        result = _run("debrief.py")
        assert result.returncode == 0
        assert "lessons:" in result.stdout


class TestRunMission:
    def test_returns_zero_and_writes_artifacts(self) -> None:
        result = _run("run_mission.py")
        assert result.returncode == 0
        data_file = PROJECT_ROOT / "output" / "data" / "mission_results.json"
        assert data_file.is_file()
        assert (PROJECT_ROOT / "output" / "figures" / "timeline_critical_path.png").is_file()


class TestManifestGeneration:
    def test_z_generate_strict_after_run(self) -> None:
        # Ensure results file exists (run_mission produces it).
        if not (PROJECT_ROOT / "output" / "data" / "mission_results.json").is_file():
            _run("run_mission.py")
        result = _run("z_generate_manuscript_variables.py")
        assert result.returncode == 0
        assert (PROJECT_ROOT / "output" / "data" / "manuscript_variables.json").is_file()
        assert (PROJECT_ROOT / "output" / "manuscript" / "00_abstract.md").is_file()

    def test_strict_mode_refuses_when_outputs_are_genuinely_absent(self, tmp_path: Path) -> None:
        """Without ``--allow-draft`` and without outputs, the CLI must fail.

        This is the negative control for the draft-mode test below: it proves
        the isolated tree really is missing ``output/data/mission_results.json``,
        so the next test's exit code is attributable to the flag.
        """
        root = _isolated_tree(tmp_path)
        result = _run("z_generate_manuscript_variables.py", cwd=root)
        assert result.returncode != 0
        assert "strict mode requires" in (result.stderr + result.stdout)

    def test_z_generate_allow_draft_without_outputs(self, tmp_path: Path) -> None:
        """``--allow-draft`` succeeds in the same tree the strict run refuses."""
        root = _isolated_tree(tmp_path)
        result = _run("z_generate_manuscript_variables.py", "--allow-draft", cwd=root)
        assert result.returncode == 0, result.stderr
        assert (root / "output" / "data" / "manuscript_variables.json").is_file()
        assert not (root / "output" / "data" / "mission_results.json").exists()
