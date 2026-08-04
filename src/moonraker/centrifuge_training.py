"""Centrifuge training regimen planning for the DRAX g-force programme.

A special agent cannot simply walk into a centrifuge and pull high g: the
training programme must respect physiological exposure limits. This module
models the regimen level of the concept with three real, deterministic pieces:

* :func:`gor_tolerance_multiplier` — gradual-onset-rate (GOR) dependence: a
  slower onset of g gives the cardiovascular system time to compensate, so the
  tolerated duration scales up (a monotone, bounded model of the aviation
  physiology result).
* :func:`exposure_g_seconds` / :func:`profile_exposure` — the accumulated
  +Gz exposure of a run measured in g·seconds above a baseline (the standard
  dosing unit in centrifuge training), integrated from a sampled g-level
  profile.
* :func:`max_sessions_for_cap` / :func:`plan_training_cycle` — a weekly
  session plan bounded by daily and weekly exposure caps, returning the
  maximum sustainable session count.

The module is infrastructure-free (stdlib ``math`` only) and deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass

from .centrifuge import TrainingProfile

__all__ = [
    "TrainingCycle",
    "gor_tolerance_multiplier",
    "exposure_g_seconds",
    "profile_exposure",
    "max_sessions_for_cap",
    "plan_training_cycle",
]


def gor_tolerance_multiplier(
    onset_rate_g_per_s: float,
    k: float = 0.35,
    floor: float = 0.5,
    ceiling: float = 2.5,
) -> float:
    """Return the tolerance multiplier for a given gradual-onset rate.

    Slower onset rates give a larger multiplier (more tolerated time at peak
    g); the result is clamped to ``[floor, ceiling]``. The model is
    ``1 + k / onset_rate`` and is monotonically decreasing in the onset rate.

    Args:
        onset_rate_g_per_s: how fast g rises during the ramp (g/s, > 0).
        k: shaping constant.
        floor / ceiling: clamp bounds (0 < floor <= ceiling).

    Returns:
        The multiplier applied to the sustained-duration tolerance.
    """
    _require_positive(onset_rate_g_per_s, "onset_rate_g_per_s")
    if not (isinstance(k, (int, float)) and k >= 0):
        raise ValueError(f"k must be >= 0 (got {k!r})")
    if not (isinstance(floor, (int, float)) and 0.0 < floor <= ceiling):
        raise ValueError(
            f"floor must satisfy 0 < floor <= ceiling (got floor={floor!r}, ceiling={ceiling!r})"
        )
    if not (isinstance(ceiling, (int, float)) and ceiling >= floor):
        raise ValueError(f"ceiling must be >= floor (got ceiling={ceiling!r})")
    raw = 1.0 + k / onset_rate_g_per_s
    return float(min(ceiling, max(floor, raw)))


def exposure_g_seconds(g_levels: tuple[float, ...], dt_s: float, baseline_g: float = 1.0) -> float:
    """Return the accumulated +Gz exposure (g·s) above ``baseline_g``.

    ``exposure = sum(max(0, g_i - baseline)) * dt`` over the sampled profile —
    the standard dosing measure for centrifuge runs. Zero-length or
    non-positive sampling steps are rejected.
    """
    if not (isinstance(g_levels, tuple) and g_levels):
        raise ValueError("g_levels must be a non-empty tuple")
    if not (isinstance(dt_s, (int, float)) and dt_s > 0):
        raise ValueError(f"dt_s must be > 0 (got {dt_s!r})")
    if not (isinstance(baseline_g, (int, float)) and baseline_g >= 0):
        raise ValueError(f"baseline_g must be >= 0 (got {baseline_g!r})")
    for g in g_levels:
        if not (isinstance(g, (int, float)) and g >= 0):
            raise ValueError(f"g_levels entries must be >= 0 (got {g!r})")
    total = sum(max(0.0, float(g) - float(baseline_g)) for g in g_levels)
    return float(total * dt_s)


def profile_exposure(profile: TrainingProfile, baseline_g: float = 1.0) -> float:
    """Return the g·s exposure of a sampled :class:`TrainingProfile`.

    The sampling step is derived from the profile's time samples; profiles with
    fewer than two samples are rejected (no step can be measured).
    """
    if not isinstance(profile, TrainingProfile):
        raise ValueError("profile must be a TrainingProfile")
    if len(profile.time_s) < 2:
        raise ValueError("profile must contain at least two samples to measure exposure")
    dt = profile.time_s[1] - profile.time_s[0]
    if dt <= 0:
        raise ValueError("profile time samples must be strictly increasing")
    return exposure_g_seconds(profile.g_levels, dt_s=dt, baseline_g=baseline_g)


def max_sessions_for_cap(per_session_g_s: float, cap_g_s: float) -> int:
    """Return the maximum whole sessions fitting under an exposure cap."""
    _require_positive(per_session_g_s, "per_session_g_s")
    _require_positive(cap_g_s, "cap_g_s")
    return int(cap_g_s // per_session_g_s)


@dataclass(frozen=True)
class TrainingCycle:
    """A weekly centrifuge training plan bounded by exposure caps.

    Fields:
        sessions_per_week: the planned session count.
        per_session_g_s: g·s exposure of a single session.
        weekly_exposure_g_s: ``sessions * per_session``.
        daily_cap_g_s / weekly_cap_g_s: the enforced limits.
        recommended_sessions: maximum sessions fitting the weekly cap.
        feasible: True when the plan respects both caps.
    """

    sessions_per_week: int
    per_session_g_s: float
    weekly_exposure_g_s: float
    daily_cap_g_s: float
    weekly_cap_g_s: float
    recommended_sessions: int
    feasible: bool

    def __post_init__(self) -> None:
        if not (isinstance(self.sessions_per_week, int) and self.sessions_per_week >= 0):
            raise ValueError("sessions_per_week must be a non-negative integer")
        for label, value in (
            ("per_session_g_s", self.per_session_g_s),
            ("weekly_exposure_g_s", self.weekly_exposure_g_s),
            ("daily_cap_g_s", self.daily_cap_g_s),
            ("weekly_cap_g_s", self.weekly_cap_g_s),
            ("recommended_sessions", self.recommended_sessions),
        ):
            if not (isinstance(value, (int, float)) and value >= 0):
                raise ValueError(f"{label} must be >= 0 (got {value!r})")


def plan_training_cycle(
    per_session_g_s: float,
    daily_cap_g_s: float,
    weekly_cap_g_s: float,
    sessions_per_week: int,
) -> TrainingCycle:
    """Plan a weekly training cycle against daily and weekly exposure caps.

    Args:
        per_session_g_s: g·s exposure of one session.
        daily_cap_g_s: per-session exposure ceiling (g·s).
        weekly_cap_g_s: per-week cumulative ceiling (g·s).
        sessions_per_week: the number of sessions the plan would run.

    Returns:
        A :class:`TrainingCycle`; ``feasible`` is True only when each session
        stays under the daily cap AND the weekly total stays under the weekly
        cap. ``recommended_sessions`` is the largest count the weekly cap
        admits.
    """
    _require_positive(per_session_g_s, "per_session_g_s")
    _require_positive(daily_cap_g_s, "daily_cap_g_s")
    _require_positive(weekly_cap_g_s, "weekly_cap_g_s")
    if not (isinstance(sessions_per_week, int) and sessions_per_week >= 0):
        raise ValueError(
            f"sessions_per_week must be a non-negative integer (got {sessions_per_week!r})"
        )

    weekly_exposure = per_session_g_s * sessions_per_week
    daily_ok = per_session_g_s <= daily_cap_g_s
    weekly_ok = weekly_exposure <= weekly_cap_g_s
    recommended = max_sessions_for_cap(per_session_g_s, weekly_cap_g_s)
    return TrainingCycle(
        sessions_per_week=sessions_per_week,
        per_session_g_s=per_session_g_s,
        weekly_exposure_g_s=weekly_exposure,
        daily_cap_g_s=daily_cap_g_s,
        weekly_cap_g_s=weekly_cap_g_s,
        recommended_sessions=recommended,
        feasible=bool(daily_ok and weekly_ok),
    )


def _require_positive(value: float, label: str) -> None:
    if not (isinstance(value, (int, float)) and value > 0):
        raise ValueError(f"{label} must be > 0 (got {value!r})")
