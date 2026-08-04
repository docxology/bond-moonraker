"""Orbital transfer mechanics for the DRAX resupply campaign.

Real astrodynamics used to fly a resupply craft from a low parking orbit up to
the DRAX station and back down:

* :func:`vis_viva` — the vis-viva equation ``v = sqrt(mu * (2/r - 1/a))`` giving
  the speed of a body at radius ``r`` on an orbit of semi-major axis ``a``.
* :func:`hohmann_transfer` — the minimum-energy (Hohmann) transfer between two
  circular orbits: two tangential burns, the transfer ellipse, and the
  half-ellipse transfer time ``t = pi * sqrt(a^3 / mu)``.
* :func:`phase_wait_time` — how long a chaser in the lower orbit must wait for
  the target's phase angle to reach the Hohmann lead angle before lighting the
  first burn.
* :func:`tsiolkovsky_mass_ratio` / :func:`propellant_fraction` /
  :func:`propellant_mass` — the rocket equation
  ``m0/mf = exp(dv / (Isp * g0))`` sizing the propellant a resupply needs.
* :func:`deorbit_dv` — the retrograde burn that drops the perigee into the
  atmosphere for a controlled deorbit.

The module is infrastructure-free (stdlib ``math`` only) and fully
deterministic; it reuses the physical constants from
:mod:`moonraker.orbital_logistics`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .orbital_logistics import EARTH_MU_KM3_S2, EARTH_RADIUS_KM

__all__ = [
    "HohmannTransfer",
    "vis_viva",
    "hohmann_transfer",
    "phase_wait_time",
    "tsiolkovsky_mass_ratio",
    "propellant_fraction",
    "propellant_mass",
    "deorbit_dv",
]

#: Standard gravity in km/s^2 (rocket-equation units).
_G0_KM_S2 = 9.80665e-3


def _require_above_earth(value: float, label: str) -> None:
    if not (isinstance(value, (int, float)) and value > EARTH_RADIUS_KM):
        raise ValueError(
            f"{label} must be above the Earth's surface (>{EARTH_RADIUS_KM} km, got {value!r})"
        )


@dataclass(frozen=True)
class HohmannTransfer:
    """The minimum-energy transfer between two circular orbits.

    Fields:
        r1_km / r2_km: radius of the departure / target circular orbit.
        dv1_km_s / dv2_km_s: magnitude of the first (prograde) and second
            (circularisation) burns.
        total_dv_km_s: ``dv1 + dv2``.
        transfer_time_s: half-ellipse transfer duration.
        semi_major_km: semi-major axis of the transfer ellipse.
    """

    r1_km: float
    r2_km: float
    dv1_km_s: float
    dv2_km_s: float
    total_dv_km_s: float
    transfer_time_s: float
    semi_major_km: float


def vis_viva(r_km: float, a_km: float, mu: float = EARTH_MU_KM3_S2) -> float:
    """Return the orbital speed (km/s) at radius ``r_km`` for semi-major axis ``a_km``.

    ``v = sqrt(mu * (2/r - 1/a))``. Requires a positive radius and semi-major
    axis, and an orbit that reaches ``r`` (``a >= r/2`` for an ellipse).
    """
    if not (isinstance(r_km, (int, float)) and r_km > 0):
        raise ValueError(f"r_km must be > 0 (got {r_km!r})")
    if not (isinstance(a_km, (int, float)) and a_km > 0):
        raise ValueError(f"a_km must be > 0 (got {a_km!r})")
    if not (isinstance(mu, (int, float)) and mu > 0):
        raise ValueError(f"mu must be > 0 (got {mu!r})")
    if a_km < r_km / 2.0:
        raise ValueError(f"a_km ({a_km}) too small to reach r_km ({r_km})")
    return float(math.sqrt(mu * (2.0 / r_km - 1.0 / a_km)))


def hohmann_transfer(
    r1_km: float,
    r2_km: float,
    mu: float = EARTH_MU_KM3_S2,
) -> HohmannTransfer:
    """Return the Hohmann transfer between two circular orbits.

    Args:
        r1_km: departure circular-orbit radius (km).
        r2_km: target circular-orbit radius (km).
        mu: gravitational parameter (km^3/s^2).

    Returns:
        The transfer with both burns, the total delta-v and the transfer time.

    Raises:
        ValueError: when the orbits coincide, are below the Earth's surface, or
            ``mu`` is invalid.
    """
    _require_above_earth(r1_km, "r1_km")
    _require_above_earth(r2_km, "r2_km")
    if not (isinstance(mu, (int, float)) and mu > 0):
        raise ValueError(f"mu must be > 0 (got {mu!r})")
    if abs(r1_km - r2_km) < 1e-9:
        raise ValueError("hohmann_transfer requires two distinct circular orbits")

    v1 = math.sqrt(mu / r1_km)
    v2 = math.sqrt(mu / r2_km)
    semi_major = (r1_km + r2_km) / 2.0
    v1t = vis_viva(r1_km, semi_major, mu=mu)
    v2t = vis_viva(r2_km, semi_major, mu=mu)
    dv1 = abs(v1t - v1)
    dv2 = abs(v2 - v2t)
    transfer_time = math.pi * math.sqrt(semi_major**3 / mu)
    return HohmannTransfer(
        r1_km=float(r1_km),
        r2_km=float(r2_km),
        dv1_km_s=float(dv1),
        dv2_km_s=float(dv2),
        total_dv_km_s=float(dv1 + dv2),
        transfer_time_s=float(transfer_time),
        semi_major_km=float(semi_major),
    )


def _mean_motion(r_km: float, mu: float) -> float:
    """Circular-orbit mean motion ``n = sqrt(mu / r^3)`` (rad/s)."""
    return math.sqrt(mu / r_km**3)


def phase_wait_time(
    r_chaser_km: float,
    r_target_km: float,
    phase_angle_rad: float,
    mu: float = EARTH_MU_KM3_S2,
) -> tuple[float, float]:
    """Return the wait and lead angle before lighting a Hohmann rendezvous burn.

    The chaser lives in the lower circular orbit (``r_chaser_km``) and must
    catch the target in the higher circular orbit (``r_target_km``). At the
    moment of the first burn the target must lead the chaser by the Hohmann
    lead angle ``phi_lead = pi - n_target * t_transfer``; because the chaser's
    mean motion exceeds the target's, the relative phase closes at rate
    ``n_chaser - n_target``.

    Args:
        r_chaser_km: chaser circular-orbit radius (lower orbit).
        r_target_km: target circular-orbit radius (higher orbit).
        phase_angle_rad: current target-leads-chaser phase angle in [0, 2pi).
        mu: gravitational parameter.

    Returns:
        ``(wait_s, lead_angle_rad)`` — the deterministic wait until the burn
        and the lead angle it requires.
    """
    _require_above_earth(r_chaser_km, "r_chaser_km")
    _require_above_earth(r_target_km, "r_target_km")
    if not (isinstance(mu, (int, float)) and mu > 0):
        raise ValueError(f"mu must be > 0 (got {mu!r})")
    if r_chaser_km >= r_target_km:
        raise ValueError("chaser must be in the LOWER orbit for a catch-up rendezvous")
    if not (isinstance(phase_angle_rad, (int, float)) and 0.0 <= phase_angle_rad < 2.0 * math.pi):
        raise ValueError("phase_angle_rad must be in [0, 2*pi)")

    transfer = hohmann_transfer(r_chaser_km, r_target_km, mu=mu)
    n_chaser = _mean_motion(r_chaser_km, mu)
    n_target = _mean_motion(r_target_km, mu)
    lead = (math.pi - n_target * transfer.transfer_time_s) % (2.0 * math.pi)
    relative_rate = n_chaser - n_target
    wait = ((phase_angle_rad - lead) % (2.0 * math.pi)) / relative_rate
    return float(wait), float(lead)


def tsiolkovsky_mass_ratio(dv_km_s: float, isp_s: float, g0_km_s2: float = _G0_KM_S2) -> float:
    """Return the rocket-equation mass ratio ``m0/mf = exp(dv / (Isp * g0))``."""
    if not (isinstance(dv_km_s, (int, float)) and dv_km_s >= 0):
        raise ValueError(f"dv_km_s must be >= 0 (got {dv_km_s!r})")
    _require_positive(isp_s, "isp_s")
    _require_positive(g0_km_s2, "g0_km_s2")
    return float(math.exp(dv_km_s / (isp_s * g0_km_s2)))


def propellant_fraction(dv_km_s: float, isp_s: float, g0_km_s2: float = _G0_KM_S2) -> float:
    """Return the fraction of the launch mass that must be propellant."""
    ratio = tsiolkovsky_mass_ratio(dv_km_s, isp_s, g0_km_s2)
    return float(1.0 - 1.0 / ratio)


def propellant_mass(
    dv_km_s: float,
    isp_s: float,
    dry_mass_kg: float,
    g0_km_s2: float = _G0_KM_S2,
) -> float:
    """Return the propellant mass (kg) needed for ``dv`` with a given dry mass."""
    _require_positive(dry_mass_kg, "dry_mass_kg")
    ratio = tsiolkovsky_mass_ratio(dv_km_s, isp_s, g0_km_s2)
    return float(dry_mass_kg * (ratio - 1.0))


def deorbit_dv(
    r_circular_km: float,
    r_perigee_km: float,
    mu: float = EARTH_MU_KM3_S2,
) -> float:
    """Return the retrograde burn (km/s) lowering perigee to ``r_perigee_km``.

    A single retrograde burn at apogee of the current circular orbit reshapes
    it into an ellipse whose perigee grazes ``r_perigee_km``. The required
    delta-v is the difference between the circular speed and the apogee speed
    of the new ellipse (vis-viva).
    """
    _require_above_earth(r_circular_km, "r_circular_km")
    _require_above_earth(r_perigee_km, "r_perigee_km")
    if not (isinstance(mu, (int, float)) and mu > 0):
        raise ValueError(f"mu must be > 0 (got {mu!r})")
    if r_perigee_km >= r_circular_km:
        raise ValueError("r_perigee_km must be below r_circular_km for a deorbit burn")

    semi_major = (r_circular_km + r_perigee_km) / 2.0
    apogee_speed = vis_viva(r_circular_km, semi_major, mu=mu)
    circular = math.sqrt(mu / r_circular_km)
    return float(circular - apogee_speed)


def _require_positive(value: float, label: str) -> None:
    if not (isinstance(value, (int, float)) and value > 0):
        raise ValueError(f"{label} must be > 0 (got {value!r})")
