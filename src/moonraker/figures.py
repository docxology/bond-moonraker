"""Publication-figure generators for the DRAX mission.

Three deterministic matplotlib figures, one per concept:

* :func:`render_timeline_figure` — the shuttle-hijack critical path as a Gantt
  layout, shading the activities on the critical path.
* :func:`render_orbit_figure` — orbital period versus altitude, annotated with
  the DRAX station's launch windows.
* :func:`render_centrifuge_figure` — the g-level training profile over time
  with the tolerance envelope overlaid.

Each generator writes to ``output/figures/`` under the project root and
returns the absolute path written. All are deterministic (fixed inputs, no
RNG) and use the headless ``Agg`` backend.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt  # noqa: E402

from .centrifuge import max_sustained_duration  # noqa: E402
from .orbital_logistics import launch_windows, orbital_period  # noqa: E402
from .shuttle_ops import DRAX_HIJACK_TIMELINE, compute_timeline  # noqa: E402

__all__ = [
    "DRAX_STATION_ALTITUDE_KM",
    "figure_output_dir",
    "render_centrifuge_figure",
    "render_orbit_figure",
    "render_timeline_figure",
]

#: The DRAX station's operational altitude (km) used across the figures.
DRAX_STATION_ALTITUDE_KM = 350.0


def figure_output_dir(project_root: Path | None = None) -> Path:
    """Return (creating if needed) the figures output directory."""
    root = project_root or Path(__file__).resolve().parents[2]
    out = root / "output" / "figures"
    out.mkdir(parents=True, exist_ok=True)
    return out


def render_timeline_figure(dest: Path | None = None) -> Path:
    """Render the hijack critical-path Gantt chart to PNG."""
    schedule = compute_timeline(DRAX_HIJACK_TIMELINE)
    path = dest or (figure_output_dir() / "timeline_critical_path.png")

    fig, ax = plt.subplots(figsize=(9, 5))
    names = list(schedule.earliest_start)
    for i, name in enumerate(names):
        start = schedule.earliest_start[name]
        dur = schedule.earliest_finish[name] - start
        color = "#D55E00" if name in schedule.critical_path else "#0072B2"
        ax.barh(i, dur, left=start, color=color, edgecolor="black", linewidth=0.6)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Minutes from launch")
    ax.set_title(f"Shuttle Hijack Critical Path — total {schedule.total_duration_min:.0f} min")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return Path(path)


def render_orbit_figure(dest: Path | None = None) -> Path:
    """Render orbital period vs altitude with the DRAX station highlighted."""
    path = dest or (figure_output_dir() / "orbit_period_windows.png")

    altitudes = [float(a) for a in range(300, 1601, 100)]
    periods = [orbital_period(a) / 60.0 for a in altitudes]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    ax1.plot(altitudes, periods, color="#0072B2", linewidth=2.5, marker="o", markersize=4)
    ax1.axvline(DRAX_STATION_ALTITUDE_KM, color="#D55E00", linestyle="--", linewidth=1.5)
    ax1.set_xlabel("Altitude (km)")
    ax1.set_ylabel("Orbital period (min)")
    ax1.set_title("Kepler period vs altitude")

    windows = launch_windows(DRAX_STATION_ALTITUDE_KM, num_windows=8)
    opens = [w.open_s / 60.0 for w in windows]
    closes = [w.close_s / 60.0 for w in windows]
    width = [c - o for o, c in zip(opens, closes, strict=True)]
    ax2.bar(list(range(len(windows))), width, color="#009E73", edgecolor="black", linewidth=0.6)
    ax2.set_xlabel("Launch window index")
    ax2.set_ylabel("Window duration (min)")
    ax2.set_title("DRAX station ground launch windows")

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return Path(path)


def render_centrifuge_figure(dest: Path | None = None) -> Path:
    """Render the g-force training profile with tolerance envelope."""
    from .centrifuge import build_training_profile

    profile = build_training_profile(
        target_g=6.0,
        radius_m=8.0,
        sustain_s=12.0,
        ramp_rate_g_per_s=0.5,
        decay_rate_g_per_s=1.0,
    )
    path = dest or (figure_output_dir() / "centrifuge_g_profile.png")

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(profile.time_s, profile.g_levels, color="#0072B2", linewidth=2.5, label="g-level")

    # Tolerance envelope: maximum sustainable duration at each g.
    g_points = [g / 10.0 for g in range(10, 100, 5)]
    tol = [max_sustained_duration(g) for g in g_points]
    ax2 = ax.twinx()
    ax2.plot(g_points, tol, color="#D55E00", linestyle="--", linewidth=1.8, label="tolerance (s)")
    ax2.set_ylabel("Max sustained duration (s)", color="#D55E00")

    ax.axhline(profile.peak_g, color="#999999", linestyle=":", linewidth=1.2)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("G-level")
    ax.set_title(f"Centrifuge training profile — peak {profile.peak_g:.1f} g")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return Path(path)
