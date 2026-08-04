# Architecture — moonraker (mission DRAX)

## Layers

| Layer | Components | Imports |
|---|---|---|
| **Domain core** | `shuttle_ops.py`, `orbital_logistics.py`, `centrifuge.py`, `mission_results.py` | stdlib + `math` only |
| **Adapter** | `mission.py` | `bond_api.*` + domain core |
| **I/O / rendering** | `manuscript_variables.py`, `figures.py` | stdlib, `yaml`, `matplotlib` |
| **Orchestrators** | `scripts/*.py` | `sys.path` bootstrap + delegate |

Dependency arrow: `scripts/ → src/moonraker/mission.py → domain core`, and
`src/moonraker/*` never imports `infrastructure.*`. `mission.py` is the only
module coupled to `bond_api`; the domain core stays importable in isolation.

## Data flow

1. `manuscript/config.yaml` → `mission:` block → `mission_results.py`
   (`compute_mission_results`) → the canonical result dict.
2. `mission.py` adapts the same computations into `MissionOutcome.results`
   with `Provenance`.
3. `manuscript_variables.py` combines config + results into `{{TOKEN}}` map;
   `write_resolved_manuscript_tree` resolves the manuscript sections.
4. `figures.py` renders the three deterministic PNGs.

## Constructing a computation

`metrics = compute_mission_results(params)` is the single, deterministic entry
point every downstream consumer (mission execute, manuscript variables, CLIs)
can rely on — do not fork it into ad-hoc scripts.
