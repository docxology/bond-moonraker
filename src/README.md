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
```

## Modules

- `shuttle_ops.py` — pure Critical-Path-Method shuttle-hijack timeline.
- `orbital_logistics.py` — pure Kepler orbit physics + station logistics.
- `centrifuge.py` — pure g-force training-profile models.
- `mission_results.py` — canonical deterministic result computation.
- `mission.py` — BOND-API `MissionProvider` adapter + gadget registration.
- `manuscript_variables.py` — `{{TOKEN}}` hydration.
- `figures.py` — deterministic matplotlib figure generators.

## Rules

- Pure domain core imports stdlib/math only (no `bond_api`/`infrastructure`).
- Deterministic: no untracked RNG, no wall-clock in persisted artifacts.
