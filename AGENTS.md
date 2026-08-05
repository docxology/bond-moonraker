# AGENTS.md — moonraker (mission DRAX)

**moonraker** is a `PROJECT BOND` suite package modelling the DRAX mission from
*Moonraker* (1979) across three concept areas — the shuttle hijack (critical-path
timeline and time-cost crashing), the Drax station (orbital logistics, Hohmann
resupply, Clohessy–Wiltshire rendezvous), and centrifuge g-force training (the
+Gz tolerance envelope and an exposure-capped regimen). It implements the frozen
BOND-API `MissionProvider` protocol.

## Scope & constraints

- **Scope = exactly this package dir.** Never touch sibling packages, bond root
  files, or the template repo.
- **Local-only.** No remote, never push. Commit only within this repo.
- **Zero mocks.** Real data + computation only; deterministic fakes implement
  the REAL protocol.
- **≥90% line+branch coverage on `src/`**: `uv run pytest tests/ --cov=src --cov-fail-under=90`.
- **Deterministic**: fixed seeds, no untracked RNG, no wall-clock in persisted
  artifacts (`Provenance.wall_time_s == 0.0`).
- **Thin orchestrators in `scripts/`; business logic in `src/`.**
- **No hand-authored metrics in prose** — every number arrives as a token.

## Build

```bash
uv sync --extra dev     # installs deps + the bond-api local path dependency
```

Re-run after any `pyproject.toml` edit; a fresh scaffold's `.venv` has no deps.
The package targets Python 3.10+ and is standalone (see `STANDALONE.md`): there
is no `infrastructure/` import anywhere in `src/`.

## Run

```bash
uv run python scripts/run_mission.py                      # full flow + all artifacts
uv run python scripts/brief.py                            # per-phase CLIs …
uv run python scripts/recon.py
uv run python scripts/plan.py
uv run python scripts/execute.py
uv run python scripts/debrief.py
uv run python scripts/z_generate_manuscript_variables.py  # tokens + resolved manuscript
```

`z_generate_manuscript_variables.py` is strict by default: it requires
`output/data/mission_results.json` (exit 2 if absent). Pass `--allow-draft` to
relax that. Everything written under `output/` is regenerable and git-ignored;
`run_mission.py` restores a byte-identical tree on re-run, which is the
determinism proof.

## Test & verify

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q     # the gate
uv run pytest tests/test_centrifuge.py -q                 # one module
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/           # drop --check to apply
uv run mypy src/ scripts/
grep -rn "MagicMock\|mocker.patch\|unittest.mock" tests/ || echo "no mocks: clean"
git status --short                                        # clean after your commit
```

Measured counts live in `docs/_generated/COUNTS.md`. Regenerate them from the
gate rather than editing them by hand, and do not quote them in other prose.

## Layer contract

| Surface | Rule |
|---|---|
| `shuttle_ops.py`, `schedule_crashing.py`, `orbital_logistics.py`, `orbital_transfer.py`, `rendezvous.py`, `centrifuge.py`, `centrifuge_training.py` | Pure domain math — stdlib only; no `bond_api`, no `infrastructure` |
| `mission_results.py` | The single canonical computation over the domain core |
| `manuscript_variables.py`, `figures.py` | I/O + rendering (`yaml`, `matplotlib`) |
| `mission.py` | The only module importing `bond_api` — thin adapter to the frozen protocol |
| `scripts/` | Thin CLIs: `sys.path` bootstrap, argv, delegate, print. No arithmetic |

The domain core stays importable without `bond-api` installed. Full detail:
`docs/architecture.md`.

## Protocol integration

- Local path dependency in `pyproject.toml`:
  `bond-api = { path = "../bond-api" }`.
- `src/moonraker/mission.py` exposes `MissionProvider`, `PROVIDER`, `provider`,
  `GADGETS`, `FILM` and `CODENAME` at module top level, implements the five
  stages (`brief`/`recon`/`plan`/`execute`/`debrief`), and registers its real
  domain callables with `bond_api.registry.GadgetRegistry`.
- Discovery: `bond_api.discovery.load_provider("moonraker")`.
- **This surface is frozen.** `bond-cli`, the coordinator's reconcile and the
  orchestrator consume it across packages. Add modules, gadgets and internals
  freely; do not rename a stage, change a return type, or drop an export.

## Manuscript discipline

- Numeric metrics are injected from `manuscript/config.yaml` →
  `src/moonraker/manuscript_variables.py`; never hand-author a number in prose.
- To publish a new quantity: add it to `compute_mission_results`, regenerate,
  confirm the value in `output/data/manuscript_variables.json`, then reference
  the token.
- `tests/test_manuscript_variables.py::TestLiveCrossReference` reads every
  numbered section on disk and fails on any token the map does not define.
- Check claims against the **resolved** copies in `output/manuscript/`, not the
  templates. A sentence can be true about a token and false about its value.
- Report what the model computes even when it contradicts the film. The
  centrifuge certification verdict is the standing example, and it is pinned in
  both directions by `tests/test_mission_results.py`.

## See also

- `README.md` — orientation, module table, the `MissionProvider` surface.
- `docs/agent_instructions.md` — operational rules and the edit loop.
- `docs/architecture.md` — layer boundaries, per-module detail, data flow.
- `docs/testing_philosophy.md` — zero-mock doctrine and coverage mechanics.
- `TODO.md` — remaining work and declared integration points.
- BOND suite skill: `bond-suite-package-development` (references
  `bond-api-phase1.md` = the frozen protocol).
