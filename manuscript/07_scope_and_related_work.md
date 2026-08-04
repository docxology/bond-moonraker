# Scope and Related Work

## Scope

This package models three **closed-form** aspects of the DRAX mission for a
deterministic research exemplar. It deliberately does *not* model: atmospheric
re-entry or ascent trajectories, drag and J2 perturbations, three-dimensional
rendezvous guidance, or a full six-degree-of-freedom centrifuge biodynamic
model. Each simplification is documented at the point of use (e.g. the linear
visibility model in `orbital_logistics.pass_duration`).

## Related work

- **Critical Path Method** (Kelley & Walker, 1959) — the scheduling backbone of
  `moonraker/shuttle_ops.py`.
- **Kepler's laws / two-body problem** — the orbital period and circular-speed
  relations in `moonraker/orbital_logistics.py`.
- **Human +Gz tolerance curves** — the basis for the deterministic
  g-duration envelope in `moonraker/centrifuge.py` (`max_sustained_duration`).
