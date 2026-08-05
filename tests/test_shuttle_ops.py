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
        assert "rendezvous_drax_station" in schedule.critical_activities
        assert "infiltrate_launch_tower" in schedule.critical_activities
        assert "launch_shuttle" in schedule.critical_activities
        # seize_flight_deck is off the critical path (has positive slack).
        assert "seize_flight_deck" not in schedule.critical_activities
        assert schedule.slack["seize_flight_deck"] == pytest.approx(3.0)

    def test_linear_network(self) -> None:
        network = (
            TimelineActivity("a", 5.0),
            TimelineActivity("b", 3.0, ("a",)),
        )
        schedule = compute_timeline(network)
        assert schedule.total_duration_min == pytest.approx(8.0)
        assert schedule.critical_activities == ("a", "b")
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
        assert "long" in schedule.critical_activities
        assert "short" not in schedule.critical_activities
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
        assert s1.critical_activities == s2.critical_activities


class TestCriticalChains:
    """The zero-slack SET is not a path; ``critical_chains`` holds the paths."""

    def test_drax_network_has_two_distinct_critical_paths(self) -> None:
        schedule = compute_timeline(DRAX_HIJACK_TIMELINE)
        assert schedule.critical_chains == (
            (
                "infiltrate_launch_tower",
                "assume_ground_control",
                "spoof_telemetry",
                "rendezvous_drax_station",
            ),
            (
                "infiltrate_launch_tower",
                "neutralise_shuttle_crew",
                "launch_shuttle",
                "execute_orbital_insertion",
                "rendezvous_drax_station",
            ),
        )

    def test_every_chain_is_a_real_dependency_route_of_full_length(self) -> None:
        """Each chain must be traversable edge by edge and sum to the total.

        This is what the zero-slack activity *set* fails: two of its
        consecutive entries (``assume_ground_control`` → ``neutralise_shuttle_crew``
        and ``execute_orbital_insertion`` → ``spoof_telemetry``) are not
        dependency edges at all.
        """
        schedule = compute_timeline(DRAX_HIJACK_TIMELINE)
        deps = {a.name: a.depends_on for a in DRAX_HIJACK_TIMELINE}
        durations = {a.name: a.duration_min for a in DRAX_HIJACK_TIMELINE}
        assert schedule.critical_chains
        for chain in schedule.critical_chains:
            for earlier, later in zip(chain[:-1], chain[1:], strict=True):
                assert earlier in deps[later], f"{earlier} -> {later} is not an edge"
            assert sum(durations[name] for name in chain) == pytest.approx(
                schedule.total_duration_min
            )
        # The set really is a union, not one of the chains.
        assert len(schedule.critical_activities) > max(
            len(chain) for chain in schedule.critical_chains
        )

    def test_single_path_network_reports_one_chain(self) -> None:
        network = (
            TimelineActivity("a", 5.0),
            TimelineActivity("b", 3.0, ("a",)),
            TimelineActivity("c", 1.0, ("a",)),
            TimelineActivity("d", 2.0, ("b", "c")),
        )
        schedule = compute_timeline(network)
        assert schedule.critical_chains == (("a", "b", "d"),)
        assert schedule.critical_activities == ("a", "b", "d")

    def test_slack_zero_but_untight_edge_is_not_on_a_path(self) -> None:
        """A zero-slack predecessor that finishes early does not drive its successor.

        ``early`` has zero slack (it is on the a→early→sink route) but the
        ``a -> sink`` edge is slack: ``sink`` starts when ``early`` finishes, so
        only the tight edges appear in the chains.
        """
        network = (
            TimelineActivity("a", 4.0),
            TimelineActivity("early", 6.0, ("a",)),
            TimelineActivity("sink", 2.0, ("a", "early")),
        )
        schedule = compute_timeline(network)
        assert schedule.critical_chains == (("a", "early", "sink"),)


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


class TestNonTupleInput:
    def test_list_of_activities_is_accepted(self) -> None:
        """``compute_timeline`` normalises any sequence to a tuple before solving."""
        activities = [
            TimelineActivity("a", 5.0),
            TimelineActivity("b", 3.0, ("a",)),
        ]
        schedule = compute_timeline(activities)  # type: ignore[arg-type]
        assert schedule.total_duration_min == pytest.approx(8.0)
        assert schedule.critical_activities == ("a", "b")
