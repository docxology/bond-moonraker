"""Canonical deterministic DRAX mission results.

This is the single place the pipeline computes the numeric results that feed
the manuscript variables and the ``execute`` CLI. It runs the pure domain core
over a fixed, documented parameter set (matching the DRAX mission plan) and
returns a deterministic dict. Everything is a closed-form computation — no RNG,
no wall-clock — so reruns are byte-identical.

The :func:`compute_transfer`, :func:`compute_rendezvous`,
:func:`compute_training` and :func:`compute_crash` helpers are the
single-source-of-truth factories shared by both the mission ``execute()``
adapter and the manuscript token map, so an outcome result and its
corresponding ``{{TOKEN}}`` can never disagree.
"""

from __future__ import annotations

import math
from typing import Any

from .centrifuge import build_training_profile, profile_is_safe, rpm_for_g
from .centrifuge_training import plan_training_cycle, profile_exposure
from .orbital_logistics import (
    EARTH_RADIUS_KM,
    circular_speed,
    consumables_days,
    launch_windows,
    orbital_period,
    orbits_per_day,
    sustainable_crew,
)
from .orbital_transfer import (
    deorbit_dv,
    hohmann_transfer,
    phase_wait_time,
    propellant_mass,
    tsiolkovsky_mass_ratio,
)
from .rendezvous import mean_motion, single_impulse_intercept
from .schedule_crashing import DRAX_CRASH_OPTIONS, crash_schedule
from .shuttle_ops import DRAX_HIJACK_TIMELINE, compute_timeline, timeline_feasibility

__all__ = [
    "MISSION_DEFAULTS",
    "compute_mission_results",
    "compute_transfer",
    "compute_rendezvous",
    "compute_training",
    "compute_crash",
]

#: Fixed DRAX mission parameter set (mirrors manuscript/config.yaml -> mission:).
MISSION_DEFAULTS: dict[str, Any] = {
    # Shuttle hijack timeline.
    "deadline_min": 60.0,
    # Orbital logistics / station.
    "station_altitude_km": 350.0,
    "crew": 6,
    "capacity_kg": 5400.0,
    "rate_kg_per_person_day": 2.0,
    "resupply_interval_days": 6.0,
    # Orbital transfer / rendezvous.
    "park_altitude_km": 200.0,
    "transfer_isp_s": 300.0,
    "transfer_dry_mass_kg": 2500.0,
    "deorbit_perigee_km": 100.0,
    "rendezvous_intercept_s": 1200.0,
    # Centrifuge profile + training regimen.
    "centrifuge_target_g": 6.0,
    "centrifuge_radius_m": 8.0,
    "centrifuge_sustain_s": 12.0,
    "ramp_rate_g_per_s": 0.5,
    "decay_rate_g_per_s": 1.0,
    "g_limit": 9.0,
    "duration_limit_s": 30.0,
    "centrifuge_margin_fraction": 0.2,
    "training_daily_cap_g_s": 150.0,
    "training_weekly_cap_g_s": 400.0,
    "training_sessions_per_week": 4,
    # Schedule crashing.
    "crash_deadline_min": 50.0,
}


def compute_transfer(params: dict[str, Any]) -> dict[str, Any]:
    """Canonical Hohmann-transfer + propellant + deorbit metrics for the resupply."""
    park = float(params["park_altitude_km"]) + EARTH_RADIUS_KM
    station = float(params["station_altitude_km"]) + EARTH_RADIUS_KM
    isp = float(params["transfer_isp_s"])
    wet_mass = float(params["transfer_dry_mass_kg"]) + float(params["capacity_kg"])

    transfer = hohmann_transfer(park, station)
    wait_s, lead_rad = phase_wait_time(park, station, 0.0)
    ratio = tsiolkovsky_mass_ratio(transfer.total_dv_km_s, isp)
    propellant = propellant_mass(transfer.total_dv_km_s, isp, wet_mass)
    deorbit = deorbit_dv(station, float(params["deorbit_perigee_km"]) + EARTH_RADIUS_KM)

    return {
        "dv1_km_s": transfer.dv1_km_s,
        "dv2_km_s": transfer.dv2_km_s,
        "total_dv_km_s": transfer.total_dv_km_s,
        "transfer_time_s": transfer.transfer_time_s,
        "wait_s": wait_s,
        "lead_deg": math.degrees(lead_rad),
        "mass_ratio": ratio,
        "propellant_kg": propellant,
        "deorbit_dv_km_s": deorbit,
    }


