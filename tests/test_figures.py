"""Tests for moonraker.figures — deterministic figure rendering.

Two properties are bound here. First, each generator writes a real PNG. Second
— the one that matters for the manuscript's claim that the figures and the
prose tokens come from one computation — each generator's *content* follows the
mission parameters. Rendering the same figure twice under different parameters
must produce different bytes; a generator that had gone back to hard-coding its
own constants would emit identical files and fail.
"""

import ast
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pytest

from moonraker import figures
from moonraker.manuscript_variables import load_mission_config
from moonraker.mission_results import MISSION_DEFAULTS, compute_mission_results

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _assert_png(path: Path) -> None:
    assert path.is_file()
    with path.open("rb") as fh:
        assert fh.read(8) == b"\x89PNG\r\n\x1a\n"


def _render_bytes(render: Any, tmp_path: Path, name: str, params: dict[str, Any] | None) -> bytes:
    dest = tmp_path / name
    path = render(dest, params=params)
    _assert_png(path)
    return dest.read_bytes()


class TestFigureOutputDir:
    def test_creates_dir(self, tmp_path: Path) -> None:
        out = figures.figure_output_dir(tmp_path)
        assert out == tmp_path / "output" / "figures"
        assert out.is_dir()


class TestMissionParams:
    def test_defaults_come_from_the_config_file(self) -> None:
        """With no override, figures plot exactly what the token map plots."""
        assert figures.mission_params() == load_mission_config(PROJECT_ROOT)

    def test_explicit_params_fill_in_from_defaults(self) -> None:
        params = figures.mission_params({"station_altitude_km": 700.0})
        assert params["station_altitude_km"] == 700.0
        assert params["capacity_kg"] == MISSION_DEFAULTS["capacity_kg"]

    def test_project_root_holds_the_manuscript(self) -> None:
        assert (figures.project_root() / "manuscript" / "config.yaml").is_file()


class TestRenderTimeline:
    def test_renders_png(self, tmp_path: Path) -> None:
        dest = tmp_path / "timeline.png"
        path = figures.render_timeline_figure(dest)
        assert path == dest
        _assert_png(path)

    def test_tracks_the_deadline_parameter(self, tmp_path: Path) -> None:
        base = _render_bytes(figures.render_timeline_figure, tmp_path, "a.png", None)
        moved = _render_bytes(
            figures.render_timeline_figure, tmp_path, "b.png", {"deadline_min": 90.0}
        )
        assert base != moved

    def test_deadline_marker_sits_at_the_configured_deadline(self) -> None:
        """Read the drawn deadline line back off the axes, not off the config."""
        for deadline in (60.0, 90.0):
            fig = figures._build_timeline_figure({"deadline_min": deadline})
            try:
                marks = [line.get_xdata()[0] for line in fig.axes[0].lines]
            finally:
                plt.close(fig)
            assert marks == [deadline]

    def test_one_bar_per_hijack_phase(self) -> None:
        fig = figures._build_timeline_figure()
        try:
            drawn = len(fig.axes[0].patches)
        finally:
            plt.close(fig)
        assert drawn == compute_mission_results()["SHUTTLE_NUM_PHASES"]


class TestRenderOrbit:
    def test_renders_png(self, tmp_path: Path) -> None:
        dest = tmp_path / "orbit.png"
        path = figures.render_orbit_figure(dest)
        _assert_png(path)

    def test_tracks_the_station_altitude(self, tmp_path: Path) -> None:
        base = _render_bytes(figures.render_orbit_figure, tmp_path, "a.png", None)
        moved = _render_bytes(
            figures.render_orbit_figure, tmp_path, "b.png", {"station_altitude_km": 700.0}
        )
        assert base != moved

    @pytest.mark.parametrize(
        "overrides",
        [{}, {"station_altitude_km": 700.0}, {"launch_horizon_h": 8.0}],
    )
    def test_bars_drawn_equal_the_published_window_count(self, overrides: dict[str, Any]) -> None:
        """Count the bars the figure actually draws against ``ORBIT_WINDOW_COUNT``.

        The desync this replaces was real and shipped: the figure asked for
        eight windows while the token reported six, and nothing compared them.
        The assertion reads the built figure's own artists, so a generator that
        went back to requesting its own count would draw a different number of
        bars and fail here.
        """
        params = figures.mission_params(dict(overrides))
        fig = figures._build_orbit_figure(params)
        try:
            windows_axis = fig.axes[1]
            drawn = len(windows_axis.patches)
        finally:
            plt.close(fig)
        published = compute_mission_results(params)["ORBIT_WINDOW_COUNT"]
        assert drawn == published
        assert drawn > 0


