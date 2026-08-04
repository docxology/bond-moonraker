"""Clohessy–Wiltshire rendezvous guidance for the DRAX intercept.

The final approach of a chaser craft to the DRAX station is modelled in the
station's local-vertical/local-horizontal (LVLH) frame using the linearised
relative-motion equations of Clohessy & Wiltshire. The state is a 6-tuple
``(x, y, z, vx, vy, vz)`` where ``x`` is radial (outward), ``y`` along-track
(in the velocity direction) and ``z`` cross-track; velocities are the relative
rates. All motion is a closed-form function of the reference orbit's mean
motion ``n = sqrt(mu / r^3)``:

* :func:`cw_state_transition` — the 6x6 state-transition matrix at time ``t``.
* :func:`cw_propagate` — propagate an initial state forward by ``t`` seconds.
* :func:`single_impulse_intercept` — solve for the single corrective impulse
  at ``t=0`` that drives the relative position to zero at time ``t`` (a
  closed-form 3x3 solve), raising on the geometric singularities where no such
  single-impulse intercept exists.

The module is infrastructure-free (stdlib ``math`` only) and deterministic.
"""

from __future__ import annotations

import math

from .orbital_logistics import EARTH_MU_KM3_S2, EARTH_RADIUS_KM

__all__ = [
    "CWState",
    "cw_state_transition",
    "cw_propagate",
    "single_impulse_intercept",
    "mean_motion",
]

#: A relative state in the LVLH frame (x, y, z, vx, vy, vz).
CWState = tuple[float, float, float, float, float, float]

#: Numerical guard for singular-intercept geometry.
_EPS = 1e-12


def mean_motion(r_km: float, mu: float = EARTH_MU_KM3_S2) -> float:
    """Return the circular-orbit mean motion ``n = sqrt(mu / r^3)`` (rad/s)."""
    if not (isinstance(r_km, (int, float)) and r_km > EARTH_RADIUS_KM):
        raise ValueError(f"r_km must be above the Earth's surface (got {r_km!r})")
    if not (isinstance(mu, (int, float)) and mu > 0):
        raise ValueError(f"mu must be > 0 (got {mu!r})")
    return float(math.sqrt(mu / r_km**3))


def _cw_transition(n: float, t: float) -> tuple[CWState, ...]:
    """Return the CW state propagated from the unit basis states.

    Implements the closed-form Clohessy–Wiltshire solution evaluated at time
    ``t`` for each initial-basis state, yielding the six columns of the state
    transition matrix.
    """
    c = math.cos(n * t)
    s = math.sin(n * t)
    nt = n * t

    def column(x0: float, y0: float, z0: float, vx0: float, vy0: float, vz0: float) -> CWState:
        return (
            (4 - 3 * c) * x0 + (s / n) * vx0 + (2 * (1 - c) / n) * vy0,
            6 * (s - nt) * x0 + y0 - (2 * (1 - c) / n) * vx0 + ((4 * s - 3 * nt) / n) * vy0,
            c * z0 + (s / n) * vz0,
            3 * n * s * x0 + c * vx0 + 2 * s * vy0,
            6 * n * (c - 1) * x0 - 2 * s * vx0 + (4 * c - 3) * vy0,
            -n * s * z0 + c * vz0,
        )

    cols = (
        column(1, 0, 0, 0, 0, 0),
        column(0, 1, 0, 0, 0, 0),
        column(0, 0, 1, 0, 0, 0),
        column(0, 0, 0, 1, 0, 0),
        column(0, 0, 0, 0, 1, 0),
        column(0, 0, 0, 0, 0, 1),
    )
    return tuple(
        (cols[0][i], cols[1][i], cols[2][i], cols[3][i], cols[4][i], cols[5][i]) for i in range(6)
    )


def cw_state_transition(n: float, t: float) -> tuple[CWState, ...]:
    """Return the 6x6 Clohessy–Wiltshire state-transition matrix at time ``t``.

    Args:
        n: reference-orbit mean motion (rad/s).
        t: propagation time (seconds, >= 0).

    Returns:
        A tuple of six rows, each a 6-tuple row of the transition matrix.
    """
    _require_n(n)
    _require_t(t)
    return _cw_transition(n, t)


