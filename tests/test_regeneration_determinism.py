"""End-to-end binding for the byte-identical re-run claim.

`manuscript/06_reproducibility.md`, `AGENTS.md`, `scripts/CONVENTIONS.md` and
`docs/testing_philosophy.md` all state that regenerating `output/` restores a
byte-identical tree. Until now the only test guarding that was
``test_deterministic_with_fixed_now``, which called ``generate_variables`` twice
with the *same injected* ``now``. That test can never fail on a wall clock: it
removes the wall clock as a precondition of running. Meanwhile the abstract
carried ``{{GENERATION_TIMESTAMP}}``, hydrated from ``datetime.now(timezone.utc)``
at minute resolution, so two real regenerations one minute apart produced
different bytes and the documented guarantee was false.

Two independent checks replace it, neither of which may inject a clock:

``TestRegenerationIsByteIdentical``
    Behavioural. Runs the real ``run_mission.py`` + ``z_generate_manuscript_variables.py``
    pair twice into an isolated tree and SHA-256-compares **every** regenerated
    file. Catches any nondeterminism whose period is shorter than the gap
    between the two runs — sub-second clocks, dict/set iteration order, unsorted
    globs, uninitialised floats.

``TestNoWallClockInPersistedPath``
    Structural, and the one with teeth against a *coarse* clock: a
    minute-resolution or date-resolution timestamp is invisible to any pair of
    runs executed inside the same minute, so behaviour alone cannot bind the
    claim without a 60-second sleep. This check parses every module that feeds
    ``output/`` and fails on any wall-clock call at all. Its positive control
    proves the parser is not vacuous.
"""

import ast
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

#: Callables that read the wall clock. Matched against the final component of a
#: call's dotted name (``datetime.now``, ``datetime.datetime.utcnow``, ...) plus
#: the fully-qualified ``time.time``, which is the one whose bare last component
#: (``time``) collides with the innocuous ``datetime.time()`` accessor.
WALL_CLOCK_ATTRS = frozenset(
    {
        "now",
        "utcnow",
        "today",
        "time_ns",
        "monotonic",
        "monotonic_ns",
        "perf_counter",
        "perf_counter_ns",
        "fromtimestamp",
        "utcfromtimestamp",
        "gmtime",
        "localtime",
    }
)
WALL_CLOCK_DOTTED = frozenset({"time.time"})


def _dotted_name(node: ast.expr) -> str:
    """Return the dotted source spelling of a call target, or ``""``."""
    parts: list[str] = []
    current: ast.expr = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    else:
        return ""
    return ".".join(reversed(parts))


def wall_clock_calls(source: str, label: str) -> list[str]:
    """Return ``label:lineno dotted.name`` for every wall-clock call in ``source``."""
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        dotted = _dotted_name(node.func)
        if not dotted:
            continue
        if dotted in WALL_CLOCK_DOTTED or dotted.rsplit(".", 1)[-1] in WALL_CLOCK_ATTRS:
            found.append(f"{label}:{node.lineno} {dotted}()")
    return found


def _persisted_path_modules() -> list[Path]:
    """Every module that can put bytes under ``output/``."""
    return sorted((PROJECT_ROOT / "src" / "moonraker").glob("*.py")) + sorted(
        (PROJECT_ROOT / "scripts").glob("*.py")
    )


def _isolated_tree(tmp_path: Path) -> Path:
    """Copy scripts/src/manuscript into a tree with no ``output/`` of its own."""
    root = tmp_path / "package"
    for name in ("scripts", "src", "manuscript"):
        shutil.copytree(PROJECT_ROOT / name, root / name)
    assert not (root / "output").exists()
    return root


def _regenerate(root: Path) -> None:
    for script in ("run_mission.py", "z_generate_manuscript_variables.py"):
        result = subprocess.run(
            [sys.executable, str(root / "scripts" / script)],
            capture_output=True,
            text=True,
            cwd=str(root),
            check=False,
        )
        assert result.returncode == 0, f"{script} failed: {result.stderr}"


def _tree_digests(output_dir: Path) -> dict[str, str]:
    """SHA-256 of every file under ``output/``, keyed by relative path."""
    digests: dict[str, str] = {}
    for path in sorted(output_dir.rglob("*")):
        if path.is_file():
            rel = str(path.relative_to(output_dir))
            digests[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


class TestRegenerationIsByteIdentical:
    def test_two_full_regenerations_agree_on_every_file(self, tmp_path: Path) -> None:
        """Run the whole artifact pipeline twice; every output byte must match."""
        root = _isolated_tree(tmp_path)

        _regenerate(root)
        first = _tree_digests(root / "output")
        assert first, "first regeneration produced no files"
        # The manuscript, the token map, the results JSON and all five figures.
        assert len(first) >= 15, f"unexpectedly small output tree: {sorted(first)}"

        _regenerate(root)
        second = _tree_digests(root / "output")

        assert sorted(second) == sorted(first), "re-run changed the set of output files"
        differing = sorted(k for k in first if first[k] != second[k])
        assert not differing, f"re-run produced different bytes for: {differing}"

    def test_manuscript_date_comes_from_config_not_the_clock(self, tmp_path: Path) -> None:
        """The persisted date token must equal the committed ``paper.date`` exactly.

        Exact equality, not a substring: a clock-derived
        ``"2026-08-05 20:43 UTC"`` still *contains* today's ``paper.date``, so a
        containment assertion would pass against the very defect this guards.
        """
        import json

        import yaml

        root = _isolated_tree(tmp_path)
        _regenerate(root)
        config = yaml.safe_load((root / "manuscript" / "config.yaml").read_text(encoding="utf-8"))
        expected = str(config["paper"]["date"])
        persisted = json.loads(
            (root / "output" / "data" / "manuscript_variables.json").read_text(encoding="utf-8")
        )
        assert persisted["MANUSCRIPT_DATE"] == expected
        abstract = (root / "output" / "manuscript" / "00_abstract.md").read_text(encoding="utf-8")
        assert f"Manuscript dated {expected}," in abstract


class TestNoWallClockInPersistedPath:
    def test_scan_set_is_not_empty(self) -> None:
        """A gate over an empty file set would pass vacuously."""
        modules = _persisted_path_modules()
        assert len(modules) >= 10, f"expected the real module set, got {modules}"

    def test_detector_flags_a_wall_clock_when_one_is_present(self) -> None:
        """Positive control: the parser must detect the exact defect it guards."""
        planted = (
            "from datetime import datetime, timezone\n"
            "import time\n"
            "def f():\n"
            "    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')\n"
            "    return stamp, time.time()\n"
        )
        hits = wall_clock_calls(planted, "planted")
        assert any("datetime.now" in h for h in hits), hits
        assert any("time.time" in h for h in hits), hits

    def test_detector_does_not_flag_the_datetime_time_accessor(self) -> None:
        """Negative control: ``dt.time()`` extracts a time-of-day, it is not a clock."""
        benign = "def f(dt):\n    return dt.time(), dt.date()\n"
        assert wall_clock_calls(benign, "benign") == []

    def test_no_module_that_writes_output_reads_the_clock(self) -> None:
        """The claim's real binding: nothing on the persisted path samples time."""
        offenders: list[str] = []
        for module in _persisted_path_modules():
            offenders.extend(
                wall_clock_calls(
                    module.read_text(encoding="utf-8"),
                    str(module.relative_to(PROJECT_ROOT)),
                )
            )
        assert not offenders, (
            "wall-clock call on the path that writes output/ — this breaks the "
            "byte-identical re-run claim in manuscript/06_reproducibility.md: "
            f"{offenders}"
        )
