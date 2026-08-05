# docs/ — Agent-Facing Documentation Hub (moonraker / DRAX)

Technical overview of the moonraker documentation tree: what each file owns, how
the tree is kept true, and what to update when the code moves.

Start at `agent_instructions.md`. It is the gate for any modification to this
package, code or prose.

## Index

| File | Owns | Status |
|---|---|---|
| `README.md` | Index of this directory and a pointer to documentation elsewhere in the package | Hand-maintained |
| `AGENTS.md` | This overview: ownership boundaries and update triggers | Hand-maintained |
| `agent_instructions.md` | Hard rules, the edit loop, the verification checklist, known failure modes | Hand-maintained |
| `architecture.md` | Layer contract, per-module description of `src/`, the `MissionProvider` implementation, data flow | Hand-maintained |
| `testing_philosophy.md` | Zero-mock doctrine, per-file test coverage map, determinism, how to write a binding test | Hand-maintained |
| `_generated/COUNTS.md` | Measured test count and coverage | Regenerated from the gate — do not hand-edit without re-running it |

## Ownership boundaries

Each fact lives in exactly one place. Duplicating it is how drift starts.

| Fact | Canonical home |
|---|---|
| What a module computes | `architecture.md` (one line each also in the root `README.md` table) |
| Why a test is shaped the way it is | `testing_philosophy.md` |
| What an agent may and may not do | `agent_instructions.md` |
| Measured coverage / test count | `_generated/COUNTS.md` |
| Numeric mission results | `output/data/manuscript_variables.json`, via tokens in `manuscript/` |
| Mission parameters | `manuscript/config.yaml` → `mission:` (mirrored by `MISSION_DEFAULTS`) |
| Remaining work | `../TODO.md` |

## Update triggers

| If you… | Update |
|---|---|
| Add or remove a module in `src/moonraker/` | `architecture.md`, root `README.md` table, `src/moonraker/__init__.py` docstring, manuscript methodology |
| Add or remove a test file | `testing_philosophy.md` coverage table |
| Change a mission parameter | `manuscript/config.yaml`, `MISSION_DEFAULTS`, manuscript experimental setup table |
| Publish a new metric | `mission_results.compute_mission_results`, then reference the token — never type the number |
| Change the protocol adapter's internals | `architecture.md` §MissionProvider (and stop if you are changing its *shape*) |
| Re-run the gate | `_generated/COUNTS.md` |

## Conventions

- **Read-first:** `agent_instructions.md` before any modification.
- **Layer isolation:** the domain core is pure; only `mission.py` imports
  `bond_api`; scripts hold no arithmetic.
- **Zero mocks:** real computation only, enforced across the suite.
- **Determinism:** no RNG, no wall-clock in persisted artifacts.
- **No hand-authored metrics:** every published number is injected from the
  canonical computation.
- **Truth over tidiness:** where the model disagrees with the film or an earlier
  draft, the documentation records the model's answer.

## Verification

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```
