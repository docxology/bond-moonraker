# Introduction

*{{CONFIG_FILM}}* (1979) sends special agent James Bond to intercept Hugo
Drax's plan to destroy humanity from his private space station. Beneath the
set-pieces — a shuttle hijacked at a NASA launch tower, Drax's orbital station
with its centrifuge room, and the g-force chamber where Bond trains — lies a
computational core this package makes rigorous and reproducible.

**{{BOND_TITLE}}** (codename **{{CONFIG_CODENAME}}**) turns those set-pieces
into three concept areas, carried by seven pure domain modules.

**1 · The shuttle hijack.** `moonraker.shuttle_ops` models the takeover as an
activity network solved with the Critical Path Method, identifying the
load-bearing phases and checking feasibility against the shuttle's point of no
return. `moonraker.schedule_crashing` answers the follow-on question the film
never asks: if the window closes early, which phases do you buy down, and what
does the compression cost? It runs the classic greedy time-cost crash over the
same CPM solver.

**2 · The station and its resupply.** `moonraker.orbital_logistics` supplies
Kepler orbital mechanics (period, velocity, orbits per day), the ground launch
windows a resupply craft can use, pass geometry, and a closed-form consumables
model binding crew size, stock and resupply cadence.
`moonraker.orbital_transfer` flies the resupply: a Hohmann two-burn transfer
sized by vis-viva, the phase wait that aligns chaser to target, a Tsiolkovsky
propellant budget, and the deorbit burn home. `moonraker.rendezvous` closes the
last few kilometres with linearised Clohessy–Wiltshire relative motion and a
closed-form single-impulse intercept.

**3 · The g-force programme.** `moonraker.centrifuge` gives the ramp/sustain/
decay profile of a centrifuge run, the g↔rpm physics, and a safety verdict
against a +Gz tolerance envelope and a procedural plateau ceiling.
`moonraker.centrifuge_training` lifts that from one run to a regimen: g·s
exposure dosing, gradual-onset-rate tolerance scaling, and weekly session
planning under daily and cumulative exposure caps.

Two composition modules sit above these. `moonraker.mission_results` is the
single canonical computation every consumer reads, and
`moonraker.manuscript_variables` turns it into the brace-delimited token map
this manuscript is written against. `moonraker.figures` renders the PNGs.

The package implements the frozen BOND-API `MissionProvider` protocol in
`moonraker/mission.py`, so the BOND suite orchestrator can discover and drive
it through the standard brief → recon → plan → execute → debrief lifecycle.

## Reader's guide

- All seven domain modules are pure and infrastructure-free: they import
  nothing but the standard library, so they can be lifted and tested anywhere.
- `mission.py` is the thin adapter between the BOND protocol and the domain
  core, and the only module that imports `bond_api`.
- `scripts/` provides one CLI per mission phase plus a flagship runner that
  regenerates every artifact.
- The manuscript's numeric claims are injected from
  `manuscript/config.yaml` + `moonraker/manuscript_variables.py`, never
  hardcoded in prose. Where a computed verdict contradicts the film — as the
  centrifuge certification does — the manuscript reports the computation.
