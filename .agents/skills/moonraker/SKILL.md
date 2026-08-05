---
name: moonraker
description: PROJECT BOND film package (Moonraker, 1979, codename DRAX) — shuttle hijack timelining, orbital logistics, centrifuge g-profiles, BOND-API MissionProvider.
version: 0.2.0
author: active-inference-institute
license: MIT
tags: [bond, film-package, mission-provider, shuttle, orbital, centrifuge]
---

# moonraker

Project-scoped skill for the PROJECT BOND package at
`projects/working/bond/moonraker/`. Load when working inside the package.

## When to Use

- Working inside the `moonraker` DRAX package — editing source, running
  scripts/tests, or regenerating outputs.
- Implementing or verifying the BOND-API `MissionProvider` adapter.
- Validating the package's contracts (thin scripts, pure domain core, zero
  mocks) after changes.

## Quick Reference

```bash
cd projects/working/bond/moonraker
uv sync --extra dev
uv run python scripts/run_mission.py                    # full flow + artifacts
uv run python scripts/brief.py                          # per-phase CLIs
uv run python scripts/z_generate_manuscript_variables.py
uv run pytest tests/ --cov=src --cov-fail-under=90 -q   # gate (>=90%)
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
```

## Concepts

Seven pure domain modules under `src/moonraker/`:

- `shuttle_ops.py` — CPM shuttle-hijack timeline.
- `schedule_crashing.py` — minimum-cost time-cost crashing of that timeline.
- `orbital_logistics.py` — Kepler orbit, launch windows, station stores.
- `orbital_transfer.py` — Hohmann transfer, rocket equation, deorbit burn.
- `rendezvous.py` — Clohessy–Wiltshire relative-motion guidance.
- `centrifuge.py` — g-force profile + two-ceiling safety adjudication.
- `centrifuge_training.py` — g·s exposure dosing + weekly regimen planning.

Above them: `mission_results.py` (the single canonical computation),
`manuscript_variables.py`, `figures.py`, and `mission.py` — the BOND-API
`MissionProvider` (slug `moonraker`, codename `DRAX`) + gadget registry.

## Pitfalls

- **Pure domain core.** All seven domain modules plus `mission_results` must not
  import `bond_api` or `infrastructure`; only `mission.py` imports `bond_api`.
- **Frozen protocol surface.** Do not rename or reshape `brief`/`recon`/`plan`/
  `execute`/`debrief` or the module-level `MissionProvider`/`PROVIDER`/
  `provider`/`GADGETS`/`FILM`/`CODENAME` exports — the CLI, coordinator and
  orchestrator consume them across packages. Deepen inside.
- **Never hand-author a metric.** Numbers reach the manuscript as tokens from
  `mission_results` + `config.yaml`. Check claims against the resolved copies in
  `output/manuscript/`, not the templates.
- **No mocks.** All tests use real computation; deterministic fakes implement
  the REAL protocol.
- **Deterministic.** No untracked RNG, no wall-clock in persisted artifacts
  (`Provenance.wall_time_s == 0.0`).
- **Outputs are disposable.** Never hand-edit `output/` — regenerate with
  `run_mission.py` (byte-identical on re-run).
- **Run from the package dir** so `scripts/` find `src/` via their sys.path
  bootstrap.

## Cross-refs

- Contract: [`AGENTS.md`](../../../AGENTS.md) · README [`README.md`](../../../README.md)
- Architecture: [`docs/architecture.md`](../../../docs/architecture.md) ·
  Agent rules: [`docs/agent_instructions.md`](../../../docs/agent_instructions.md) ·
  Testing: [`docs/testing_philosophy.md`](../../../docs/testing_philosophy.md)
- TODO: [`TODO.md`](../../../TODO.md)
- BOND suite skill: `bond-suite-package-development` (+ `references/bond-api-phase1.md`)
