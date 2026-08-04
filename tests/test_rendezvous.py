"""Tests for moonraker.rendezvous — Clohessy–Wiltshire relative motion."""

import math

import pytest

from moonraker.orbital_logistics import EARTH_MU_KM3_S2, EARTH_RADIUS_KM
from moonraker.rendezvous import (
    cw_propagate,
    cw_state_transition,
    mean_motion,
    single_impulse_intercept,
)

N = mean_motion(350.0 + EARTH_RADIUS_KM)
PERIOD = 2.0 * math.pi / N


class TestMeanMotion:
    def test_formula(self) -> None:
        r = 350.0 + EARTH_RADIUS_KM
        assert mean_motion(r) == pytest.approx(math.sqrt(EARTH_MU_KM3_S2 / r**3))

    def test_validation(self) -> None:
        with pytest.raises(ValueError):
            mean_motion(EARTH_RADIUS_KM)
        with pytest.raises(ValueError):
            mean_motion(350.0 + EARTH_RADIUS_KM, mu=0.0)


class TestStateTransition:
    def test_identity_at_t0(self) -> None:
        matrix = cw_state_transition(N, 0.0)
        assert len(matrix) == 6
        for i in range(6):
            for j in range(6):
                expected = 1.0 if i == j else 0.0
                assert matrix[i][j] == pytest.approx(expected)

    def test_deterministic(self) -> None:
        assert cw_state_transition(N, 120.0) == cw_state_transition(N, 120.0)

    def test_validation(self) -> None:
        with pytest.raises(ValueError):
            cw_state_transition(0.0, 10.0)
        with pytest.raises(ValueError):
            cw_state_transition(N, -1.0)


class TestPropagate:
    def test_t0_returns_state(self) -> None:
        state = (1.0, 2.0, 3.0, 0.1, 0.2, 0.3)
        assert cw_propagate(N, 0.0, state) == pytest.approx(state)

    def test_radial_offset_returns_after_period(self) -> None:
        x0 = 1.0
        result = cw_propagate(N, PERIOD, (x0, 0.0, 0.0, 0.0, 0.0, 0.0))
        # After one full period the radial position returns and the along-track
        # position has drifted by the classic -12*pi*x0.
        assert result[0] == pytest.approx(x0)
        assert result[1] == pytest.approx(-12.0 * math.pi * x0)
        assert result[2] == pytest.approx(0.0)

    def test_cross_track_decoupled(self) -> None:
        result = cw_propagate(N, 500.0, (0.0, 0.0, 2.0, 0.0, 0.0, 0.1))
        assert result[0] == pytest.approx(0.0)
        assert result[1] == pytest.approx(0.0)
        assert result[2] != pytest.approx(0.0)

    def test_along_track_offset_frozen(self) -> None:
        result = cw_propagate(N, 400.0, (0.0, 5.0, 0.0, 0.0, 0.0, 0.0))
        assert result[1] == pytest.approx(5.0)

    def test_validation(self) -> None:
        with pytest.raises(ValueError):
            cw_propagate(N, 10.0, (1.0, 2.0))  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            cw_propagate(0.0, 10.0, (0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
        with pytest.raises(ValueError):
            cw_propagate(N, -5.0, (0.0, 0.0, 0.0, 0.0, 0.0, 0.0))


class TestSingleImpulseIntercept:
    def test_round_trip_zeroes_position(self) -> None:
        r0 = (0.5, 2.0, 0.0)
        impulse, v0 = single_impulse_intercept(N, 1200.0, r0)
        assert impulse > 0.0
        final = cw_propagate(N, 1200.0, v0)
        assert final[0] == pytest.approx(0.0, abs=1e-9)
        assert final[1] == pytest.approx(0.0, abs=1e-9)
        assert final[2] == pytest.approx(0.0, abs=1e-9)

    def test_locked_impulse(self) -> None:
        impulse, _ = single_impulse_intercept(N, 1200.0, (0.5, 2.0, 0.0))
        assert impulse == pytest.approx(0.001875, abs=1e-5)

    def test_cross_track_intercept(self) -> None:
        impulse, v0 = single_impulse_intercept(N, 900.0, (0.0, 0.0, 3.0))
        final = cw_propagate(N, 900.0, v0)
        assert final[2] == pytest.approx(0.0, abs=1e-9)
        assert impulse > 0.0

    def test_singular_times_raise(self) -> None:
        # t=0 and full-period geometry have no single-impulse intercept.
        with pytest.raises(ValueError):
            single_impulse_intercept(N, 0.0, (0.5, 2.0, 0.0))
        with pytest.raises(ValueError):
            single_impulse_intercept(N, PERIOD, (0.5, 2.0, 0.0))

    def test_validation(self) -> None:
        with pytest.raises(ValueError):
            single_impulse_intercept(0.0, 100.0, (0.5, 2.0, 0.0))
        with pytest.raises(ValueError):
            single_impulse_intercept(N, -1.0, (0.5, 2.0, 0.0))
        with pytest.raises(ValueError):
            single_impulse_intercept(N, 100.0, (0.5, 2.0))  # type: ignore[arg-type]
