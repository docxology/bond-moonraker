"""Tests for moonraker.schedule_crashing — time-cost crashing of the timeline."""

import pytest

from moonraker.schedule_crashing import (
    DRAX_CRASH_OPTIONS,
    CrashableActivity,
    CrashResult,
    activities_by_name,
    crash_schedule,
)


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
