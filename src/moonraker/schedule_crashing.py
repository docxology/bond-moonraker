"""Time-cost crashing of the shuttle-hijack timeline.

When the hijack plan must finish inside a deadline tighter than its critical
path, the operation can be *crashed*: individual phases are compressed (more
agents, redundant systems, faster procedures) at a per-minute cost. This
module implements the classic project-crashing trade-off:

* :class:`CrashableActivity` — a phase with a normal duration, a minimum
  (crashed) duration and a linear cost per minute saved.
* :func:`crash_schedule` — the deterministic greedy crash: repeatedly locate
  the current critical path (via the CPM core in :mod:`moonraker.shuttle_ops`),
  pick the cheapest still-crashable critical activity, and crash it one minute
  at a time until the deadline is met or no further compression is possible.
* :data:`DRAX_CRASH_OPTIONS` — the canonical crashable version of the DRAX
  hijack timeline. It is *derived* from
  :data:`moonraker.shuttle_ops.DRAX_HIJACK_TIMELINE` rather than re-typed:
  durations and dependency edges come from the timeline, and only the crash
  economics (minimum duration and cost per minute) are new data here. The two
  networks therefore cannot drift apart, and
  :func:`_crashable_from_timeline` raises if the economics table stops covering
  the timeline exactly.

The module is infrastructure-free (stdlib only), deterministic, and shares the
CPM solver with :mod:`moonraker.shuttle_ops`.
"""

from __future__ import annotations

from dataclasses import dataclass

from .shuttle_ops import (
    DRAX_HIJACK_TIMELINE,
    TimelineActivity,
    TimelineSchedule,
    compute_timeline,
)

__all__ = [
    "CrashableActivity",
    "CrashResult",
    "crash_schedule",
    "DRAX_CRASH_ECONOMICS",
    "DRAX_CRASH_OPTIONS",
]


@dataclass(frozen=True)
class CrashableActivity:
    """A hijack phase that can be compressed at a cost.

    Fields:
        name: activity identifier (must match a timeline activity).
        normal_duration_min: the planned duration.
        crash_duration_min: the minimum achievable duration (<= normal).
        cost_per_min: cost of saving one minute (>= 0).
        depends_on: prerequisite activity names (mirrors the base timeline).
    """

    name: str
    normal_duration_min: float
    crash_duration_min: float
    cost_per_min: float
    depends_on: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("CrashableActivity.name must be a non-empty string")
        if not (
            isinstance(self.normal_duration_min, (int, float)) and self.normal_duration_min > 0
        ):
            raise ValueError(f"normal_duration_min must be > 0 (got {self.normal_duration_min!r})")
        if not (
            isinstance(self.crash_duration_min, (int, float))
            and 0 < self.crash_duration_min <= self.normal_duration_min
        ):
            raise ValueError(
                "crash_duration_min must satisfy 0 < crash <= normal "
                f"(got {self.crash_duration_min!r} vs normal {self.normal_duration_min!r})"
            )
        if not (isinstance(self.cost_per_min, (int, float)) and self.cost_per_min >= 0):
            raise ValueError(f"cost_per_min must be >= 0 (got {self.cost_per_min!r})")
        if not isinstance(self.depends_on, tuple):
            raise ValueError("CrashableActivity.depends_on must be a tuple")
        for dep in self.depends_on:
            if not (isinstance(dep, str) and dep.strip()):
                raise ValueError("CrashableActivity.depends_on entries must be non-empty strings")


@dataclass(frozen=True)
class CrashResult:
    """Outcome of a schedule-crash run.

    Fields:
        original_duration_min: the uncrashed critical-path length.
        final_duration_min: the critical-path length after crashing.
        total_cost: the summed crash cost.
        crashed: activity name -> minutes crashed.
        feasible: True when the deadline was reached.
        final_critical_activities: the zero-slack activity *set* after crashing
            (a union when the crashed network carries several critical paths —
            see :class:`moonraker.shuttle_ops.TimelineSchedule`).
    """

    original_duration_min: float
    final_duration_min: float
    total_cost: float
    crashed: dict[str, float]
    feasible: bool
    final_critical_activities: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.crashed, dict):
            raise ValueError("CrashResult.crashed must be a dict")
        for label, value in (
            ("original_duration_min", self.original_duration_min),
            ("final_duration_min", self.final_duration_min),
            ("total_cost", self.total_cost),
        ):
            if not (isinstance(value, (int, float)) and value >= 0):
                raise ValueError(f"{label} must be >= 0 (got {value!r})")
        if not (
            isinstance(self.feasible, bool) and isinstance(self.final_critical_activities, tuple)
        ):
            raise ValueError(
                "CrashResult.feasible must be bool and final_critical_activities a tuple"
            )


