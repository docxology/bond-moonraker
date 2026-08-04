"""Tests for moonraker.orbital_transfer — Hohmann, rocket equation, deorbit."""

import math

import pytest

from moonraker.orbital_logistics import EARTH_MU_KM3_S2, EARTH_RADIUS_KM
from moonraker.orbital_transfer import (
    deorbit_dv,
    hohmann_transfer,
    phase_wait_time,
    propellant_fraction,
    propellant_mass,
    tsiolkovsky_mass_ratio,
    vis_viva,
)

R1 = 200.0 + EARTH_RADIUS_KM
R2 = 350.0 + EARTH_RADIUS_KM


class TestVisViva:
    def test_circular_consistency(self) -> None:
        for r in (R1, R2):
            assert vis_viva(r, r) == pytest.approx(math.sqrt(EARTH_MU_KM3_S2 / r))

    def test_transfer_speed_between_circular_speeds(self) -> None:
        a = (R1 + R2) / 2.0
        v_circ_low = vis_viva(R1, R1)
        v_transfer_low = vis_viva(R1, a)
        assert (
            v_transfer_low > v_circ_low
        )  # raised orbit is slower at perigee? no: perigee speed > circular
        v_circ_high = vis_viva(R2, R2)
        v_transfer_high = vis_viva(R2, a)
        assert v_transfer_high < v_circ_high  # apogee speed < circular at target

    def test_validation(self) -> None:
        with pytest.raises(ValueError):
            vis_viva(0.0, R1)
        with pytest.raises(ValueError):
            vis_viva(R1, 0.0)
        with pytest.raises(ValueError):
            vis_viva(R1, R1, mu=0.0)
        with pytest.raises(ValueError):
            vis_viva(R1, R1 / 4.0)  # semi-major too small to reach r


class TestHohmannTransfer:
    def test_known_raise(self) -> None:
        transfer = hohmann_transfer(R1, R2)
        a = (R1 + R2) / 2.0
        assert transfer.dv1_km_s == pytest.approx(vis_viva(R1, a) - vis_viva(R1, R1))
        assert transfer.dv2_km_s == pytest.approx(vis_viva(R2, R2) - vis_viva(R2, a))
        assert transfer.total_dv_km_s == pytest.approx(transfer.dv1_km_s + transfer.dv2_km_s)
        assert transfer.transfer_time_s == pytest.approx(
            math.pi * math.sqrt(a**3 / EARTH_MU_KM3_S2)
        )
        assert transfer.semi_major_km == pytest.approx(a)
        # Locked physical values (200 km -> 350 km).
        assert transfer.dv1_km_s == pytest.approx(0.04382, abs=1e-4)
        assert transfer.dv2_km_s == pytest.approx(0.04358, abs=1e-4)
        assert transfer.total_dv_km_s == pytest.approx(0.0874, abs=1e-4)
        assert transfer.transfer_time_s == pytest.approx(2696.0, abs=1.0)

    def test_inward_transfer_symmetric(self) -> None:
        up = hohmann_transfer(R1, R2)
        down = hohmann_transfer(R2, R1)
        assert down.total_dv_km_s == pytest.approx(up.total_dv_km_s)
        assert down.transfer_time_s == pytest.approx(up.transfer_time_s)

    def test_deterministic(self) -> None:
        assert hohmann_transfer(R1, R2) == hohmann_transfer(R1, R2)

    def test_validation(self) -> None:
        with pytest.raises(ValueError):
            hohmann_transfer(R1, R1)  # identical orbits
        with pytest.raises(ValueError):
            hohmann_transfer(100.0, R2)  # below the surface
        with pytest.raises(ValueError):
            hohmann_transfer(R1, R2, mu=0.0)


