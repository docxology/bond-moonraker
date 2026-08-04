"""Drax space-station orbital logistics.

Real orbital mechanics and closed-form logistics for a crewed space station
(the DRAX station) in a circular low-Earth orbit:

* :func:`orbital_period` — Kepler's third law, ``T = 2\\pi\\sqrt{a^3/\\mu}``.
* :func:`circular_speed` — the circular orbital velocity ``v = \\sqrt{\\mu/a}``.
* :func:`orbits_per_day` — the number of orbital revolutions in a sidereal day.
* :func:`visibility_half_angle` / :func:`pass_duration` — how long a ground
  site sees the station on each overhead pass (horizon geometry).
* :func:`launch_windows` — the deterministic series of ground launch windows a
  resupply craft can use to reach the station.
* the consumables model — :func:`consumables_days`, :func:`depletion_day`,
  :func:`sustainable_crew` and :func:`resupply_interval` — bounding station
  capacity, crew size and resupply cadence.

The module is infrastructure-free (stdlib ``math`` only): it is the pure
orbital-logistics core of ``moonraker`` and does not import ``bond_api``.
All constants are physical and deterministic — no RNG, no wall-clock inputs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "EARTH_RADIUS_KM",
    "EARTH_MU_KM3_S2",
    "SIDEREAL_DAY_S",
    "orbital_period",
    "circular_speed",
    "orbits_per_day",
    "visibility_half_angle",
    "pass_duration",
    "launch_windows",
    "consumables_days",
    "depletion_day",
    "sustainable_crew",
    "resupply_interval",
]

#: Mean Earth radius (km).
EARTH_RADIUS_KM = 6371.0
#: Standard gravitational parameter of Earth (km^3 / s^2).
EARTH_MU_KM3_S2 = 398600.4418
#: One sidereal day (s) — the Earth's rotation period against the stars.
SIDEREAL_DAY_S = 86164.0905


def orbital_period(
    altitude_km: float, r_earth: float = EARTH_RADIUS_KM, mu: float = EARTH_MU_KM3_S2
) -> float:
    """Return the orbital period of a circular orbit (seconds).

    Args:
        altitude_km: mean altitude above the Earth's surface.
        r_earth: mean Earth radius (km).
        mu: Earth gravitational parameter (km^3 / s^2).

    Returns:
        Orbital period in seconds, ``T = 2\\pi\\sqrt{a^3/\\mu}``.
    """
    if not (isinstance(altitude_km, (int, float)) and altitude_km > 0):
        raise ValueError(f"altitude_km must be > 0 (got {altitude_km!r})")
    if not (isinstance(r_earth, (int, float)) and r_earth > 0):
        raise ValueError(f"r_earth must be > 0 (got {r_earth!r})")
    if not (isinstance(mu, (int, float)) and mu > 0):
        raise ValueError(f"mu must be > 0 (got {mu!r})")
    semi_major = altitude_km + r_earth
    return 2.0 * math.pi * math.sqrt(semi_major**3 / mu)


def circular_speed(
    altitude_km: float, r_earth: float = EARTH_RADIUS_KM, mu: float = EARTH_MU_KM3_S2
) -> float:
    """Return the circular orbital speed (km/s) at a given altitude."""
    if not (isinstance(altitude_km, (int, float)) and altitude_km > 0):
        raise ValueError(f"altitude_km must be > 0 (got {altitude_km!r})")
    semi_major = altitude_km + r_earth
    return math.sqrt(mu / semi_major)


def orbits_per_day(altitude_km: float, sidereal_day_s: float = SIDEREAL_DAY_S) -> float:
    """Return the number of orbital revolutions per sidereal day."""
    if not (isinstance(sidereal_day_s, (int, float)) and sidereal_day_s > 0):
        raise ValueError(f"sidereal_day_s must be > 0 (got {sidereal_day_s!r})")
    return sidereal_day_s / orbital_period(altitude_km)


def visibility_half_angle(altitude_km: float, r_earth: float = EARTH_RADIUS_KM) -> float:
    """Return the maximum ground central angle (deg) at which the station is
    above the horizon for a site.

    A satellite at altitude ``h`` is visible from a site while the site-to-
    sub-satellite central angle stays below the horizon limit derived from the
    right triangle at grazing incidence: ``cos(limit) = R / (R + h)``.
    """
    if not (isinstance(altitude_km, (int, float)) and altitude_km > 0):
        raise ValueError(f"altitude_km must be > 0 (got {altitude_km!r})")
    ratio = r_earth / (r_earth + altitude_km)
    ratio = max(-1.0, min(1.0, ratio))
    return math.degrees(math.acos(ratio))


def pass_duration(
    altitude_km: float, elevation_threshold_deg: float = 10.0, r_earth: float = EARTH_RADIUS_KM
) -> float:
    """Return how long the station is visible from a nadir site per overhead
    pass (seconds).

    Uses the elevation threshold to shrink the visible half-angle: at a higher
    minimum elevation the usable cone is narrower. The pass duration is the
    time for the sub-satellite point to cross the usable chord, at the
    station's angular rate ``2\\pi / T``.
    """
    if not (
        isinstance(elevation_threshold_deg, (int, float)) and 0.0 <= elevation_threshold_deg < 90.0
    ):
        raise ValueError(
            f"elevation_threshold_deg must be in [0, 90) (got {elevation_threshold_deg!r})"
        )
    period = orbital_period(altitude_km, r_earth=r_earth)
    # Usable central half-angle: either side of the site the station must still
    # clear the required elevation. Horizon geometry gives the grazing angle;
    # apply a linear shrinkage for the elevation threshold (documented model).
    horizon_angle = math.radians(visibility_half_angle(altitude_km, r_earth=r_earth))
    threshold = math.radians(elevation_threshold_deg)
    usable = max(0.0, horizon_angle - threshold * (horizon_angle / (math.pi / 2.0)))
    # Angular rate of the station (rad/s); time to traverse the usable chord.
    angular_rate = 2.0 * math.pi / period
    return (2.0 * usable) / angular_rate


@dataclass(frozen=True)
class LaunchWindow:
    """A ground launch window: an open and close time (seconds from epoch)."""

    open_s: float
    close_s: float

    def __post_init__(self) -> None:
        for label, value in (("open_s", self.open_s), ("close_s", self.close_s)):
            if not (isinstance(value, (int, float)) and value >= 0):
                raise ValueError(f"LaunchWindow.{label} must be >= 0 (got {value!r})")
        if self.close_s <= self.open_s:
            raise ValueError("LaunchWindow.close_s must be after open_s")


def launch_windows(
    altitude_km: float,
    *,
    num_windows: int = 4,
    epoch_s: float = 0.0,
    elevation_threshold_deg: float = 10.0,
) -> tuple[LaunchWindow, ...]:
    """Return the next deterministic ground launch windows for the station.

    A launch site on the ground can rendezvous with the station each time the
    station's orbital plane passes over the site. Modeling the two plane
    crossings (ascending and descending node passage) per orbit, a window opens
    every half-period, and each window stays open for the duration of the
    usable pass at the requested elevation threshold. The windows are fully
    deterministic in ``epoch_s + k * (T/2)``.

    Args:
        altitude_km: station altitude.
        num_windows: number of windows to return (>= 1).
        epoch_s: mission epoch (seconds); windows are relative to this.
        elevation_threshold_deg: minimum pass elevation for a usable launch.

    Returns:
        An ordered tuple of :class:`LaunchWindow` (open, close) seconds.
    """
    if not (isinstance(num_windows, int) and num_windows >= 1):
        raise ValueError(f"num_windows must be an int >= 1 (got {num_windows!r})")
    if not (isinstance(epoch_s, (int, float)) and epoch_s >= 0):
        raise ValueError(f"epoch_s must be >= 0 (got {epoch_s!r})")
    period = orbital_period(altitude_km)
    half_period = period / 2.0
    duration = pass_duration(altitude_km, elevation_threshold_deg=elevation_threshold_deg)
    windows: list[LaunchWindow] = []
    for k in range(num_windows):
        open_s = epoch_s + k * half_period
        windows.append(LaunchWindow(open_s=open_s, close_s=open_s + duration))
    return tuple(windows)


def consumables_days(capacity_kg: float, crew: int, rate_kg_per_person_day: float) -> float:
    """Return how many days the station's consumables last at the given crew.

    ``days = capacity / (crew * rate)``.
    """
    _require_positive(capacity_kg, "capacity_kg")
    _require_positive(rate_kg_per_person_day, "rate_kg_per_person_day")
    _require_nonneg_int(crew, "crew")
    if crew == 0:
        return math.inf
    return capacity_kg / (crew * rate_kg_per_person_day)


def depletion_day(capacity_kg: float, crew: int, rate_kg_per_person_day: float) -> float:
    """Return the day (from resupply) on which consumables run empty.

    A station that cannot last until its next resupply is a logistics failure:
    the mission must raise resupply cadence or cut crew.
    """
    return consumables_days(capacity_kg, crew, rate_kg_per_person_day)


def sustainable_crew(
    capacity_kg: float, resupply_interval_days: float, rate_kg_per_person_day: float
) -> int:
    """Return the maximum integer crew size the station can sustain between
    resupplies, given the per-capita daily consumption rate.

    ``max_crew = floor(capacity / (interval * rate))``.
    """
    _require_positive(capacity_kg, "capacity_kg")
    _require_positive(resupply_interval_days, "resupply_interval_days")
    _require_positive(rate_kg_per_person_day, "rate_kg_per_person_day")
    return int(capacity_kg // (resupply_interval_days * rate_kg_per_person_day))


def resupply_interval(capacity_kg: float, crew: int, rate_kg_per_person_day: float) -> float:
    """Return the longest resupply cadence (days) the station can tolerate.

    This is exactly ``consumables_days`` — the station must be resupplied
    before its stores run out, so the maximum tolerable interval equals the
    depletion horizon for the current crew.
    """
    return consumables_days(capacity_kg, crew, rate_kg_per_person_day)


def _require_positive(value: float, label: str) -> None:
    if not (isinstance(value, (int, float)) and value > 0):
        raise ValueError(f"{label} must be > 0 (got {value!r})")


def _require_nonneg_int(value: int, label: str) -> None:
    if not (isinstance(value, int) and not isinstance(value, bool) and value >= 0):
        raise ValueError(f"{label} must be a non-negative integer (got {value!r})")
