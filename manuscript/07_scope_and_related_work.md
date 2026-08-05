# Scope and Related Work

## Scope

This package models three **closed-form** aspects of the DRAX mission as a
deterministic research exemplar. Everything it computes is a two-body,
linearised or linear-cost approximation chosen so the answer can be audited by
hand.

Deliberately **not** modelled:

- Atmospheric ascent and re-entry trajectories; the shuttle timeline ends at
  docking and the deorbit burn is sized but not flown.
- Orbital perturbations — drag, the J2 oblateness term, third-body effects,
  solar radiation pressure. Orbits are ideal circular two-body orbits, so the
  launch-window series in `orbital_logistics` does not precess.
- Full three-dimensional, multi-burn rendezvous guidance. The
  Clohessy–Wiltshire model in `rendezvous` is linearised about a circular
  reference orbit and is valid only for separations small against the orbit
  radius; `single_impulse_intercept` raises rather than returning a number at
  the geometric singularities (whole-period intercept times) where the
  single-impulse assumption fails.
- Six-degree-of-freedom centrifuge biodynamics. `centrifuge` treats +Gz as a
  scalar level against a population-average tolerance envelope, with no
  individual variation, no anti-G straining manoeuvre, no G-suit and no
  cumulative fatigue between sessions.
- Stochastic activity durations. The hijack network is deterministic CPM with no
  PERT-style distribution over phase durations, so there is no confidence
  interval on the {{SHUTTLE_TOTAL_MIN}}-minute total.
- Onset-rate credit in the training regimen. `centrifuge_training` implements
  `gor_tolerance_multiplier`, but nothing published consumes it: the reported
  allowance and session count are onset-rate–independent (see §Methodology).

Each simplification is also documented at its point of use — for example the
linear elevation-threshold shrinkage in `orbital_logistics.pass_duration` and
the power-law fit in `centrifuge.max_sustained_duration`.

## Related work

| Model | Module | Source |
|---|---|---|
| Critical Path Method | `shuttle_ops.py` | Kelley & Walker (1959) [@kelley1959critical] |
| Time-cost crashing | `schedule_crashing.py` | Kelley & Walker (1959) [@kelley1959critical] |
| Kepler two-body orbits, pass geometry | `orbital_logistics.py` | Vallado (2013) [@vallado2013astrodynamics] |
| Hohmann two-impulse transfer | `orbital_transfer.py` | Hohmann (1925) [@hohmann1925] |
| Rocket equation | `orbital_transfer.py` | Tsiolkovsky (1903) [@tsiolkovsky1903] |
| Linearised relative motion | `rendezvous.py` | Clohessy & Wiltshire (1960) [@clohessy1960] |
| +Gz tolerance envelope | `centrifuge.py` | Stoll (1956) [@stoll1956human] |
| +Gz exposure dosing (GOR scaling implemented but unpublished) | `centrifuge_training.py` | Burton (1988) [@burton1988] |

The time-cost crashing trade-off is the cost extension of the same Kelley &
Walker scheduling work that introduces CPM. This package implements the greedy
crash along the critical path rather than the equivalent linear programme; for
the strictly linear per-minute cost structure used here the two agree.

Within the BOND suite, `moonraker` is the orbital-logistics package. Adjacent
packages model neighbouring physics — orbital capture and hidden-base discovery
(`you_only_live_twice`), orbital weapon targeting geometry
(`diamonds_are_forever`, `die_another_day`) and orbital EMP effects
(`goldeneye`). Per the suite layering rule these packages never import one
another; shared mechanics would live in `bond-utilities` or `bond-api`.
