"""Tests for moonraker.centrifuge_training — regimen planning and exposure."""

import pytest

from moonraker.centrifuge import TrainingProfile, build_training_profile
from moonraker.centrifuge_training import (
    TrainingCycle,
    exposure_g_seconds,
    gor_tolerance_multiplier,
    max_sessions_for_cap,
    plan_training_cycle,
    profile_exposure,
)


class TestGorToleranceMultiplier:
    def test_monotone_in_onset_rate(self) -> None:
        slow = gor_tolerance_multiplier(0.2)
        fast = gor_tolerance_multiplier(2.0)
        assert slow > fast

    def test_known_values(self) -> None:
        assert gor_tolerance_multiplier(0.5) == pytest.approx(1.7)
        assert gor_tolerance_multiplier(2.0) == pytest.approx(1.175)

    def test_clamps(self) -> None:
        assert gor_tolerance_multiplier(0.001) == pytest.approx(2.5)  # ceiling
        assert gor_tolerance_multiplier(1000.0) == pytest.approx(1.0, abs=1e-3)  # ~1, above floor
        assert gor_tolerance_multiplier(0.5, floor=2.0) == pytest.approx(2.0)  # floor

    def test_validation(self) -> None:
        with pytest.raises(ValueError):
            gor_tolerance_multiplier(0.0)
        with pytest.raises(ValueError):
            gor_tolerance_multiplier(0.5, k=-1.0)
        with pytest.raises(ValueError):
            gor_tolerance_multiplier(0.5, floor=0.0)
        with pytest.raises(ValueError):
            gor_tolerance_multiplier(0.5, floor=3.0, ceiling=2.0)


class TestExposure:
    def test_constant_profile(self) -> None:
        assert exposure_g_seconds((2.0, 2.0, 2.0), dt_s=1.0) == pytest.approx(3.0)
        assert exposure_g_seconds((0.5, 0.5), dt_s=10.0) == pytest.approx(0.0)  # below baseline

    def test_custom_baseline(self) -> None:
        assert exposure_g_seconds((3.0, 3.0), dt_s=2.0, baseline_g=2.0) == pytest.approx(4.0)

    def test_deterministic(self) -> None:
        assert exposure_g_seconds((1.5, 2.5), dt_s=1.0) == exposure_g_seconds((1.5, 2.5), dt_s=1.0)

    def test_validation(self) -> None:
        with pytest.raises(ValueError):
            exposure_g_seconds((), dt_s=1.0)
        with pytest.raises(ValueError):
            exposure_g_seconds((1.0,), dt_s=0.0)
        with pytest.raises(ValueError):
            exposure_g_seconds((1.0,), dt_s=-1.0)
        with pytest.raises(ValueError):
            exposure_g_seconds((-1.0, 1.0), dt_s=1.0)
        with pytest.raises(ValueError):
            exposure_g_seconds((1.0,), dt_s=1.0, baseline_g=-0.1)


class TestProfileExposure:
    def test_matches_sample_integral(self) -> None:
        profile = build_training_profile(
            target_g=6.0,
            radius_m=8.0,
            sustain_s=12.0,
            ramp_rate_g_per_s=0.5,
            decay_rate_g_per_s=1.0,
        )
        dt = profile.time_s[1] - profile.time_s[0]
        assert profile_exposure(profile) == pytest.approx(
            exposure_g_seconds(profile.g_levels, dt_s=dt)
        )
        # Locked value.
        assert profile_exposure(profile) == pytest.approx(97.5, abs=0.6)

    def test_validation(self) -> None:
        with pytest.raises(ValueError):
            profile_exposure("not a profile")  # type: ignore[arg-type]
        one_sample = TrainingProfile((0.0,), (0.0,), 0.0, 0.0)
        with pytest.raises(ValueError):
            profile_exposure(one_sample)


class TestMaxSessions:
    def test_floor(self) -> None:
        assert max_sessions_for_cap(107.5, 400.0) == 3
        assert max_sessions_for_cap(97.5, 400.0) == 4

    def test_validation(self) -> None:
        with pytest.raises(ValueError):
            max_sessions_for_cap(0.0, 400.0)
        with pytest.raises(ValueError):
            max_sessions_for_cap(107.5, 0.0)


class TestTrainingCycle:
    def test_feasible_plan(self) -> None:
        cycle = plan_training_cycle(97.5, 150.0, 400.0, 4)
        assert cycle.feasible is True
        assert cycle.weekly_exposure_g_s == pytest.approx(390.0)
        assert cycle.recommended_sessions == 4

    def test_weekly_cap_violation_infeasible(self) -> None:
        cycle = plan_training_cycle(107.5, 150.0, 400.0, 4)
        assert cycle.feasible is False
        assert cycle.recommended_sessions == 3

    def test_daily_cap_violation_infeasible(self) -> None:
        cycle = plan_training_cycle(200.0, 150.0, 800.0, 1)
        assert cycle.feasible is False

    def test_zero_sessions_feasible(self) -> None:
        cycle = plan_training_cycle(97.5, 150.0, 400.0, 0)
        assert cycle.feasible is True
        assert cycle.weekly_exposure_g_s == pytest.approx(0.0)

    def test_deterministic(self) -> None:
        assert plan_training_cycle(97.5, 150.0, 400.0, 4) == plan_training_cycle(
            97.5, 150.0, 400.0, 4
        )

    def test_validation(self) -> None:
        with pytest.raises(ValueError):
            plan_training_cycle(0.0, 150.0, 400.0, 1)
        with pytest.raises(ValueError):
            plan_training_cycle(97.5, 0.0, 400.0, 1)
        with pytest.raises(ValueError):
            plan_training_cycle(97.5, 150.0, 0.0, 1)
        with pytest.raises(ValueError):
            plan_training_cycle(97.5, 150.0, 400.0, -1)

    def test_dataclass_validation(self) -> None:
        with pytest.raises(ValueError):
            TrainingCycle(-1, 97.5, -97.5, 150.0, 400.0, 4, True)
        with pytest.raises(ValueError):
            TrainingCycle(4, -1.0, 0.0, 150.0, 400.0, 4, True)


class TestValidationEdges:
    def test_bad_ceiling_is_rejected_before_use(self) -> None:
        """A non-numeric or non-positive ceiling must raise ValueError, not TypeError.

        The ceiling is compared against in the floor check, so it has to be
        validated first; otherwise a string ceiling escapes as a TypeError.
        """
        with pytest.raises(ValueError):
            gor_tolerance_multiplier(0.5, ceiling=0.0)
        with pytest.raises(ValueError):
            gor_tolerance_multiplier(0.5, ceiling="high")  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            gor_tolerance_multiplier(0.5, floor=3.0, ceiling=2.0)

    def test_non_increasing_time_samples_rejected(self) -> None:
        """A hand-built profile whose samples do not advance has no dt to dose."""
        stalled = TrainingProfile(
            time_s=(0.0, 0.0), g_levels=(1.0, 2.0), peak_g=2.0, sustain_duration_s=0.0
        )
        with pytest.raises(ValueError, match="strictly increasing"):
            profile_exposure(stalled)
