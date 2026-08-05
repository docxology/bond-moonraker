"""Publication-figure generators for the DRAX mission.

Five deterministic matplotlib figures:

* :func:`render_timeline_figure` — the hijack schedule as a Gantt layout,
  shading the zero-slack (critical) activities and marking the deadline.
* :func:`render_orbit_figure` — orbital period versus altitude, annotated with
  the DRAX station's usable launch windows inside the planning horizon.
* :func:`render_centrifuge_figure` — the g-level training profile over time
  with the tolerance envelope and the governing allowance overlaid.
* :func:`render_hohmann_figure` — the resupply transfer geometry: parking
  orbit, station orbit and the transfer ellipse.
* :func:`render_training_figure` — the weekly training exposure against the
  g·s caps.

**Every number these figures plot comes from
:mod:`moonraker.mission_results`.** No figure re-declares a mission parameter
and none recomputes a published metric: each generator resolves its parameters
through :func:`mission_params` — which reads ``manuscript/config.yaml`` →
``mission:`` via :func:`moonraker.manuscript_variables.load_mission_config`,
the same reader the token map uses — and then calls the canonical factories.
Editing ``config.yaml`` therefore moves the prose tokens and the figures
together; a figure and its ``{{TOKEN}}`` cannot disagree.

Each generator writes to ``output/figures/`` under the project root and
returns the absolute path written. All are deterministic (fixed inputs, no
RNG) and use the headless ``Agg`` backend.
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Circle  # noqa: E402

from .centrifuge import max_sustained_duration  # noqa: E402
from .manuscript_variables import load_mission_config  # noqa: E402
from .mission_results import (  # noqa: E402
    MISSION_DEFAULTS,
    compute_centrifuge,
    compute_orbit,
    compute_schedule,
    compute_training,
    compute_transfer,
)
from .orbital_logistics import EARTH_RADIUS_KM  # noqa: E402

__all__ = [
    "figure_output_dir",
    "mission_params",
    "project_root",
    "render_centrifuge_figure",
    "render_hohmann_figure",
    "render_orbit_figure",
    "render_timeline_figure",
    "render_training_figure",
]


def project_root() -> Path:
    """Return the package root (the directory holding ``manuscript/``)."""
    return Path(__file__).resolve().parents[2]


def mission_params(
    params: dict[str, Any] | None = None, root: Path | None = None
) -> dict[str, Any]:
    """Return the mission parameter set a figure should plot.

    With no argument the parameters are read from ``manuscript/config.yaml`` —
    the single source of truth shared with the manuscript token map — falling
    back to :data:`~moonraker.mission_results.MISSION_DEFAULTS` for keys the
    config omits. An explicit ``params`` dict (used by tests and by callers
    varying a scenario) is merged over the defaults the same way.
    """
    if params is not None:
        return {**MISSION_DEFAULTS, **params}
    return load_mission_config(root or project_root())


def figure_output_dir(root: Path | None = None) -> Path:
    """Return (creating if needed) the figures output directory."""
    out = (root or project_root()) / "output" / "figures"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _build_timeline_figure(params: dict[str, Any] | None = None) -> Figure:
    """Render the hijack schedule Gantt chart to PNG."""
    p = mission_params(params)
    timeline = compute_schedule(p)
    schedule = timeline["schedule"]

    fig, ax = plt.subplots(figsize=(9, 5))
    names = list(schedule.earliest_start)
    for i, name in enumerate(names):
        start = schedule.earliest_start[name]
        dur = schedule.earliest_finish[name] - start
        color = "#D55E00" if name in schedule.critical_activities else "#0072B2"
        ax.barh(i, dur, left=start, color=color, edgecolor="black", linewidth=0.6)
    ax.axvline(
        float(p["deadline_min"]),
        color="#000000",
        linestyle="--",
        linewidth=1.4,
        label=f"point of no return ({p['deadline_min']} min)",
    )
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Minutes from launch")
    ax.set_title(
        f"Shuttle hijack schedule — total {timeline['total_duration_min']:.0f} min, "
        f"{len(timeline['critical_chains'])} critical paths"
    )
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def _build_orbit_figure(params: dict[str, Any] | None = None) -> Figure:
    """Render orbital period vs altitude with the DRAX station highlighted."""
    p = mission_params(params)
    orbit = compute_orbit(p)

    station_altitude = orbit["altitude_km"]
    sweep_start = max(100.0, station_altitude - 50.0)
    altitudes = [sweep_start + 100.0 * i for i in range(14)]
    periods = [
        compute_orbit({**p, "station_altitude_km": a})["period_s"] / 60.0 for a in altitudes
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    ax1.plot(altitudes, periods, color="#0072B2", linewidth=2.5, marker="o", markersize=4)
    ax1.axvline(station_altitude, color="#D55E00", linestyle="--", linewidth=1.5)
    ax1.set_xlabel("Altitude (km)")
    ax1.set_ylabel("Orbital period (min)")
    ax1.set_title("Kepler period vs altitude")

    windows = orbit["windows"]
    opens = [w.open_s / 60.0 for w in windows]
    closes = [w.close_s / 60.0 for w in windows]
    width = [c - o for o, c in zip(opens, closes, strict=True)]
    ax2.bar(list(range(len(windows))), width, color="#009E73", edgecolor="black", linewidth=0.6)
    ax2.set_xlabel("Launch window index")
    ax2.set_ylabel("Window duration (min)")
    ax2.set_title(f"{len(windows)} usable launch windows in a {orbit['horizon_h']:g} h horizon")

    fig.tight_layout()
    return fig


def _build_centrifuge_figure(params: dict[str, Any] | None = None) -> Figure:
    """Render the g-force training profile with tolerance envelope."""
    p = mission_params(params)
    centrifuge = compute_centrifuge(p)
    profile = centrifuge["profile"]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(profile.time_s, profile.g_levels, color="#0072B2", linewidth=2.5, label="g-level")

    # Tolerance envelope: maximum sustainable duration at each g.
    g_points = [g / 10.0 for g in range(10, 100, 5)]
    tol = [max_sustained_duration(g) for g in g_points]
    ax2 = ax.twinx()
    ax2.plot(g_points, tol, color="#D55E00", linestyle="--", linewidth=1.8, label="tolerance (s)")
    ax2.axhline(
        centrifuge["allowable_s"],
        color="#009E73",
        linestyle=":",
        linewidth=1.5,
        label="governing allowance",
    )
    ax2.set_ylabel("Max sustained duration (s)", color="#D55E00")

    ax.axhline(profile.peak_g, color="#999999", linestyle=":", linewidth=1.2)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("G-level")
    ax.set_title(
        f"Centrifuge training profile — peak {profile.peak_g:.1f} g, "
        f"allowance {centrifuge['allowable_s']:.1f} s"
    )
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def _build_hohmann_figure(params: dict[str, Any] | None = None) -> Figure:
    """Render the Hohmann transfer geometry (two circular orbits + ellipse)."""
    p = mission_params(params)
    transfer = compute_transfer(p)

    park = transfer["park_radius_km"]
    station = transfer["station_radius_km"]
    eccentricity = (station - park) / (station + park)

    fig, ax = plt.subplots(figsize=(6.2, 6.2))
    earth = Circle((0, 0), EARTH_RADIUS_KM, color="#999999", alpha=0.35)
    ax.add_patch(earth)
    for radius, color in (
        (park, "#0072B2"),
        (station, "#009E73"),
    ):
        circle = Circle((0, 0), radius, fill=False, color=color, linewidth=1.5)
        ax.add_patch(circle)

    # Transfer ellipse in polar form: r(theta) = a(1-e^2) / (1 + e cos theta).
    semi_major = transfer["semi_major_km"]
    theta = [t / 1000.0 * math.pi for t in range(0, 1001)]
    radii = [
        semi_major * (1 - eccentricity * eccentricity) / (1 + eccentricity * math.cos(t))
        for t in theta
    ]
    xs = [r * math.cos(t) for r, t in zip(radii, theta, strict=True)]
    ys = [r * math.sin(t) for r, t in zip(radii, theta, strict=True)]
    ax.plot(
        xs,
        ys,
        color="#D55E00",
        linewidth=2.2,
        label=f"transfer Δv {transfer['total_dv_km_s']:.3f} km/s",
    )

    ax.set_aspect("equal")
    ax.set_xlim(-station * 1.15, station * 1.15)
    ax.set_ylim(-station * 1.15, station * 1.15)
    ax.set_xlabel("Radial distance (km)")
    ax.set_ylabel("Radial distance (km)")
    ax.set_title("Hohmann resupply transfer to the DRAX station")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def _build_training_figure(params: dict[str, Any] | None = None) -> Figure:
    """Render the weekly training exposure against the g·s caps."""
    p = mission_params(params)
    training = compute_training(p)

    per_session = training["per_session_g_s"]
    weekly_cap = training["weekly_cap_g_s"]
    counts = list(range(1, 7))
    exposures = [per_session * c for c in counts]

    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.bar(counts, exposures, color="#0072B2", edgecolor="black", linewidth=0.6)
    ax.axhline(
        weekly_cap,
        color="#D55E00",
        linestyle="--",
        linewidth=1.8,
        label=f"weekly cap ({weekly_cap:g} g·s)",
    )
    ax.axvline(training["recommended"], color="#009E73", linestyle=":", linewidth=1.5)
    for i, value in zip(counts, exposures, strict=True):
        ax.text(i, value + 6, f"{value:.0f}", ha="center", fontsize=8)
    ax.set_xticks(counts)
    ax.set_xlabel("Sessions per week")
    ax.set_ylabel("Weekly +Gz exposure (g·s)")
    ax.set_title(f"Centrifuge training load — {per_session:.1f} g·s per session")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def _save(fig: Figure, dest: Path | None, filename: str) -> Path:
    """Write a built figure to ``dest`` (or the default output path) and close it."""
    path = Path(dest or (figure_output_dir() / filename))
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def render_timeline_figure(dest: Path | None = None, params: dict[str, Any] | None = None) -> Path:
    """Render the hijack schedule Gantt chart to PNG."""
    return _save(_build_timeline_figure(params), dest, "timeline_critical_path.png")


def render_orbit_figure(dest: Path | None = None, params: dict[str, Any] | None = None) -> Path:
    """Render orbital period vs altitude with the DRAX station highlighted."""
    return _save(_build_orbit_figure(params), dest, "orbit_period_windows.png")


def render_centrifuge_figure(
    dest: Path | None = None, params: dict[str, Any] | None = None
) -> Path:
    """Render the g-force training profile with tolerance envelope."""
    return _save(_build_centrifuge_figure(params), dest, "centrifuge_g_profile.png")


def render_hohmann_figure(dest: Path | None = None, params: dict[str, Any] | None = None) -> Path:
    """Render the Hohmann transfer geometry (two circular orbits + ellipse)."""
    return _save(_build_hohmann_figure(params), dest, "hohmann_transfer.png")


def render_training_figure(dest: Path | None = None, params: dict[str, Any] | None = None) -> Path:
    """Render the weekly training exposure against the g\u00b7s caps."""
    return _save(_build_training_figure(params), dest, "training_weekly_load.png")