class TestRenderCentrifuge:
    def test_renders_png(self, tmp_path: Path) -> None:
        dest = tmp_path / "centrifuge.png"
        path = figures.render_centrifuge_figure(dest)
        _assert_png(path)

    def test_tracks_the_configured_profile(self, tmp_path: Path) -> None:
        """A different target g must produce a different plot, not the same one."""
        base = _render_bytes(figures.render_centrifuge_figure, tmp_path, "a.png", None)
        moved = _render_bytes(
            figures.render_centrifuge_figure, tmp_path, "b.png", {"centrifuge_target_g": 4.0}
        )
        assert base != moved


class TestRenderHohmann:
    def test_renders_png(self, tmp_path: Path) -> None:
        dest = tmp_path / "hohmann.png"
        path = figures.render_hohmann_figure(dest)
        _assert_png(path)

    def test_tracks_the_parking_orbit(self, tmp_path: Path) -> None:
        base = _render_bytes(figures.render_hohmann_figure, tmp_path, "a.png", None)
        moved = _render_bytes(
            figures.render_hohmann_figure, tmp_path, "b.png", {"park_altitude_km": 120.0}
        )
        assert base != moved


class TestRenderTraining:
    def test_renders_png(self, tmp_path: Path) -> None:
        dest = tmp_path / "training.png"
        path = figures.render_training_figure(dest)
        _assert_png(path)

    def test_tracks_the_weekly_cap(self, tmp_path: Path) -> None:
        base = _render_bytes(figures.render_training_figure, tmp_path, "a.png", None)
        moved = _render_bytes(
            figures.render_training_figure,
            tmp_path,
            "b.png",
            {"training_weekly_cap_g_s": 800.0},
        )
        assert base != moved


class TestFiguresDeclareNoMissionConstants:
    """``figures.py`` must hold no mission parameter of its own.

    The shipped defect was exactly this: a module-level
    ``DRAX_STATION_ALTITUDE_KM = 350.0``, so editing ``config.yaml`` moved every
    prose token and no figure. Re-introducing any module-level numeric constant
    fails this test.
    """

    def test_module_defines_no_numeric_constant(self) -> None:
        """No module-level numeric assignment anywhere in ``figures.py``.

        Parsed from the source rather than from ``vars()``, so a re-exported
        physical constant such as ``EARTH_RADIUS_KM`` (imported, not authored
        here) does not count while a locally-declared parameter does.
        """
        tree = ast.parse(Path(figures.__file__).read_text(encoding="utf-8"))
        offenders = [
            target.id
            for node in tree.body
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
            for target in node.targets
            if isinstance(target, ast.Name) and isinstance(node.value.value, (int, float))
        ]
        assert not offenders, f"figures.py declares mission constants: {offenders}"

    def test_config_edit_moves_every_figure_that_should_see_it(self, tmp_path: Path) -> None:
        """One config value, three figures: all must move together.

        ``station_altitude_km`` is plotted by the orbit figure (period marker
        and windows) and the Hohmann figure (target orbit radius), and it
        changes the published tokens. If any of them had kept a private copy of
        350.0 it would render identical bytes here.
        """
        moved = {"station_altitude_km": 700.0}
        for render, name in (
            (figures.render_orbit_figure, "orbit"),
            (figures.render_hohmann_figure, "hohmann"),
        ):
            base = _render_bytes(render, tmp_path, f"{name}_base.png", None)
            after = _render_bytes(render, tmp_path, f"{name}_moved.png", moved)
            assert base != after, f"{name} figure ignored station_altitude_km"
        assert (
            compute_mission_results()["ORBIT_PERIOD_S"]
            != compute_mission_results(moved)["ORBIT_PERIOD_S"]
        )


@pytest.mark.parametrize(
    "render",
    [
        figures.render_timeline_figure,
        figures.render_orbit_figure,
        figures.render_centrifuge_figure,
        figures.render_hohmann_figure,
        figures.render_training_figure,
    ],
)
def test_rendering_is_byte_deterministic(render: Any, tmp_path: Path) -> None:
    first = _render_bytes(render, tmp_path, "first.png", None)
    second = _render_bytes(render, tmp_path, "second.png", None)
    assert first == second
