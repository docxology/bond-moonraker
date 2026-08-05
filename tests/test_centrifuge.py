"""Tests for moonraker.centrifuge — g-force profile modelling."""

import math

import pytest

from moonraker.centrifuge import (
    G0_MS2,
    TrainingProfile,
    build_training_profile,
    g_from_rpm,
    max_sustained_duration,
    profile_is_safe,
    rpm_for_g,
)


class TestGFromRpm:
    def test_known_value(self) -> None:
        # 1 g on an 8 m arm: rpm = sqrt(g*g0/r) * 60/(2pi)
        rpm = rpm_for_g(1.0, 8.0)
        assert g_from_rpm(rpm, 8.0) == pytest.approx(1.0, abs=1e-9)

    def test_zero_rpm_zero_g(self) -> None:
        assert g_from_rpm(0.0, 8.0) == pytest.approx(0.0)

    def test_invalid_radius_raises(self) -> None:
        with pytest.raises(ValueError):
            g_from_rpm(10.0, 0.0)
        with pytest.raises(ValueError):
            g_from_rpm(10.0, -1.0)
        with pytest.raises(ValueError):
            g_from_rpm(-1.0, 8.0)

    def test_rpm_for_g_inverse(self) -> None:
        for g in (3.0, 6.0, 9.0):
            r = rpm_for_g(g, 8.0)
            assert g_from_rpm(r, 8.0) == pytest.approx(g, rel=1e-9)

    def test_rpm_for_g_validation(self) -> None:
        with pytest.raises(ValueError):
            rpm_for_g(-1.0, 8.0)
        with pytest.raises(ValueError):
            rpm_for_g(6.0, 0.0)
        # RPM consistency with the g equation.
        assert rpm_for_g(6.0, 8.0) == pytest.approx(
            (60 / (2 * math.pi)) * math.sqrt(6 * G0_MS2 / 8.0)
        )


class TestMaxSustainedDuration:
    def test_zero_g_returns_ceiling(self) -> None:
        assert max_sustained_duration(0.0) == pytest.approx(60.0)

    def test_monotonically_decreasing(self) -> None:
        assert (
            max_sustained_duration(3.0) > max_sustained_duration(6.0) > max_sustained_duration(9.0)
        )

    def test_formula_at_6g(self) -> None:
        assert max_sustained_duration(6.0) == pytest.approx(min(800.0 * 6.0**-2.5, 60.0))

    def test_validation(self) -> None:
        with pytest.raises(ValueError):
            max_sustained_duration(-1.0)
        with pytest.raises(ValueError):
            max_sustained_duration(6.0, ceiling_s=0.0)
        with pytest.raises(ValueError):
            max_sustained_duration(6.0, scale=0.0)


class TestBuildTrainingProfile:
    def test_ramp_sustain_decay_shape(self) -> None:
        profile = build_training_profile(
            target_g=6.0,
            radius_m=8.0,
            sustain_s=12.0,
            ramp_rate_g_per_s=0.5,
            decay_rate_g_per_s=1.0,
        )
        assert profile.peak_g == pytest.approx(6.0)
        assert profile.time_s[0] == pytest.approx(0.0)
        assert profile.g_levels[0] == pytest.approx(0.0)
        # Peak is reached during the plateau.
        assert max(profile.g_levels) == pytest.approx(6.0, abs=0.6)
        # Final sample returns to ~0.
        assert profile.g_levels[-1] < 0.5
        # Ramp takes 12 s at 0.5 g/s to reach 6 g; plateau 12 s; decay 6 s -> 30 s.
        assert profile.time_s[-1] == pytest.approx(30.0, abs=3.0)

    def test_deterministic(self) -> None:
        p1 = build_training_profile(target_g=6.0, radius_m=8.0, sustain_s=12.0)
        p2 = build_training_profile(target_g=6.0, radius_m=8.0, sustain_s=12.0)
        assert p1 == p2

    def test_validation(self) -> None:
        with pytest.raises(ValueError):
            build_training_profile(target_g=6.0, radius_m=0.0, sustain_s=12.0)  # bad radius
        with pytest.raises(ValueError):
            build_training_profile(
                target_g=6.0, radius_m=8.0, sustain_s=12.0, ramp_rate_g_per_s=0.0
            )
        with pytest.raises(ValueError):
            build_training_profile(
                target_g=6.0, radius_m=8.0, sustain_s=12.0, decay_rate_g_per_s=0.0
            )
        with pytest.raises(ValueError):
            build_training_profile(target_g=6.0, radius_m=8.0, sustain_s=12.0, sample_rate_hz=0.0)
        with pytest.raises(ValueError):
            build_training_profile(target_g=-1.0, radius_m=8.0, sustain_s=12.0)


