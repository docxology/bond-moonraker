"""Tests for moonraker.shuttle_ops — the shuttle-hijack critical-path model."""

import pytest

from moonraker.shuttle_ops import (
    DRAX_HIJACK_TIMELINE,
    TimelineActivity,
    compute_timeline,
    timeline_feasibility,
)


def _attrs(activity: TimelineActivity) -> tuple[str, float, tuple[str, ...]]:
    return activity.name, activity.duration_min, activity.depends_on


class TestTimelineActivityValidation:
    def test_valid(self) -> None:
        a = TimelineActivity("launch", 4.0)
        assert _attrs(a) == ("launch", 4.0, ())

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError):
            TimelineActivity("  ", 4.0)

    def test_nonpositive_duration_raises(self) -> None:
        with pytest.raises(ValueError):
            TimelineActivity("a", 0.0)
        with pytest.raises(ValueError):
            TimelineActivity("a", -1.0)

    def test_non_tuple_depends_on_raises(self) -> None:
        with pytest.raises(ValueError):
            TimelineActivity("a", 1.0, ["b"])  # type: ignore[arg-type]

    def test_empty_dep_entry_raises(self) -> None:
        with pytest.raises(ValueError):
            TimelineActivity("a", 1.0, (" ",))


class TestComputeTimeline:
    def test_drax_timeline_total_and_critical(self) -> None:
        schedule = compute_timeline(DRAX_HIJACK_TIMELINE)
        assert schedule.total_duration_min == pytest.approx(57.0)
        assert "rendezvous_drax_station" in schedule.critical_path
        assert "infiltrate_launch_tower" in schedule.critical_path
        assert "launch_shuttle" in schedule.critical_path
        # seize_flight_deck is off the critical path (has positive slack).
        assert "seize_flight_deck" not in schedule.critical_path
        assert schedule.slack["seize_flight_deck"] == pytest.approx(3.0)

    def test_linear_network(self) -> None:
        network = (
            TimelineActivity("a", 5.0),
            TimelineActivity("b", 3.0, ("a",)),
        )
        schedule = compute_timeline(network)
        assert schedule.total_duration_min == pytest.approx(8.0)
        assert schedule.critical_path == ("a", "b")
        assert schedule.earliest_start["b"] == pytest.approx(5.0)

    def test_parallel_branches_slack(self) -> None:
        network = (
            TimelineActivity("root", 2.0),
            TimelineActivity("long", 10.0, ("root",)),
            TimelineActivity("short", 4.0, ("root",)),
            TimelineActivity("sink", 1.0, ("long", "short")),
        )
        schedule = compute_timeline(network)
        # long branch is the critical one; short has slack.
        assert schedule.total_duration_min == pytest.approx(13.0)
        assert "long" in schedule.critical_path
        assert "short" not in schedule.critical_path
        assert schedule.slack["short"] == pytest.approx(6.0)

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            compute_timeline(())

    def test_duplicate_names_raise(self) -> None:
        with pytest.raises(ValueError):
            compute_timeline((TimelineActivity("a", 1.0), TimelineActivity("a", 2.0)))

    def test_unknown_dependency_raises(self) -> None:
        with pytest.raises(ValueError):
            compute_timeline((TimelineActivity("a", 1.0, ("ghost",)),))

    def test_cycle_raises(self) -> None:
        network = (
            TimelineActivity("a", 1.0, ("b",)),
            TimelineActivity("b", 1.0, ("a",)),
        )
        with pytest.raises(ValueError):
            compute_timeline(network)

    def test_self_cycle_raises(self) -> None:
        with pytest.raises(ValueError):
            compute_timeline((TimelineActivity("a", 1.0, ("a",)),))

    def test_deterministic(self) -> None:
        s1 = compute_timeline(DRAX_HIJACK_TIMELINE)
        s2 = compute_timeline(DRAX_HIJACK_TIMELINE)
        assert s1.earliest_finish == s2.earliest_finish
        assert s1.critical_path == s2.critical_path


class TestTimelineFeasibility:
    def test_feasible_with_margin(self) -> None:
        schedule = compute_timeline(DRAX_HIJACK_TIMELINE)
        feasible, margin = timeline_feasibility(schedule, 60.0)
        assert feasible is True
        assert margin == pytest.approx(3.0)

    def test_infeasible_when_deadline_tight(self) -> None:
        schedule = compute_timeline(DRAX_HIJACK_TIMELINE)
        feasible, margin = timeline_feasibility(schedule, 50.0)
        assert feasible is False
        assert margin == pytest.approx(-7.0)

    def test_invalid_deadline_raises(self) -> None:
        schedule = compute_timeline(DRAX_HIJACK_TIMELINE)
        with pytest.raises(ValueError):
            timeline_feasibility(schedule, 0.0)
        with pytest.raises(ValueError):
            timeline_feasibility(schedule, -5.0)