def crash_schedule(
    activities: tuple[CrashableActivity, ...],
    deadline_min: float,
) -> CrashResult:
    """Crash the cheapest critical activities until the deadline is met.

    Args:
        activities: the crashable phases (all names unique).
        deadline_min: the hard deadline to reach (minutes).

    Returns:
        A :class:`CrashResult`; ``feasible`` is False when even fully-crashed
        critical phases cannot reach the deadline.

    Raises:
        ValueError: on duplicate names, an empty set, a non-positive deadline,
            or activities whose names do not form a valid dependency network.
    """
    if not activities:
        raise ValueError("crash_schedule requires at least one activity")
    if not (isinstance(deadline_min, (int, float)) and deadline_min > 0):
        raise ValueError(f"deadline_min must be > 0 (got {deadline_min!r})")

    names = {a.name for a in activities}
    if len(names) != len(activities):
        raise ValueError("CrashableActivity names must be unique")

    crashed: dict[str, float] = {a.name: 0.0 for a in activities}
    remaining: dict[str, float] = {
        a.name: float(a.normal_duration_min - a.crash_duration_min) for a in activities
    }

    def _base_schedule() -> TimelineSchedule:
        timeline = tuple(
            TimelineActivity(
                name=a.name,
                duration_min=float(a.normal_duration_min) - crashed[a.name],
                depends_on=a.depends_on,
            )
            for a in activities
        )
        return compute_timeline(timeline)

    schedule = _base_schedule()
    original = schedule.total_duration_min
    total_cost = 0.0

    while schedule.total_duration_min > deadline_min:
        critical_crashable: list[str] = []
        for name in schedule.critical_activities:
            if remaining[name] > 1e-9:
                critical_crashable.append(name)
        if not critical_crashable:
            break
        cheapest = min(
            critical_crashable,
            key=lambda n: (activities_by_name(activities, n).cost_per_min, n),
        )
        step = min(1.0, remaining[cheapest], schedule.total_duration_min - deadline_min)
        crashed[cheapest] += step
        remaining[cheapest] -= step
        total_cost += step * activities_by_name(activities, cheapest).cost_per_min
        schedule = _base_schedule()

    final_duration = schedule.total_duration_min
    return CrashResult(
        original_duration_min=original,
        final_duration_min=final_duration,
        total_cost=total_cost,
        crashed={name: round(minutes, 4) for name, minutes in crashed.items() if minutes > 1e-9},
        feasible=bool(final_duration <= deadline_min),
        final_critical_activities=schedule.critical_activities,
    )


def activities_by_name(activities: tuple[CrashableActivity, ...], name: str) -> CrashableActivity:
    """Return the crashable activity with ``name`` (used by the greedy loop)."""
    for activity in activities:
        if activity.name == name:
            return activity
    raise KeyError(f"no crashable activity named {name!r}")


#: Crash economics for the DRAX hijack: activity name -> (minimum achievable
#: duration in minutes, cost per minute saved). This table is the ONLY crash
#: data authored here; normal durations and dependency edges are read from
#: :data:`moonraker.shuttle_ops.DRAX_HIJACK_TIMELINE`.
DRAX_CRASH_ECONOMICS: dict[str, tuple[float, float]] = {
    "infiltrate_launch_tower": (8.0, 2.0),
    "neutralise_shuttle_crew": (6.0, 3.0),
    "seize_flight_deck": (4.0, 4.0),
    "assume_ground_control": (10.0, 2.5),
    "launch_shuttle": (3.0, 5.0),
    "execute_orbital_insertion": (8.0, 3.5),
    "spoof_telemetry": (5.0, 2.0),
    "rendezvous_drax_station": (18.0, 4.0),
}


def _crashable_from_timeline(
    timeline: tuple[TimelineActivity, ...],
    economics: dict[str, tuple[float, float]],
) -> tuple[CrashableActivity, ...]:
    """Attach crash economics to a timeline, refusing any mismatch.

    Durations and prerequisites come from ``timeline``, so the crashable network
    is a projection of the canonical one rather than a hand-kept copy. The
    economics table must name every timeline activity and nothing else — an
    activity added to the timeline without crash data, or crash data left behind
    for a deleted activity, raises here at import rather than silently producing
    a crash network that models a different plan.

    Raises:
        ValueError: when the economics keys and the timeline names differ.
    """
    names = {a.name for a in timeline}
    missing = sorted(names - set(economics))
    extra = sorted(set(economics) - names)
    if missing or extra:
        raise ValueError(
            f"crash economics must cover the timeline exactly (missing={missing}, unknown={extra})"
        )
    return tuple(
        CrashableActivity(
            name=activity.name,
            normal_duration_min=float(activity.duration_min),
            crash_duration_min=economics[activity.name][0],
            cost_per_min=economics[activity.name][1],
            depends_on=activity.depends_on,
        )
        for activity in timeline
    )


#: Canonical crashable DRAX hijack timeline, derived from the canonical network.
DRAX_CRASH_OPTIONS: tuple[CrashableActivity, ...] = _crashable_from_timeline(
    DRAX_HIJACK_TIMELINE, DRAX_CRASH_ECONOMICS
)
