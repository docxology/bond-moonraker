"""moonraker — DRAX special-agent mission software (film: Moonraker, 1979).

Seven pure-domain modules model the three DRAX concept areas.

*The shuttle hijack*

* :mod:`moonraker.shuttle_ops` — the hijack as a critical-path (CPM) activity
  network with feasibility against the shuttle's point of no return.
* :mod:`moonraker.schedule_crashing` — minimum-cost time-cost crashing of that
  network when the deadline tightens.

*The station and its resupply*

* :mod:`moonraker.orbital_logistics` — Kepler orbit physics, ground launch
  windows, pass geometry, and the consumables/crew capacity model.
* :mod:`moonraker.orbital_transfer` — Hohmann transfer, phase-wait timing, the
  Tsiolkovsky propellant budget, and the deorbit burn.
* :mod:`moonraker.rendezvous` — Clohessy–Wiltshire relative motion and the
  closed-form single-impulse intercept for the final approach.

*The g-force programme*

* :mod:`moonraker.centrifuge` — centrifuge g↔rpm physics, the +Gz tolerance
  envelope, the ramp/sustain/decay profile builder, and the safety verdict.
* :mod:`moonraker.centrifuge_training` — g·s exposure dosing, gradual-onset-rate
  tolerance scaling, and exposure-capped weekly regimen planning.

All seven are the pure domain core: infrastructure-free (no ``bond_api``, no
``infrastructure``) and deterministic, so they can be imported and tested in
isolation. :mod:`moonraker.mission_results` composes them into the single
canonical result set; :mod:`moonraker.manuscript_variables` turns that into the
manuscript ``{{TOKEN}}`` map and :mod:`moonraker.figures` into the PNGs. The
BOND-API mission adapter lives in :mod:`moonraker.mission` and is imported
separately so the core stays importable without the protocol.
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
from .centrifuge_training import TrainingCycle, plan_training_cycle, profile_exposure
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
from .orbital_transfer import (
    HohmannTransfer,
    deorbit_dv,
    hohmann_transfer,
    phase_wait_time,
    propellant_fraction,
    propellant_mass,
    tsiolkovsky_mass_ratio,
    vis_viva,
)
from .rendezvous import (
    CWState,
    cw_propagate,
    cw_state_transition,
    mean_motion,
    single_impulse_intercept,
)
from .schedule_crashing import (
    DRAX_CRASH_OPTIONS,
    CrashableActivity,
    CrashResult,
    crash_schedule,
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
    "DRAX_CRASH_OPTIONS",
    "TrainingProfile",
    "TrainingCycle",
    "LaunchWindow",
    "TimelineActivity",
    "TimelineSchedule",
    "HohmannTransfer",
    "CrashResult",
    "CrashableActivity",
    "CWState",
    "build_training_profile",
    "circular_speed",
    "compute_timeline",
    "consumables_days",
    "crash_schedule",
    "cw_propagate",
    "cw_state_transition",
    "deorbit_dv",
    "depletion_day",
    "g_from_rpm",
    "hohmann_transfer",
    "launch_windows",
    "max_sustained_duration",
    "mean_motion",
    "orbital_period",
    "orbits_per_day",
    "pass_duration",
    "phase_wait_time",
    "plan_training_cycle",
    "profile_exposure",
    "profile_is_safe",
    "propellant_fraction",
    "propellant_mass",
    "resupply_interval",
    "rpm_for_g",
    "single_impulse_intercept",
    "sustainable_crew",
    "timeline_feasibility",
    "tsiolkovsky_mass_ratio",
    "vis_viva",
    "visibility_half_angle",
]
