# src/ — moonraker domain core + mission adapter

The importable logic of the moonraker (DRAX) package.

## Modules

- `shuttle_ops.py` — pure CPM shuttle-hijack timeline.
- `orbital_logistics.py` — pure Kepler + station logistics.
- `centrifuge.py` — pure g-force profile models.
- `orbital_transfer.py` — pure Hohmann transfer + rocket equation + deorbit.
- `rendezvous.py` — pure Clohessy–Wiltshire relative-motion guidance.
- `centrifuge_training.py` — pure g·s exposure + training-regimen planning.
- `schedule_crashing.py` — pure minimum-cost time-cost crashing.
- `mission_results.py` — canonical deterministic result computation.
- `mission.py` — BOND-API `MissionProvider` adapter (the only `bond_api`
  import) + gadget registration.
- `manuscript_variables.py` — `{{TOKEN}}` hydration from config + results.
- `figures.py` — deterministic matplotlib figure generators.

## Rules

- Domain core (all `shuttle_ops`…`schedule_crashing` plus `mission_results`)
  must import nothing but stdlib/math — no `bond_api`, no `infrastructure`.
  This keeps it liftable into any Python environment.
- `mission.py` is the thin adapter; all computation stays in the domain core.
- Everything is deterministic (no untracked RNG, no wall-clock in artifacts).
