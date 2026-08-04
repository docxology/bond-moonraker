# docs/ — Agent-Facing Documentation Hub (moonraker / DRAX)

Technical overview of the moonraker documentation tree. Read
`agent_instructions.md` first — it is the gate for any edit.

## Index

| File | Purpose | Status |
|---|---|---|
| `README.md` | This index | Current |
| `AGENTS.md` | Technical overview of this tree | Current |
| `agent_instructions.md` | Behavioral rules (read-first) | Current |
| `architecture.md` | Layer boundaries + data flow | Current |
| `testing_philosophy.md` | Zero-mock + coverage mechanics | Current |
| `_generated/COUNTS.md` | Live test count + coverage (do not hand-edit) | Generated |

## Conventions

- **Read-first:** start at `agent_instructions.md` before any modification.
- **Layer isolation:** domain core is pure; only `mission.py` imports
  `bond_api`; scripts are thin.
- **Zero-mock:** enforced by the suite; real computation only.
- **Determinism:** no RNG/wall-clock in persisted artifacts.

## Verification

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
```
