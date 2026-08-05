# src/ — moonraker domain core + mission adapter

Importable logic for the moonraker (DRAX) package. The domain core is pure and
infrastructure-free; `mission.py` is the thin adapter to the frozen BOND-API
protocol.

## Quick start

```python
from moonraker.shuttle_ops import compute_timeline, DRAX_HIJACK_TIMELINE
from moonraker.centrifuge import build_training_profile, profile_is_safe

schedule = compute_timeline(DRAX_HIJACK_TIMELINE)  # CPM hijack timeline
profile = build_training_profile(target_g=6.0, radius_m=8.0, sustain_s=12.0)
safe, metrics = profile_is_safe(profile, g_limit=9.0, duration_limit_s=30.0)
# -> (False, {...}): the 12 s plateau overruns the allowance at 6 g.
```

The canonical result set comes from one place:

```python
from moonraker.mission_results import compute_mission_results

results = compute_mission_results()  # defaults; pass a dict to override
```

## Modules

Pure domain core (stdlib only, importable without `bond-api`):

- `shuttle_ops.py` — Critical-Path-Method shuttle-hijack timeline.
- `schedule_crashing.py` — minimum-cost time-cost crashing of that timeline.
- `orbital_logistics.py` — Kepler orbit physics, launch windows, station stores.
- `orbital_transfer.py` — Hohmann transfer, rocket equation, deorbit burn.
- `rendezvous.py` — Clohessy–Wiltshire relative-motion guidance.
- `centrifuge.py` — g-force profile physics and the two-ceiling safety check.
- `centrifuge_training.py` — g·s exposure dosing and weekly regimen planning.

Composition, adapter, presentation:

- `mission_results.py` — the single canonical deterministic result computation.
- `mission.py` — BOND-API `MissionProvider` adapter + gadget registration (the
  only module importing `bond_api`).
- `manuscript_variables.py` — token hydration from config + results.
- `figures.py` — five deterministic matplotlib figure generators.

Per-module detail: `../docs/architecture.md`.

## Rules

- Pure domain core imports stdlib/math only (no `bond_api`/`infrastructure`).
- Deterministic: no untracked RNG, no wall-clock in persisted artifacts.
