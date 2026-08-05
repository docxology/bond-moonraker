"""Tests for moonraker.schedule_crashing — time-cost crashing of the timeline."""

import pytest

from moonraker.schedule_crashing import (
    DRAX_CRASH_ECONOMICS,
    DRAX_CRASH_OPTIONS,
    CrashableActivity,
    CrashResult,
    _crashable_from_timeline,
    activities_by_name,
    crash_schedule,
)
from moonraker.shuttle_ops import DRAX_HIJACK_TIMELINE, TimelineActivity, compute_timeline


class TestCrashableActivity:
    def test_valid(self) -> None:
        a = CrashableActivity("a", 10.0, 6.0, 2.0)
        assert a.name == "a"

    def test_validation(self) -> None:
        with pytest.raises(ValueError):
            CrashableActivity("  ", 10.0, 6.0, 2.0)
        with pytest.raises(ValueError):
            CrashableActivity("a", 0.0, 0.0, 2.0)
        with pytest.raises(ValueError):
            CrashableActivity("a", 6.0, 10.0, 2.0)  # crash > normal
        with pytest.raises(ValueError):
            CrashableActivity("a", 10.0, 0.0, 2.0)  # crash <= 0
        with pytest.raises(ValueError):
            CrashableActivity("a", 10.0, 6.0, -1.0)
        with pytest.raises(ValueError):
            CrashableActivity("a", 10.0, 6.0, 2.0, ["b"])  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            CrashableActivity("a", 10.0, 6.0, 2.0, (" ",))


class TestCrashSchedule:
    def test_serial_network_exact(self) -> None:
        network = (
            CrashableActivity("a", 5.0, 3.0, 2.0),
            CrashableActivity("b", 3.0, 2.0, 4.0, ("a",)),
        )
        result = crash_schedule(network, 6.0)
        assert result.original_duration_min == pytest.approx(8.0)
        assert result.final_duration_min == pytest.approx(6.0)
        assert result.feasible is True
        assert result.total_cost == pytest.approx(4.0)
        assert result.crashed == {"a": 2.0}

    def test_no_crash_needed(self) -> None:
        result = crash_schedule(DRAX_CRASH_OPTIONS, 57.0)
        assert result.feasible is True
        assert result.total_cost == 0.0
        assert result.crashed == {}
        assert result.final_duration_min == pytest.approx(57.0)

    def test_drax_to_50_locked(self) -> None:
        result = crash_schedule(DRAX_CRASH_OPTIONS, 50.0)
        assert result.original_duration_min == pytest.approx(57.0)
        assert result.final_duration_min == pytest.approx(50.0)
        assert result.feasible is True
        assert result.total_cost == pytest.approx(23.0)
        assert set(result.crashed) == {
            "infiltrate_launch_tower",
            "neutralise_shuttle_crew",
            "spoof_telemetry",
        }
        assert result.crashed["infiltrate_launch_tower"] == pytest.approx(4.0)
        assert result.crashed["neutralise_shuttle_crew"] == pytest.approx(3.0)
        assert result.crashed["spoof_telemetry"] == pytest.approx(3.0)

    def test_infeasible_deadline(self) -> None:
        result = crash_schedule(DRAX_CRASH_OPTIONS, 40.0)
        assert result.feasible is False
        assert result.final_duration_min > 40.0

    def test_cost_never_decreases_with_tighter_deadline(self) -> None:
        loose = crash_schedule(DRAX_CRASH_OPTIONS, 52.0)
        tight = crash_schedule(DRAX_CRASH_OPTIONS, 50.0)
        assert tight.total_cost >= loose.total_cost
        assert tight.final_duration_min <= loose.final_duration_min

    def test_deterministic(self) -> None:
        assert crash_schedule(DRAX_CRASH_OPTIONS, 50.0) == crash_schedule(DRAX_CRASH_OPTIONS, 50.0)

    def test_validation(self) -> None:
        with pytest.raises(ValueError):
            crash_schedule((), 50.0)
        with pytest.raises(ValueError):
            crash_schedule(DRAX_CRASH_OPTIONS, 0.0)
        with pytest.raises(ValueError):
            crash_schedule(
                (
                    CrashableActivity("a", 5.0, 3.0, 2.0),
                    CrashableActivity("a", 4.0, 2.0, 1.0),
                ),
                6.0,
            )


class TestCrashNetworkMirrorsTheTimeline:
    """The crashable network is derived from the timeline, not hand-copied.

    Before this, ``DRAX_CRASH_OPTIONS`` re-typed all eight durations and every
    dependency edge of ``DRAX_HIJACK_TIMELINE``, and nothing compared them —
    while the manuscript subtracts one network's total (57 min) from the
    other's crashed total (50 min).
    """

    def test_durations_and_edges_come_from_the_canonical_timeline(self) -> None:
        timeline = {a.name: a for a in DRAX_HIJACK_TIMELINE}
        assert {a.name for a in DRAX_CRASH_OPTIONS} == set(timeline)
        for crashable in DRAX_CRASH_OPTIONS:
            source = timeline[crashable.name]
            assert crashable.normal_duration_min == pytest.approx(source.duration_min)
            assert crashable.depends_on == source.depends_on

    def test_uncrashed_totals_agree(self) -> None:
        """The subtraction the manuscript performs must be within one network."""
        assert crash_schedule(DRAX_CRASH_OPTIONS, 999.0).original_duration_min == pytest.approx(
            compute_timeline(DRAX_HIJACK_TIMELINE).total_duration_min
        )

    def test_missing_economics_entry_is_refused(self) -> None:
        """An activity added to the timeline with no crash data must not slip through."""
        extended = (*DRAX_HIJACK_TIMELINE, TimelineActivity("plant_charges", 5.0))
        with pytest.raises(ValueError, match="missing="):
            _crashable_from_timeline(extended, DRAX_CRASH_ECONOMICS)

    def test_stale_economics_entry_is_refused(self) -> None:
        """Crash data left behind for a deleted activity must not slip through."""
        with pytest.raises(ValueError, match="unknown="):
            _crashable_from_timeline(
                DRAX_HIJACK_TIMELINE, {**DRAX_CRASH_ECONOMICS, "ghost_phase": (1.0, 1.0)}
            )


class TestHelpers:
    def test_activities_by_name(self) -> None:
        activity = activities_by_name(DRAX_CRASH_OPTIONS, "launch_shuttle")
        assert activity.cost_per_min == pytest.approx(5.0)

    def test_unknown_name_raises(self) -> None:
        with pytest.raises(KeyError):
            activities_by_name(DRAX_CRASH_OPTIONS, "ghost")

    def test_crash_result_validation(self) -> None:
        with pytest.raises(ValueError):
            CrashResult(57.0, 50.0, 23.0, [], True, ())  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            CrashResult(-1.0, 50.0, 23.0, {}, True, ())
        with pytest.raises(ValueError):
            CrashResult(57.0, 50.0, 23.0, {}, "yes", ())  # type: ignore[arg-type]
