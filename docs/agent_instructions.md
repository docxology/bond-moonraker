# Agent Instructions — moonraker (mission DRAX)

Read-first protocol: before modifying moonraker, internalise these rules. This
is a `PROJECT BOND` package implementing the frozen BOND-API `MissionProvider`
protocol for the DRAX mission.

## Hard rules

1. **Zero mocks.** No `unittest.mock`, `MagicMock`, `@patch`, `create_autospec`
   anywhere in `tests/`. Tests exercise real computation through real
   parameters. A mock can pass while the math is wrong; real data cannot.
2. **Thin orchestrators, fat core.** Business logic lives in `src/moonraker/`;
   `scripts/` only bootstraps `sys.path`, parses argv, and delegates. No math
   in scripts.
3. **Pure domain core.** `shuttle_ops.py`, `orbital_logistics.py`,
   `centrifuge.py`, `mission_results.py` import nothing but stdlib/math — no
   `bond_api`, no `infrastructure`. Only `mission.py` imports `bond_api`.
4. **Deterministic.** Fixed seeds, no untracked RNG, no wall-clock in
   persisted artifacts. `Provenance.wall_time_s == 0.0`; `input_hash` is stable.
5. **Manuscript metrics are injected.** Numeric results come from
   `manuscript/config.yaml` + `moonraker/manuscript_variables.py` — never
   hand-author numbers in prose.
6. **Coverage gate ≥90%.** `uv run pytest tests/ --cov=src --cov-fail-under=90`
   and keep ruff + mypy clean before committing.
7. **Scope.** Work only inside this package dir; local-only, never push.

## Verification checklist (before "done")

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo Clean
git status --short   # clean after your commit
```

## Consequences of skipping

- Introducing a mock → the zero-mock gate will catch it; worse, it can mask a
  real numerical bug in the hijack/orbit/centrifuge models.
- Math in `scripts/` → breaks the thin-orchestrator rule and the coverage model.
- Hardcoding a result in the manuscript → the value drifts from config and the
  injected tokens are no longer the source of truth.
