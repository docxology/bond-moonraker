# src/ — moonraker domain core + mission adapter

The importable logic of the moonraker (DRAX) package.

## Modules

- `shuttle_ops.py` — pure CPM shuttle-hijack timeline.
- `orbital_logistics.py` — pure Kepler + station logistics.
- `centrifuge.py` — pure g-force profile models.
- `mission_results.py` — canonical deterministic result computation.
- `mission.py` — BOND-API `MissionProvider` adapter (the only `bond_api`
  import) + gadget registration.
- `manuscript_variables.py` — `{{TOKEN}}` hydration from config + results.
- `figures.py` — deterministic matplotlib figure generators.

## Rules

- Domain core (`shuttle_ops`, `orbital_logistics`, `centrifuge`,
  `mission_results`) must import nothing but stdlib/math — no `bond_api`, no
  `infrastructure`. This keeps it liftable into any Python environment.
- `mission.py` is the thin adapter; all computation stays in the domain core.
- Everything is deterministic (no untracked RNG, no wall-clock in artifacts).
