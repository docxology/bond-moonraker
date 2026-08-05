"""Shuttle hijack timeline model (space-shuttle hijack).

The DRAX concept models a hostile takeover of a NASA space shuttle as a
deterministic project network and solves it with the Critical Path Method
(CPM). Each phase of the hijack — from launch-tower infiltration to
orbital insertion and docking with Drax's station — is an activity with a
duration and a set of prerequisite activities. A forward pass computes the
earliest start/finish of every activity, a backward pass computes the latest
start/finish, and the slack reveals which phases are load-bearing (zero
slack) on the critical path. Because the shuttle is a moving deadline (it
reaches a point of no return the moment it commits to orbital insertion),
the whole plan must fit inside a hard ``deadline`` before it is feasible.

The module is deliberately infrastructure-free (stdlib only): it is the pure
mathematical core of the ``moonraker`` package and can be lifted into any
Python environment without ``bond_api`` or the BOND suite installed.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "TimelineActivity",
    "TimelineSchedule",
    "compute_timeline",
    "timeline_feasibility",
    "DRAX_HIJACK_TIMELINE",
]


@dataclass(frozen=True)
class TimelineActivity:
    """A single hijack phase: a name, a duration, and its prerequisites.

    Fields:
        name: unique activity identifier.
        duration_min: duration of the phase in minutes (must be > 0).
        depends_on: names of activities that must finish before this one can
            start (empty tuple for the network's source activities).
    """

    name: str
    duration_min: float
    depends_on: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("TimelineActivity.name must be a non-empty string")
        if not (isinstance(self.duration_min, (int, float)) and self.duration_min > 0):
            raise ValueError(
                f"TimelineActivity.duration_min must be > 0 (got {self.duration_min!r})"
            )
        if not isinstance(self.depends_on, tuple):
            raise ValueError("TimelineActivity.depends_on must be a tuple")
        for dep in self.depends_on:
            if not (isinstance(dep, str) and dep.strip()):
                raise ValueError("TimelineActivity.depends_on entries must be non-empty strings")


@dataclass(frozen=True)
class TimelineSchedule:
    """Result of a CPM pass over a hijack timeline.

    Fields:
        earliest_start: activity name -> earliest start minute (from launch_t=0).
        earliest_finish: activity name -> earliest finish minute.
        latest_start: activity name -> latest start minute without delaying the
            project (from the backward pass).
        latest_finish: activity name -> latest finish minute.
        slack: activity name -> total float in minutes (>= 0).
        total_duration_min: length of the critical path in minutes.
        critical_path: ordered tuple of activity names with zero slack.
    """

    earliest_start: dict[str, float]
    earliest_finish: dict[str, float]
    latest_start: dict[str, float]
    latest_finish: dict[str, float]
    slack: dict[str, float]
    total_duration_min: float
    critical_path: tuple[str, ...]


def _validate_network(activities: tuple[TimelineActivity, ...]) -> None:
    """Guard against duplicate names, unknown deps and dependency cycles."""
    names = {a.name for a in activities}
    if len(names) != len(activities):
        raise ValueError("TimelineActivity names must be unique")
    for activity in activities:
        for dep in activity.depends_on:
            if dep not in names:
                raise ValueError(f"activity {activity.name!r} depends on unknown activity {dep!r}")

    # Kahn-style cycle detection: repeatedly strip zero-dependency activities.
    # If a round finds nothing ready while activities remain, the residue is a
    # cycle (every remaining activity still waits on another remaining one).
    pending = {a.name: set(a.depends_on) for a in activities}
    while pending:
        ready = [name for name, deps in pending.items() if not deps]
        if not ready:
            raise ValueError("hijack timeline contains a dependency cycle")
        for name in ready:
            del pending[name]
            for deps in pending.values():
                deps.discard(name)


def compute_timeline(activities: tuple[TimelineActivity, ...]) -> TimelineSchedule:
    """Run the Critical Path Method over a hijack timeline.

    Args:
        activities: the hijack phases and their dependencies (must form a DAG).

    Returns:
        A :class:`TimelineSchedule` with per-activity critical-path floats.

    Raises:
        ValueError: on duplicate names, unknown dependencies, non-positive
            durations or a cyclic network.
    """
    if not isinstance(activities, tuple):
        activities = tuple(activities)
    if not activities:
        raise ValueError("hijack timeline must contain at least one activity")
    _validate_network(activities)

    deps_of: dict[str, set[str]] = {a.name: set(a.depends_on) for a in activities}
    duration: dict[str, float] = {a.name: float(a.duration_min) for a in activities}

    # Forward pass: ES = max(EF of deps), EF = ES + duration.
    earliest_start: dict[str, float] = {}
    earliest_finish: dict[str, float] = {}
    pending = list(deps_of)
    while pending:
        ready = [n for n in pending if not (deps_of[n] - set(earliest_finish))]
        for name in ready:
            dep_ef = [earliest_finish[d] for d in deps_of[name]] or [0.0]
            es = max(dep_ef)
            earliest_start[name] = es
            earliest_finish[name] = es + duration[name]
            pending.remove(name)

    project_end = max(earliest_finish.values())

    # Backward pass: LF = min(LS of successors), LS = LF - duration.
    succ_of: dict[str, set[str]] = {a.name: set() for a in activities}
    for a in activities:
        for dep in a.depends_on:
            succ_of[dep].add(a.name)

    latest_start: dict[str, float] = {}
    latest_finish: dict[str, float] = {}
    pending = list(earliest_start)
    while pending:
        ready = [n for n in pending if all(s in latest_start for s in succ_of[n])]
        for name in ready:
            succ_ls = [latest_start[s] for s in succ_of[name]] or [project_end]
            lf = min(succ_ls)
            latest_finish[name] = lf
            latest_start[name] = lf - duration[name]
            pending.remove(name)

    slack = {n: latest_finish[n] - earliest_finish[n] for n in earliest_start}
    critical = tuple(
        name
        for name, _ in sorted(earliest_start.items(), key=lambda kv: (kv[1], kv[0]))
        if slack[name] <= 1e-9
    )

    return TimelineSchedule(
        earliest_start=earliest_start,
        earliest_finish=earliest_finish,
        latest_start=latest_start,
        latest_finish=latest_finish,
        slack=slack,
        total_duration_min=project_end,
        critical_path=critical,
    )


def timeline_feasibility(schedule: TimelineSchedule, deadline_min: float) -> tuple[bool, float]:
    """Check whether a hijack timeline finishes inside a hard deadline.

    Args:
        schedule: the computed CPM schedule.
        deadline_min: the point of no return (minutes from launch) by which the
            hijack must be complete.

    Returns:
        ``(feasible, margin_min)`` where ``margin_min`` is positive when the
        plan fits (deadline less the total duration) and negative when it does
        not. ``feasible`` is True iff ``margin_min >= 0``.
    """
    if not (isinstance(deadline_min, (int, float)) and deadline_min > 0):
        raise ValueError(f"deadline_min must be > 0 (got {deadline_min!r})")
    margin = float(deadline_min) - schedule.total_duration_min
    return margin >= 0, margin


#: Canonical Drax hijack timeline (minutes). The hostage-taking of the shuttle
#: commences at launch-tower infiltration and must finish before the shuttle
#: crosses its orbital-insertion point of no return (the ``deadline``).
DRAX_HIJACK_TIMELINE: tuple[TimelineActivity, ...] = (
    TimelineActivity("infiltrate_launch_tower", 12.0),
    TimelineActivity("neutralise_shuttle_crew", 9.0, ("infiltrate_launch_tower",)),
    TimelineActivity("seize_flight_deck", 6.0, ("infiltrate_launch_tower",)),
    TimelineActivity("assume_ground_control", 15.0, ("infiltrate_launch_tower",)),
    TimelineActivity("launch_shuttle", 4.0, ("neutralise_shuttle_crew", "seize_flight_deck")),
    TimelineActivity("execute_orbital_insertion", 10.0, ("launch_shuttle",)),
    TimelineActivity("spoof_telemetry", 8.0, ("assume_ground_control",)),
    TimelineActivity(
        "rendezvous_drax_station", 22.0, ("execute_orbital_insertion", "spoof_telemetry")
    ),
)
