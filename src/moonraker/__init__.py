"""moonraker — DRAX special-agent mission software (film: Moonraker, 1979).

The package models three concepts from the DRAX mission:

* :mod:`moonraker.shuttle_ops` — a space-shuttle hijack as a critical-path
  timeline (CPM) with feasibility against a hard deadline.
* :mod:`moonraker.orbital_logistics` — Drax's space-station orbital logistics:
  Kepler orbit physics, ground launch windows, and consumables capacity.
* :mod:`moonraker.centrifuge` — centrifuge g-force training profiles with a
  physiological tolerance envelope and safety checks.

These three modules are the pure domain core: they are infrastructure-free
(no ``bond_api``, no ``infrastructure``) and deterministic, so they can be
imported and tested in isolation. The BOND-API mission adapter lives in
:mod:`moonraker.mission` and is imported separately so the core stays
importable without the protocol.
"""

from __future__ import annotations

from .centrifuge import (
    G0_MS2,
    TrainingProfile,
    build_training_profile,
    g_from_rpm,
    max_sustained_duration,
    profile_is_safe,
    rpm_for_g,
)
from .orbital_logistics import (
    EARTH_MU_KM3_S2,
    EARTH_RADIUS_KM,
    SIDEREAL_DAY_S,
    LaunchWindow,
    circular_speed,
    consumables_days,
    depletion_day,
    launch_windows,
    orbital_period,
    orbits_per_day,
    pass_duration,
    resupply_interval,
    sustainable_crew,
    visibility_half_angle,
)
from .shuttle_ops import (
    DRAX_HIJACK_TIMELINE,
    TimelineActivity,
    TimelineSchedule,
    compute_timeline,
    timeline_feasibility,
)

__all__ = [
    "G0_MS2",
    "EARTH_MU_KM3_S2",
    "EARTH_RADIUS_KM",
    "SIDEREAL_DAY_S",
    "DRAX_HIJACK_TIMELINE",
    "TrainingProfile",
    "LaunchWindow",
    "TimelineActivity",
    "TimelineSchedule",
    "build_training_profile",
    "circular_speed",
    "compute_timeline",
    "consumables_days",
    "depletion_day",
    "g_from_rpm",
    "launch_windows",
    "max_sustained_duration",
    "orbital_period",
    "orbits_per_day",
    "pass_duration",
    "profile_is_safe",
    "resupply_interval",
    "rpm_for_g",
    "sustainable_crew",
    "timeline_feasibility",
    "visibility_half_angle",
]