def cw_propagate(n: float, t: float, state0: CWState) -> CWState:
    """Propagate an initial LVLH state forward by ``t`` seconds.

    Applies the closed-form CW solution to ``state0``; position components
    depend on the initial position and the initial relative velocity, and
    velocity components follow the CW rate equations.
    """
    _require_n(n)
    _require_t(t)
    if not (isinstance(state0, tuple) and len(state0) == 6):
        raise ValueError("state0 must be a 6-tuple (x, y, z, vx, vy, vz)")

    x0, y0, z0, vx0, vy0, vz0 = (float(v) for v in state0)
    c = math.cos(n * t)
    s = math.sin(n * t)
    nt = n * t
    return (
        (4 - 3 * c) * x0 + (s / n) * vx0 + (2 * (1 - c) / n) * vy0,
        6 * (s - nt) * x0 + y0 - (2 * (1 - c) / n) * vx0 + ((4 * s - 3 * nt) / n) * vy0,
        c * z0 + (s / n) * vz0,
        3 * n * s * x0 + c * vx0 + 2 * s * vy0,
        6 * n * (c - 1) * x0 - 2 * s * vx0 + (4 * c - 3) * vy0,
        -n * s * z0 + c * vz0,
    )


def single_impulse_intercept(
    n: float, t: float, r0: tuple[float, float, float]
) -> tuple[float, CWState]:
    """Return the single corrective impulse that zeroes the relative position.

    Solves the linear system ``Phi_rv(t) v0 = -Phi_rr(t) r0`` for the initial
    relative velocity that makes the relative position vanish at time ``t``.
    The in-plane (radial/along-track) and cross-track channels decouple and are
    solved in closed form.

    Args:
        n: reference-orbit mean motion (rad/s).
        t: intercept time (seconds, >= 0).
        r0: initial relative position ``(x0, y0, z0)`` (km).

    Returns:
        ``(impulse_km_s, v0)`` — the magnitude of the required initial relative
        velocity and the full required state ``(r0, v0)``.

    Raises:
        ValueError: at geometric singularities (``t=0``, full orbital periods,
            or intermediate in-plane degeneracies) where no single-impulse
            intercept exists; the chaser must use a multi-burn strategy there.
    """
    _require_n(n)
    _require_t(t)
    if not (isinstance(r0, tuple) and len(r0) == 3):
        raise ValueError("r0 must be a 3-tuple (x0, y0, z0)")
    x0, y0, z0 = (float(v) for v in r0)

    c = math.cos(n * t)
    s = math.sin(n * t)
    nt = n * t

    # Position-to-position and position-to-velocity blocks of the STM.
    ar_x = (4 - 3 * c) * x0
    ar_y = 6 * (s - nt) * x0 + y0

    det_inplane = (s * (4 * s - 3 * nt) + 4 * (1 - c) * (1 - c)) / (n * n)
    if abs(det_inplane) < _EPS:
        raise ValueError("singular in-plane intercept geometry: no single-impulse intercept")
    if abs(s) < _EPS:
        raise ValueError(
            "singular intercept geometry (cross-track): no single-impulse intercept at this time"
        )

    b00 = s / n
    b01 = 2 * (1 - c) / n
    b10 = -2 * (1 - c) / n
    b11 = (4 * s - 3 * nt) / n

    # v0 = -B^-1 (A r0): explicit 2x2 inverse.
    vx0 = -(b11 * ar_x - b01 * ar_y) / det_inplane
    vy0 = -(-b10 * ar_x + b00 * ar_y) / det_inplane
    vz0 = -(c * z0) * n / s

    impulse = math.sqrt(vx0 * vx0 + vy0 * vy0 + vz0 * vz0)
    return float(impulse), (float(x0), float(y0), float(z0), float(vx0), float(vy0), float(vz0))


def _require_n(n: float) -> None:
    if not (isinstance(n, (int, float)) and n > 0):
        raise ValueError(f"mean motion n must be > 0 (got {n!r})")


def _require_t(t: float) -> None:
    if not (isinstance(t, (int, float)) and t >= 0):
        raise ValueError(f"time t must be >= 0 (got {t!r})")