class TestPhaseWaitTime:
    def test_known_wait(self) -> None:
        wait, lead = phase_wait_time(R1, R2, 0.0)
        n1 = math.sqrt(EARTH_MU_KM3_S2 / R1**3)
        n2 = math.sqrt(EARTH_MU_KM3_S2 / R2**3)
        t_transfer = hohmann_transfer(R1, R2).transfer_time_s
        expected_lead = (math.pi - n2 * t_transfer) % (2.0 * math.pi)
        assert lead == pytest.approx(expected_lead)
        expected_wait = ((0.0 - expected_lead) % (2.0 * math.pi)) / (n1 - n2)
        assert wait == pytest.approx(expected_wait)
        # Locked values.
        assert wait == pytest.approx(157909.7, rel=1e-3)
        assert math.degrees(lead) == pytest.approx(3.0045, abs=1e-2)

    def test_zero_wait_at_lead_angle(self) -> None:
        lead = lead_of(R1, R2)
        wait, _ = phase_wait_time(R1, R2, lead)
        assert wait == pytest.approx(0.0, abs=1e-6)

    def test_validation(self) -> None:
        with pytest.raises(ValueError):
            phase_wait_time(R2, R1, 0.0)  # chaser not in lower orbit
        with pytest.raises(ValueError):
            phase_wait_time(R1, R2, -0.1)
        with pytest.raises(ValueError):
            phase_wait_time(R1, R2, 2.0 * math.pi)
        with pytest.raises(ValueError):
            phase_wait_time(R1, R2, 0.0, mu=0.0)
        with pytest.raises(ValueError):
            phase_wait_time(100.0, R2, 0.0)


def lead_of(r_low: float, r_high: float) -> float:
    """Recompute the Hohmann lead angle for a phase-angle target."""
    n2 = math.sqrt(EARTH_MU_KM3_S2 / r_high**3)
    t_transfer = hohmann_transfer(r_low, r_high).transfer_time_s
    return (math.pi - n2 * t_transfer) % (2.0 * math.pi)


class TestRocketEquation:
    def test_zero_dv_unit_ratio(self) -> None:
        assert tsiolkovsky_mass_ratio(0.0, 300.0) == pytest.approx(1.0)
        assert propellant_fraction(0.0, 300.0) == pytest.approx(0.0)

    def test_known_ratio(self) -> None:
        dv = hohmann_transfer(R1, R2).total_dv_km_s
        ratio = tsiolkovsky_mass_ratio(dv, 300.0)
        assert ratio == pytest.approx(math.exp(dv / (300.0 * 9.80665e-3)))
        assert propellant_fraction(dv, 300.0) == pytest.approx(1.0 - 1.0 / ratio)
        # Locked values.
        assert ratio == pytest.approx(1.0302, abs=1e-3)
        assert propellant_mass(dv, 300.0, 7900.0) == pytest.approx(238.2, abs=0.5)

    def test_monotone_in_dv(self) -> None:
        assert tsiolkovsky_mass_ratio(0.5, 300.0) > tsiolkovsky_mass_ratio(0.1, 300.0)

    def test_validation(self) -> None:
        with pytest.raises(ValueError):
            tsiolkovsky_mass_ratio(-1.0, 300.0)
        with pytest.raises(ValueError):
            tsiolkovsky_mass_ratio(0.1, 0.0)
        with pytest.raises(ValueError):
            tsiolkovsky_mass_ratio(0.1, 300.0, g0_km_s2=0.0)
        with pytest.raises(ValueError):
            propellant_mass(0.1, 300.0, 0.0)


class TestDeorbit:
    def test_known_deorbit(self) -> None:
        dv = deorbit_dv(R2, 100.0 + EARTH_RADIUS_KM)
        assert dv > 0.0
        assert dv == pytest.approx(0.07332, abs=1e-4)

    def test_smaller_perigee_needs_more_dv(self) -> None:
        shallow = deorbit_dv(R2, 300.0 + EARTH_RADIUS_KM)
        deep = deorbit_dv(R2, 100.0 + EARTH_RADIUS_KM)
        assert deep > shallow

    def test_validation(self) -> None:
        with pytest.raises(ValueError):
            deorbit_dv(R2, R2)  # perigee not below circular orbit
        with pytest.raises(ValueError):
            deorbit_dv(R2, 100.0 + EARTH_RADIUS_KM, mu=0.0)
        with pytest.raises(ValueError):
            deorbit_dv(100.0, 100.0 + EARTH_RADIUS_KM)
