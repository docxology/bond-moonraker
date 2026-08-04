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

- `src/moonraker/shuttle_ops.py` — CPM shuttle-hijack timeline.
- `src/moonraker/orbital_logistics.py` — Kepler orbit + station logistics.
- `src/moonraker/centrifuge.py` — g-force profile + tolerance envelope.
- `src/moonraker/mission.py` — BOND-API `MissionProvider` (slug `moonraker`,
  codename `DRAX`) + gadget registry.

## Pitfalls

- **Pure domain core.** `shuttle_ops/orbital_logistics/centrifuge/mission_results`
  must not import `bond_api` or `infrastructure`; only `mission.py` imports
  `bond_api`.
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
- TODO: [`TODO.md`](../../../TODO.md)
- BOND suite skill: `bond-suite-package-development` (+ `references/bond-api-phase1.md`)
