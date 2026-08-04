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
  hijack timeline.

The module is infrastructure-free (stdlib only), deterministic, and shares the
CPM solver with :mod:`moonraker.shuttle_ops`.
"""

from __future__ import annotations

from dataclasses import dataclass

from .shuttle_ops import TimelineActivity, TimelineSchedule, compute_timeline

__all__ = [
    "CrashableActivity",
    "CrashResult",
    "crash_schedule",
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
        final_critical_path: the critical path after crashing.
    """

    original_duration_min: float
    final_duration_min: float
    total_cost: float
    crashed: dict[str, float]
    feasible: bool
    final_critical_path: tuple[str, ...]

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
        if not (isinstance(self.feasible, bool) and isinstance(self.final_critical_path, tuple)):
            raise ValueError("CrashResult.feasible must be bool and final_critical_path a tuple")


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
        for name in schedule.critical_path:
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
        final_critical_path=schedule.critical_path,
    )


def activities_by_name(activities: tuple[CrashableActivity, ...], name: str) -> CrashableActivity:
    """Return the crashable activity with ``name`` (used by the greedy loop)."""
    for activity in activities:
        if activity.name == name:
            return activity
    raise KeyError(f"no crashable activity named {name!r}")


#: Canonical crashable DRAX hijack timeline (normal, crash, cost-per-minute).
DRAX_CRASH_OPTIONS: tuple[CrashableActivity, ...] = (
    CrashableActivity("infiltrate_launch_tower", 12.0, 8.0, 2.0),
    CrashableActivity("neutralise_shuttle_crew", 9.0, 6.0, 3.0, ("infiltrate_launch_tower",)),
    CrashableActivity("seize_flight_deck", 6.0, 4.0, 4.0, ("infiltrate_launch_tower",)),
    CrashableActivity("assume_ground_control", 15.0, 10.0, 2.5, ("infiltrate_launch_tower",)),
    CrashableActivity(
        "launch_shuttle", 4.0, 3.0, 5.0, ("neutralise_shuttle_crew", "seize_flight_deck")
    ),
    CrashableActivity("execute_orbital_insertion", 10.0, 8.0, 3.5, ("launch_shuttle",)),
    CrashableActivity("spoof_telemetry", 8.0, 5.0, 2.0, ("assume_ground_control",)),
    CrashableActivity(
        "rendezvous_drax_station",
        22.0,
        18.0,
        4.0,
        ("execute_orbital_insertion", "spoof_telemetry"),
    ),
)
