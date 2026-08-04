# AGENTS.md — moonraker (mission DRAX)

**moonraker** is a `PROJECT BOND` suite package modelling the DRAX mission from
*Moonraker* (1979): a space-shuttle hijack timeline, Drax space-station orbital
logistics, and centrifuge g-force training profiles. It implements the frozen
BOND-API `MissionProvider` protocol.

## Scope & constraints

- **Scope = exactly this package dir.** Never touch sibling packages, bond root
  files, or the template repo.
- **Local-only.** No remote, never push. Commit only within this repo with
  path-scoped, `git add -A` commits.
- **Zero mocks.** Real data + computation only; deterministic fakes implement
  the REAL protocol.
- **≥90% line+branch coverage on `src/`**: `uv run pytest tests/ --cov=src --cov-fail-under=90`.
- **Deterministic**: fixed seeds, no untracked RNG, no wall-clock in persisted
  artifacts (`Provenance.wall_time_s == 0.0`).
- **Thin orchestrators in `scripts/`; business logic in `src/`.**
- **No leftover exemplar lineage strings** (aim zero).

## Layer contract

| Surface | Rule |
|---|---|
| `src/moonraker/shuttle_ops.py`, `orbital_logistics.py`, `centrifuge.py`, `mission_results.py` | Pure domain math — no `bond_api`, no `infrastructure` imports |
| `src/moonraker/mission.py` | Thin adapter to the frozen `bond_api` protocol (imports it) |
| `src/moonraker/manuscript_variables.py`, `figures.py` | I/O + rendering; `figures` uses matplotlib only |
| `scripts/` | Thin CLIs (sys.path bootstrap + argv + delegate) |

The domain core stays importable without `bond-api`; `mission.py` is the only
protocol-coupled module.

## Protocol integration

- Local path dependency in `pyproject.toml`: `bond-api = { path = .../bond-api }`.
- `src/moonraker/mission.py` exposes `MissionProvider` at module top level
  (slug `moonraker`), implements the five stages, and registers domain functions
  as gadgets with `bond_api.registry.GadgetRegistry`.
- Run `uv sync --extra dev` after editing `pyproject.toml` (a fresh scaffold's
  `.venv` has no deps).

## Manuscript discipline

- Numeric metrics are injected from `manuscript/config.yaml` +
  `src/moonraker/manuscript_variables.py`; never hand-author numbers in prose.
- `scripts/z_generate_manuscript_variables.py` is strict by default (requires
  `output/data/mission_results.json`); `--allow-draft` relaxes it.

## Verification (before "done")

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo Clean
grep -r "MagicMock\|mocker.patch\|unittest.mock" tests/ || echo Clean
git status --short   # clean after your commit
```

## See also

- `README.md` — quick orientation.
- `docs/agent_instructions.md` — behavioral rules.
- `docs/architecture.md` — layer boundaries.
- `docs/testing_philosophy.md` — zero-mock + coverage mechanics.
- `TODO.md` — what is built and declared integration points.
- BOND suite skill: `bond-suite-package-development` (references
  `bond-api-phase1.md` = the frozen protocol).