def compute_rendezvous(params: dict[str, Any]) -> dict[str, Any]:
    """Canonical Clohessy–Wiltshire intercept metrics for the final approach."""
    station = float(params["station_altitude_km"]) + EARTH_RADIUS_KM
    n = mean_motion(station)
    t = float(params["rendezvous_intercept_s"])
    impulse, _v0 = single_impulse_intercept(n, t, (0.5, 2.0, 0.0))
    return {"impulse_km_s": impulse, "time_s": t}


def compute_training(params: dict[str, Any]) -> dict[str, Any]:
    """Canonical centrifuge training-regimen metrics (exposure + cycle plan)."""
    profile = build_training_profile(
        target_g=float(params["centrifuge_target_g"]),
        radius_m=float(params["centrifuge_radius_m"]),
        sustain_s=float(params["centrifuge_sustain_s"]),
        ramp_rate_g_per_s=float(params["ramp_rate_g_per_s"]),
        decay_rate_g_per_s=float(params["decay_rate_g_per_s"]),
    )
    per_session = profile_exposure(profile)
    cycle = plan_training_cycle(
        per_session_g_s=per_session,
        daily_cap_g_s=float(params["training_daily_cap_g_s"]),
        weekly_cap_g_s=float(params["training_weekly_cap_g_s"]),
        sessions_per_week=int(params["training_sessions_per_week"]),
    )
    return {
        "per_session_g_s": per_session,
        "weekly_g_s": cycle.weekly_exposure_g_s,
        "sessions": cycle.sessions_per_week,
        "recommended": cycle.recommended_sessions,
        "feasible": cycle.feasible,
    }


def compute_crash(params: dict[str, Any]) -> dict[str, Any]:
    """Canonical schedule-crash metrics for the hijack timeline."""
    result = crash_schedule(DRAX_CRASH_OPTIONS, float(params["crash_deadline_min"]))
    return {
        "deadline_min": float(params["crash_deadline_min"]),
        "final_min": result.final_duration_min,
        "saved_min": result.original_duration_min - result.final_duration_min,
        "total_cost": result.total_cost,
        "feasible": result.feasible,
        "activities": ", ".join(sorted(result.crashed)),
    }


