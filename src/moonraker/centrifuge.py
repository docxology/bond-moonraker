"""Centrifuge g-force training profiles.

The DRAX concept includes the g-force training a special agent must survive
before boarding a manned spaceflight: high-radius centrifuge runs in which the
subject experiences sustained artificial gravity. This module models that
regime with real physics and a documented physiological tolerance curve:

* :func:`g_from_rpm` / :func:`rpm_for_g` — centripetal acceleration
  ``a = \\omega^2 r`` mapped to ``g = a / g0``.
* :func:`max_sustained_duration` — the human tolerance envelope: the longest
  time a given peak ``g`` level can be sustained before the onset of
  incapacitation (a power-law decay fit to the centrifuge-training literature).
* the profile builders — :func:`build_training_profile` (ramp / sustain /
  decay) and :func:`profile_is_safe` (never exceeds peak-g and duration
  limits with a safety margin).

The module is infrastructure-free (stdlib ``math`` only) and fully
deterministic: every value is a closed-form function of its inputs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "G0_MS2",
    "g_from_rpm",
    "rpm_for_g",
    "max_sustained_duration",
    "build_training_profile",
    "profile_is_safe",
]

#: Standard gravity (m/s^2), the conversion reference for g-levels.
G0_MS2 = 9.80665


def g_from_rpm(rpm: float, radius_m: float) -> float:
    """Return the centripetal acceleration (in g) at ``rpm`` on a centrifuge of
    given arm ``radius_m``.

    ``g = (2\\pi * rpm / 60)^2 * radius / g0``.
    """
    _require_positive(radius_m, "radius_m")
    _require_ge_zero(rpm, "rpm")
    angular_rate = 2.0 * math.pi * rpm / 60.0
    return angular_rate**2 * radius_m / G0_MS2


def rpm_for_g(g_target: float, radius_m: float) -> float:
    """Return the RPM required to produce ``g_target`` on a centrifuge arm of
    length ``radius_m`` (the inverse of :func:`g_from_rpm`)."""
    _require_ge_zero(g_target, "g_target")
    _require_positive(radius_m, "radius_m")
    return (60.0 / (2.0 * math.pi)) * math.sqrt(g_target * G0_MS2 / radius_m)


def max_sustained_duration(
    g: float, ceiling_s: float = 60.0, scale: float = 800.0, exponent: float = 2.5
) -> float:
    """Return the maximum time (seconds) a peak ``g`` level can be sustained.

    A deterministic power-law tolerance envelope, ``t = min(scale * g**-exp, ceiling)``,
    fitted to the centrifuge-training regime: tolerated duration falls steeply
    as peak ``g`` climbs, capped at ``ceiling_s`` for benign levels.
    """
    _require_ge_zero(g, "g")
    _require_positive(ceiling_s, "ceiling_s")
    _require_positive(scale, "scale")
    if g <= 0.0:
        return ceiling_s
    value: float = float(scale) * (float(g) ** -float(exponent))
    return min(value, float(ceiling_s))


@dataclass(frozen=True)
class TrainingProfile:
    """A deterministic centrifuge training run.

    Fields:
        time_s: tuple of sample times (seconds).
        g_levels: tuple of g-level samples aligned with ``time_s``.
        peak_g: the maximum g reached during the run.
        sustain_duration_s: length of the sustained plateau.
    """

    time_s: tuple[float, ...]
    g_levels: tuple[float, ...]
    peak_g: float
    sustain_duration_s: float

    def __post_init__(self) -> None:
        if len(self.time_s) != len(self.g_levels):
            raise ValueError("time_s and g_levels must be the same length")
        if not self.time_s:
            raise ValueError("TrainingProfile must contain at least one sample")
        for label, values in (("time_s", self.time_s), ("g_levels", self.g_levels)):
            for value in values:
                _require_ge_zero(value, f"{label} sample")


def build_training_profile(
    target_g: float,
    radius_m: float,
    ramp_rate_g_per_s: float = 0.5,
    sustain_s: float = 0.0,
    decay_rate_g_per_s: float = 1.0,
    sample_rate_hz: float = 10.0,
) -> TrainingProfile:
    """Build a full centrifuge run: ramp up, sustain at ``target_g``, decay.

    Args:
        target_g: peak g to hold during the sustain plateau.
        radius_m: centrifuge arm length (m).
        ramp_rate_g_per_s: how fast g rises during the ramp-up phase.
        sustain_s: seconds to hold the plateau.
        decay_rate_g_per_s: how fast g falls during the ramp-down phase.
        sample_rate_hz: number of g measurements per second.

    Returns:
        A :class:`TrainingProfile` with equally spaced time samples covering the
        whole run (ramp + plateau + decay). The plateau length is enforced in
        the discretized samples.
    """
    _require_ge_zero(target_g, "target_g")
    _require_positive(radius_m, "radius_m")
    _require_positive(ramp_rate_g_per_s, "ramp_rate_g_per_s")
    _require_ge_zero(sustain_s, "sustain_s")
    _require_positive(decay_rate_g_per_s, "decay_rate_g_per_s")
    _require_positive(sample_rate_hz, "sample_rate_hz")

    ramp_s = target_g / ramp_rate_g_per_s
    decay_s = target_g / decay_rate_g_per_s
    total_s = ramp_s + sustain_s + decay_s

    samples = int(math.ceil(total_s * sample_rate_hz))
    step = total_s / samples if samples else 0.0

    time_s: list[float] = []
    g_levels: list[float] = []
    for i in range(samples + 1):
        t = i * step
        time_s.append(round(t, 6))
        if t <= ramp_s:
            g = ramp_rate_g_per_s * t
        elif t <= ramp_s + sustain_s:
            g = target_g
        else:
            dt = t - (ramp_s + sustain_s)
            g = max(0.0, target_g - decay_rate_g_per_s * dt)
        g_levels.append(round(g, 6))

    return TrainingProfile(
        time_s=tuple(time_s),
        g_levels=tuple(g_levels),
        peak_g=round(target_g, 6),
        sustain_duration_s=round(sustain_s, 6),
    )


def profile_is_safe(
    profile: TrainingProfile,
    g_limit: float,
    duration_limit_s: float,
    margin_fraction: float = 0.2,
) -> tuple[bool, dict[str, float]]:
    """Check a training profile against peak-g and duration tolerance limits.

    Args:
        profile: the training run to assess.
        g_limit: the hard peak-g ceiling the run must stay under.
        duration_limit_s: the maximum escalator of the plateau.
        margin_fraction: a safety fraction (0..1) of the duration limit that is
            reserved, so the run is deemed safe only with headroom remaining.

    Returns:
        ``(safe, metrics)`` where ``metrics`` holds ``peak_g``, ``allowable_s``
        (the tolerance-limit duration at ``peak_g``) and ``xduration_s`` (the
        sustained duration). ``safe`` is True iff the peak stays under
        ``g_limit`` and the plateau is no longer than the allowed duration.
    """
    _require_positive(g_limit, "g_limit")
    _require_positive(duration_limit_s, "duration_limit_s")
    if not (0.0 <= margin_fraction < 1.0):
        raise ValueError("margin_fraction must be in [0, 1)")

    allowable_s = max_sustained_duration(profile.peak_g) * (1.0 - margin_fraction)
    peak_ok = profile.peak_g <= g_limit
    duration_ok = profile.sustain_duration_s <= allowable_s
    metrics = {
        "peak_g": profile.peak_g,
        "allowable_s": allowable_s,
        "sustain_s": profile.sustain_duration_s,
    }
    return peak_ok and duration_ok, metrics


def _require_positive(value: float, label: str) -> None:
    if not (isinstance(value, (int, float)) and value > 0):
        raise ValueError(f"{label} must be > 0 (got {value!r})")


def _require_ge_zero(value: float, label: str) -> None:
    if not (isinstance(value, (int, float)) and value >= 0):
        raise ValueError(f"{label} must be >= 0 (got {value!r})")