class TestTrainingProfileDataclass:
    def test_length_mismatch_raises(self) -> None:
        with pytest.raises(ValueError):
            TrainingProfile((0.0, 1.0), (0.0,), 1.0, 1.0)

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            TrainingProfile((), (), 1.0, 1.0)

    def test_negative_sample_raises(self) -> None:
        with pytest.raises(ValueError):
            TrainingProfile((0.0, -1.0), (0.0, 1.0), 1.0, 1.0)


class TestProfileIsSafe:
    def test_safe_profile(self) -> None:
        profile = build_training_profile(target_g=6.0, radius_m=8.0, sustain_s=2.0)
        safe, metrics = profile_is_safe(profile, g_limit=9.0, duration_limit_s=30.0)
        assert safe is True
        assert metrics["peak_g"] == pytest.approx(6.0)

    def test_over_peak_g_unsafe(self) -> None:
        profile = build_training_profile(target_g=10.0, radius_m=8.0, sustain_s=2.0)
        safe, _ = profile_is_safe(profile, g_limit=9.0, duration_limit_s=30.0)
        assert safe is False

    def test_over_sustain_unsafe(self) -> None:
        # Very high g has a tiny allowable duration, so a 12 s plateau is unsafe.
        profile = build_training_profile(target_g=9.0, radius_m=8.0, sustain_s=12.0)
        safe, metrics = profile_is_safe(profile, g_limit=9.0, duration_limit_s=30.0)
        assert safe is False
        assert metrics["allowable_s"] < metrics["sustain_s"]

    def test_procedural_duration_limit_binds(self) -> None:
        """``duration_limit_s`` must be able to fail a physiologically-fine run.

        At 1 g the tolerance envelope saturates at its 60 s ceiling (48 s after
        the 20% margin), so a 10 s plateau clears physiology outright. Only the
        procedural ceiling can reject it: with a 5 s limit the run is refused,
        with a 30 s limit it passes. Both allowances equal the procedural limit,
        proving it — not the envelope — governs here.
        """
        profile = build_training_profile(target_g=1.0, radius_m=8.0, sustain_s=10.0)
        tight, tight_metrics = profile_is_safe(profile, g_limit=9.0, duration_limit_s=5.0)
        assert tight is False
        assert tight_metrics["allowable_s"] == pytest.approx(5.0)

        loose, loose_metrics = profile_is_safe(profile, g_limit=9.0, duration_limit_s=30.0)
        assert loose is True
        assert loose_metrics["allowable_s"] == pytest.approx(30.0)

    def test_canonical_drax_profile_is_not_certified(self) -> None:
        """The shipped 6 g / 12 s DRAX profile overruns its tolerance allowance.

        Pinned deliberately: the manuscript reports this verdict through a
        token, and a silent flip (either direction) must break a test rather
        than quietly contradict the prose.
        """
        profile = build_training_profile(
            target_g=6.0, radius_m=8.0, sustain_s=12.0, ramp_rate_g_per_s=0.5
        )
        safe, metrics = profile_is_safe(profile, g_limit=9.0, duration_limit_s=30.0)
        assert safe is False
        assert metrics["allowable_s"] == pytest.approx(7.26, abs=0.01)
        assert metrics["sustain_s"] == pytest.approx(12.0)

    def test_validation(self) -> None:
        profile = build_training_profile(target_g=6.0, radius_m=8.0, sustain_s=2.0)
        with pytest.raises(ValueError):
            profile_is_safe(profile, g_limit=0.0, duration_limit_s=30.0)
        with pytest.raises(ValueError):
            profile_is_safe(profile, g_limit=9.0, duration_limit_s=0.0)
        with pytest.raises(ValueError):
            profile_is_safe(profile, g_limit=9.0, duration_limit_s=30.0, margin_fraction=1.5)