def compute_mission_results(params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the full deterministic DRAX mission result set.

    Args:
        params: optional override of :data:`MISSION_DEFAULTS`; missing keys fall
            back to the defaults.

    Returns:
        A flat dict of result metrics keyed by manuscript-token suffix.
    """
    p = {**MISSION_DEFAULTS, **(params or {})}

    # Shuttle hijack timeline (critical path + feasibility).
    schedule = compute_timeline(DRAX_HIJACK_TIMELINE)
    feasible, margin = timeline_feasibility(schedule, float(p["deadline_min"]))

    # Orbital logistics.
    altitude = float(p["station_altitude_km"])
    period_s = orbital_period(altitude)
    windows = launch_windows(altitude, num_windows=6)
    consumables = consumables_days(
        float(p["capacity_kg"]), int(p["crew"]), float(p["rate_kg_per_person_day"])
    )
    max_crew = sustainable_crew(
        float(p["capacity_kg"]),
        float(p["resupply_interval_days"]),
        float(p["rate_kg_per_person_day"]),
    )

    # Centrifuge g-profile + safety.
    profile = build_training_profile(
        target_g=float(p["centrifuge_target_g"]),
        radius_m=float(p["centrifuge_radius_m"]),
        sustain_s=float(p["centrifuge_sustain_s"]),
        ramp_rate_g_per_s=float(p["ramp_rate_g_per_s"]),
        decay_rate_g_per_s=float(p["decay_rate_g_per_s"]),
    )
    safe, metrics = profile_is_safe(
        profile,
        float(p["g_limit"]),
        float(p["duration_limit_s"]),
        margin_fraction=float(p["centrifuge_margin_fraction"]),
    )
    rpm = rpm_for_g(profile.peak_g, float(p["centrifuge_radius_m"]))
    # Signed plateau exceedance: positive means the plateau overruns the
    # governing allowance (the profile is NOT certified), negative means
    # headroom remains. Reported so the prose never has to assert a verdict.
    exceedance_s = profile.sustain_duration_s - metrics["allowable_s"]

    # Deepened concepts (canonical factories).
    transfer = compute_transfer(p)
    rendezvous = compute_rendezvous(p)
    training = compute_training(p)
    crash = compute_crash(p)

    return {
        "SHUTTLE_TOTAL_MIN": round(schedule.total_duration_min, 2),
        "SHUTTLE_NUM_PHASES": len(DRAX_HIJACK_TIMELINE),
        "SHUTTLE_CRITICAL_PATH": ", ".join(schedule.critical_path),
        "SHUTTLE_FEASIBLE": "yes" if feasible else "no",
        "SHUTTLE_MARGIN_MIN": round(margin, 2),
        "ORBIT_PERIOD_S": round(period_s, 1),
        "ORBIT_SPEED_KMS": round(circular_speed(altitude), 3),
        "ORBIT_ORBITS_PER_DAY": round(orbits_per_day(altitude), 1),
        "ORBIT_WINDOW_COUNT": len(windows),
        "ORBIT_CONSUMABLES_DAYS": round(consumables, 1),
        "ORBIT_SUSTAINABLE_CREW": max_crew,
        "CENTRIFUGE_PEAK_G": round(profile.peak_g, 2),
        "CENTRIFUGE_SUSTAIN_S": round(profile.sustain_duration_s, 2),
        "CENTRIFUGE_ALLOWABLE_S": round(metrics["allowable_s"], 2),
        "CENTRIFUGE_RPM": round(rpm, 1),
        "CENTRIFUGE_SAFE": "yes" if safe else "no",
        "CENTRIFUGE_VERDICT": "certified" if safe else "not certified",
        "CENTRIFUGE_EXCEEDANCE_S": round(exceedance_s, 2),
        # Orbital transfer / rendezvous.
        "TRANSFER_DV1_KMS": round(transfer["dv1_km_s"], 4),
        "TRANSFER_DV2_KMS": round(transfer["dv2_km_s"], 4),
        "TRANSFER_TOTAL_DV_KMS": round(transfer["total_dv_km_s"], 4),
        "TRANSFER_TIME_MIN": round(transfer["transfer_time_s"] / 60.0, 1),
        "TRANSFER_WAIT_H": round(transfer["wait_s"] / 3600.0, 1),
        "TRANSFER_LEAD_DEG": round(transfer["lead_deg"], 2),
        "TRANSFER_MASS_RATIO": round(transfer["mass_ratio"], 4),
        "TRANSFER_PROPELLANT_KG": round(transfer["propellant_kg"], 1),
        "TRANSFER_DEORBIT_KMS": round(transfer["deorbit_dv_km_s"], 4),
        "RENDEZVOUS_IMPULSE_M_S": round(rendezvous["impulse_km_s"] * 1000.0, 3),
        "RENDEZVOUS_TIME_S": int(rendezvous["time_s"]),
        # Centrifuge training regimen.
        "TRAINING_PER_SESSION_GS": round(training["per_session_g_s"], 1),
        "TRAINING_WEEKLY_GS": round(training["weekly_g_s"], 1),
        "TRAINING_SESSIONS": training["sessions"],
        "TRAINING_RECOMMENDED": training["recommended"],
        "TRAINING_FEASIBLE": "yes" if training["feasible"] else "no",
        # Schedule crashing.
        "CRASH_DEADLINE_MIN": round(crash["deadline_min"], 1),
        "CRASH_FINAL_MIN": round(crash["final_min"], 1),
        "CRASH_SAVED_MIN": round(crash["saved_min"], 1),
        "CRASH_TOTAL_COST": round(crash["total_cost"], 1),
        "CRASH_FEASIBLE": "yes" if crash["feasible"] else "no",
        "CRASH_ACTIVITIES": crash["activities"],
    }
