# Experimental Setup

## Mission parameters

All parameters live in `manuscript/config.yaml` → `mission:` and are read by
`moonraker/mission_results.py`:

| Parameter | Value | Consumed by |
|---|---|---|
| Hijack point of no return | {{CONFIG_DEADLINE_MIN}} min | `shuttle_ops` |
| Tightened crash deadline | {{CONFIG_CRASH_DEADLINE_MIN}} min | `schedule_crashing` |
| Station altitude | {{CONFIG_STATION_ALTITUDE_KM}} km | `orbital_logistics` |
| Crew | {{CONFIG_CREW}} | `orbital_logistics` |
| Resupply capacity | {{CONFIG_CAPACITY_KG}} kg | `orbital_logistics` |
| Per-capita consumption | {{CONFIG_RATE_KG_PERSON_DAY}} kg/person/day | `orbital_logistics` |
| Resupply cadence | {{CONFIG_RESUPPLY_INTERVAL_DAYS}} days | `orbital_logistics` |
| Parking-orbit altitude | {{CONFIG_PARK_ALTITUDE_KM}} km | `orbital_transfer` |
| Engine specific impulse | {{CONFIG_TRANSFER_ISP_S}} s | `orbital_transfer` |
| Resupply dry mass | {{CONFIG_TRANSFER_DRY_MASS_KG}} kg | `orbital_transfer` |
| Deorbit target perigee | {{CONFIG_DEORBIT_PERIGEE_KM}} km | `orbital_transfer` |
| Intercept time | {{CONFIG_RENDEZVOUS_INTERCEPT_S}} s | `rendezvous` |
| Centrifuge arm | {{CONFIG_CENTRIFUGE_RADIUS_M}} m | `centrifuge` |
| Centrifuge target g | {{CONFIG_TARGET_G}} g | `centrifuge` |
| Sustained plateau | {{CONFIG_SUSTAIN_S}} s | `centrifuge` |
| Ramp / decay rate | {{CONFIG_RAMP_RATE_G_PER_S}} / {{CONFIG_DECAY_RATE_G_PER_S}} g/s | `centrifuge` |
| Peak-g ceiling | {{CONFIG_G_LIMIT}} g | `centrifuge` |
| Procedural plateau ceiling | {{CONFIG_DURATION_LIMIT_S}} s | `centrifuge` |
| Tolerance safety margin | {{CONFIG_MARGIN_PCT}}% | `centrifuge` |
| Daily exposure cap | {{CONFIG_TRAINING_DAILY_CAP_GS}} g·s | `centrifuge_training` |
| Weekly exposure cap | {{CONFIG_TRAINING_WEEKLY_CAP_GS}} g·s | `centrifuge_training` |
| Planned sessions per week | {{CONFIG_TRAINING_SESSIONS}} | `centrifuge_training` |

These values are shared, single-source parameters; the manuscript consumes them
via token injection from `moonraker/manuscript_variables.py`, never as
hardcoded prose. `MISSION_DEFAULTS` in `moonraker/mission_results.py` mirrors
this block so the domain core stays runnable without reading a config file, and
any key the config omits falls back to it.

## Running the setup

```bash
uv sync --extra dev
uv run python scripts/run_mission.py                      # results + figures
uv run python scripts/z_generate_manuscript_variables.py  # tokens + resolved tree
```

## Software environment

- Python {{PYTHON_VERSION}} on {{PLATFORM}}.
- Declared dependencies: `matplotlib`, `pyyaml`, and `bond-api` (the frozen
  BOND suite protocol); `numpy` is pulled transitively by matplotlib and is not
  imported by any module in this package.
- Determinism: fixed parameter set, no random draws, no wall-clock inputs in
  any persisted artifact.
