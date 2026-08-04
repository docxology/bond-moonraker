"""Tests for moonraker.figures — deterministic figure rendering."""

from pathlib import Path

from moonraker import figures


def _assert_png(path: Path) -> None:
    assert path.is_file()
    with path.open("rb") as fh:
        assert fh.read(8) == b"\x89PNG\r\n\x1a\n"


class TestFigureOutputDir:
    def test_creates_dir(self, tmp_path: Path) -> None:
        out = figures.figure_output_dir(tmp_path)
        assert out == tmp_path / "output" / "figures"
        assert out.is_dir()


class TestRenderTimeline:
    def test_renders_png(self, tmp_path: Path) -> None:
        dest = tmp_path / "timeline.png"
        path = figures.render_timeline_figure(dest)
        assert path == dest
        _assert_png(path)


class TestRenderOrbit:
    def test_renders_png(self, tmp_path: Path) -> None:
        dest = tmp_path / "orbit.png"
        path = figures.render_orbit_figure(dest)
        _assert_png(path)


class TestRenderCentrifuge:
    def test_renders_png(self, tmp_path: Path) -> None:
        dest = tmp_path / "centrifuge.png"
        path = figures.render_centrifuge_figure(dest)
        _assert_png(path)

    def test_profile_plotted(self) -> None:
        from moonraker.centrifuge import TrainingProfile, build_training_profile

        p = build_training_profile(target_g=6.0, radius_m=8.0, sustain_s=12.0)
        assert isinstance(p, TrainingProfile)
