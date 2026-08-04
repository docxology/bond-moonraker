"""Tests for moonraker.orbital_logistics — Drax station orbital logistics."""

import math

import pytest

from moonraker.orbital_logistics import (
    EARTH_MU_KM3_S2,
    EARTH_RADIUS_KM,
    SIDEREAL_DAY_S,
    LaunchWindow,
    circular_speed,
    consumables_days,
    depletion_day,
    launch_windows,
    orbital_period,
    orbits_per_day,
    pass_duration,
    resupply_interval,
    sustainable_crew,
    visibility_half_angle,
)


class TestOrbitalPeriod:
    def test_kepler_formula(self) -> None:
        h = 400.0
        a = h + EARTH_RADIUS_KM
        expected = 2.0 * math.pi * math.sqrt(a**3 / EARTH_MU_KM3_S2)
        assert orbital_period(400.0) == pytest.approx(expected)

    def test_increases_with_altitude(self) -> None:
        assert orbital_period(300.0) < orbital_period(1000.0)

    def test_invalid_altitude_raises(self) -> None:
        with pytest.raises(ValueError):
            orbital_period(0.0)
        with pytest.raises(ValueError):
            orbital_period(-1.0)
        with pytest.raises(ValueError):
            orbital_period(400.0, r_earth=0.0)
        with pytest.raises(ValueError):
            orbital_period(400.0, mu=0.0)


class TestCircularSpeed:
    def test_kepler_speed(self) -> None:
        a = 350.0 + EARTH_RADIUS_KM
        assert circular_speed(350.0) == pytest.approx(math.sqrt(EARTH_MU_KM3_S2 / a))

    def test_invalid_altitude_raises(self) -> None:
        with pytest.raises(ValueError):
            circular_speed(-3.0)


class TestOrbitsPerDay:
    def test_known_value(self) -> None:
        period = orbital_period(350.0)
        assert orbits_per_day(350.0) == pytest.approx(SIDEREAL_DAY_S / period)

    def test_invalid_sidereal_day_raises(self) -> None:
        with pytest.raises(ValueError):
            orbits_per_day(350.0, sidereal_day_s=0.0)


class TestVisibility:
    def test_half_angle_increases_with_altitude(self) -> None:
        # Higher altitude -> smaller R/(R+h) -> larger horizon half-angle.
        low = visibility_half_angle(200.0)
        high = visibility_half_angle(2000.0)
        assert high > low > 0.0

    def test_pass_duration_positive_and_wider_at_higher_altitude(self) -> None:
        d_low = pass_duration(300.0)
        d_high = pass_duration(800.0)
        assert d_low > 0.0
        assert d_high > d_low  # higher station stays visible for longer

    def test_pass_duration_elevation_threshold(self) -> None:
        assert pass_duration(400.0, elevation_threshold_deg=0.0) > pass_duration(
            400.0, elevation_threshold_deg=30.0
        )

    def test_invalid_elevation_raises(self) -> None:
        with pytest.raises(ValueError):
            pass_duration(400.0, elevation_threshold_deg=90.0)
        with pytest.raises(ValueError):
            pass_duration(400.0, elevation_threshold_deg=-1.0)

    def test_invalid_altitude_raises(self) -> None:
        with pytest.raises(ValueError):
            visibility_half_angle(-1.0)


class TestLaunchWindow:
    def test_validation(self) -> None:
        assert LaunchWindow(0.0, 10.0).close_s == 10.0
        with pytest.raises(ValueError):
            LaunchWindow(-1.0, 10.0)
        with pytest.raises(ValueError):
            LaunchWindow(5.0, 5.0)

    def test_windows_spacing_and_duration(self) -> None:
        period = orbital_period(350.0)
        windows = launch_windows(350.0, num_windows=4)
        assert len(windows) == 4
        for i, w in enumerate(windows):
            assert w.open_s == pytest.approx(i * period / 2.0)
            assert (w.close_s - w.open_s) == pytest.approx(pass_duration(350.0))

    def test_deterministic(self) -> None:
        assert launch_windows(350.0, num_windows=3) == launch_windows(350.0, num_windows=3)

    def test_invalid_args_raise(self) -> None:
        with pytest.raises(ValueError):
            launch_windows(350.0, num_windows=0)
        with pytest.raises(ValueError):
            launch_windows(350.0, num_windows=1, epoch_s=-1.0)
        with pytest.raises(ValueError):
            launch_windows(-1.0, num_windows=1)


class TestConsumables:
    def test_consumables_days_formula(self) -> None:
        assert consumables_days(5400.0, 6, 2.0) == pytest.approx(450.0)

    def test_zero_crew_infinite(self) -> None:
        assert consumables_days(5400.0, 0, 2.0) == math.inf

    def test_depletion_day_equals_consumables(self) -> None:
        assert depletion_day(5400.0, 6, 2.0) == consumables_days(5400.0, 6, 2.0)

    def test_sustainable_crew(self) -> None:
        # capacity / (interval * rate) = 5400 / (6*2) = 450
        assert sustainable_crew(5400.0, 6.0, 2.0) == 450

    def test_resupply_interval_equals_consumables(self) -> None:
        assert resupply_interval(5400.0, 6, 2.0) == pytest.approx(450.0)

    def test_invalid_inputs_raise(self) -> None:
        with pytest.raises(ValueError):
            consumables_days(-1.0, 6, 2.0)
        with pytest.raises(ValueError):
            consumables_days(5400.0, 6, 0.0)
        with pytest.raises(ValueError):
            consumables_days(5400.0, -1, 2.0)
        with pytest.raises(ValueError):
            sustainable_crew(5400.0, 0.0, 2.0)
        with pytest.raises(ValueError):
            sustainable_crew(5400.0, 6.0, -1.0)
        with pytest.raises(ValueError):
            consumables_days(5400.0, True, 2.0)
