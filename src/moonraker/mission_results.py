"""Canonical deterministic DRAX mission results.

This is the single place the pipeline computes the numeric results that feed
the manuscript variables and the ``execute`` CLI. It runs the pure domain core
over a fixed, documented parameter set (matching the DRAX mission plan) and
returns a deterministic dict. Everything is a closed-form computation — no RNG,
no wall-clock — so reruns are byte-identical.
"""

from __future__ import annotations

from typing import Any

from .centrifuge import build_training_profile, profile_is_safe, rpm_for_g
from .orbital_logistics import (
    circular_speed,
    consumables_days,
    launch_windows,
    orbital_period,
    orbits_per_day,
    sustainable_crew,
)
from .shuttle_ops import DRAX_HIJACK_TIMELINE, compute_timeline, timeline_feasibility

__all__ = ["compute_mission_results", "MISSION_DEFAULTS"]

#: Fixed DRAX mission parameter set (mirrors manuscript/config.yaml -> mission:).
MISSION_DEFAULTS: dict[str, Any] = {
    "deadline_min": 60.0,
    "station_altitude_km": 350.0,
    "crew": 6,
    "capacity_kg": 5400.0,
    "rate_kg_per_person_day": 2.0,
    "resupply_interval_days": 6.0,
    "centrifuge_target_g": 6.0,
    "centrifuge_radius_m": 8.0,
    "centrifuge_sustain_s": 12.0,
    "ramp_rate_g_per_s": 0.5,
    "decay_rate_g_per_s": 1.0,
    "g_limit": 9.0,
    "duration_limit_s": 30.0,
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
    safe, metrics = profile_is_safe(profile, float(p["g_limit"]), float(p["duration_limit_s"]))
    rpm = rpm_for_g(profile.peak_g, float(p["centrifuge_radius_m"]))

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
    }
