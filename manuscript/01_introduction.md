# Introduction

*{{CONFIG_FILM}}* (1979) sends special agent James Bond to intercept Hugo
Drax's plan to destroy humanity from his private space station. Beneath the
set-pieces — a shuttle hijacked at a NASA launch tower, Drax's orbital station
with its centrifuge room, and the g-force chamber where Bond trains — lies a
computational core this package makes rigorous and reproducible.

**{{BOND_TITLE}}** (codename **{{CONFIG_CODENAME}}**) turns those set-pieces
into three verified models:

1. **Shuttle hijack timeline** (`moonraker.shuttle_ops`) — the takeover of the
   shuttle as an activity network, solved with the Critical Path Method to
   identify the load-bearing phases and check feasibility against the
   shuttle's point of no return.
2. **Space-station orbital logistics** (`moonraker.orbital_logistics`) — real
   Kepler orbital mechanics (period, velocity, orbits per day), the series of
   ground launch windows a resupply craft can use, and a closed-form
   consumables-capacity model that binds crew size, stock and resupply cadence.
3. **Centrifuge g-force training profiles** (`moonraker.centrifuge`) — the
   ramp/sustain/decay g-profile of a centrifuge run, bounded by a deterministic
   g-duration tolerance envelope and a safety check.

The package implements the frozen BOND-API `MissionProvider` protocol in
`moonraker/mission.py`, so the BOND suite orchestrator can discover and drive
it through the standard brief → recon → plan → execute → debrief lifecycle.

## Reader's guide

- The three domain modules are pure and infrastructure-free: they import
  nothing but the standard library, so they can be lifted and tested anywhere.
- `mission.py` is the thin adapter between the BOND protocol and the domain
  core.
- `scripts/` provides one CLI per mission phase.
- The manuscript's numeric claims are injected from
  `manuscript/config.yaml` + `moonraker/manuscript_variables.py`, never
  hardcoded in prose.
