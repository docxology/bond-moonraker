# Experimental Setup

## Mission parameters

All parameters live in `manuscript/config.yaml` → `mission:` and are read by
`moonraker/mission_results.py`:

| Parameter | Value |
|---|---|
| Hijack point of no return | {{CONFIG_DEADLINE_MIN}} min |
| Station altitude | {{CONFIG_STATION_ALTITUDE_KM}} km |
| Crew | {{CONFIG_CREW}} |
| Resupply capacity | {{CONFIG_CAPACITY_KG}} kg |
| Per-capita consumption | {{CONFIG_RATE_KG_PERSON_DAY}} kg/person/day |
| Resupply cadence | {{CONFIG_RESUPPLY_INTERVAL_DAYS}} days |
| Centrifuge arm | {{CONFIG_CENTRIFUGE_RADIUS_M}} m |
| Centrifuge target g | {{CONFIG_TARGET_G}} g |
| Sustained plateau | {{CONFIG_SUSTAIN_S}} s |

These values are shared, single-source parameters; the manuscript consumes them
via token injection from `moonraker/manuscript_variables.py`, never as
hardcoded prose.

## Software environment

- Python {{PYTHON_VERSION}} on {{PLATFORM}}.
- Dependencies: `numpy`, `matplotlib`, `pyyaml`, and `bond-api` (the frozen
  BOND suite protocol).
- Determinism: fixed parameter set, no random draws, no wall-clock inputs in
  any persisted artifact.
