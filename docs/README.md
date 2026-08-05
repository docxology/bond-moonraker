# docs/ — moonraker (mission DRAX)

Everything an agent or developer needs to work inside the moonraker package
that is longer than a line in the root `README.md`. Four hand-maintained files
and one generated one.

| File | What it holds | Read it when |
|---|---|---|
| `README.md` | This index | You are orienting |
| `AGENTS.md` | Technical overview of this docs tree and its conventions | You are adding or restructuring documentation |
| `agent_instructions.md` | Operational rules, the edit loop, verification checklist, and the failure modes this package has actually hit | **Before** any code or prose change |
| `architecture.md` | Module-by-module architecture of `src/`, the layer contract, how `mission.py` implements the frozen `MissionProvider`, and the end-to-end data flow | You need to know where something belongs or what a module computes |
| `testing_philosophy.md` | The zero-mock / real-data / determinism doctrine as it applies here, what each test file binds, and how to write a test that can fail | You are adding or changing tests |
| `_generated/COUNTS.md` | Measured test count and coverage, with the date measured | You want a real number — never quote one from prose |

## Where the rest of the documentation lives

| Location | Contents |
|---|---|
| `../README.md` | Purpose, film/concept mapping, every `src/` module in one line, install + test commands, the `MissionProvider` surface |
| `../AGENTS.md` | Scope constraints, layer contract table, protocol integration, verification commands |
| `../TODO.md` | Real remaining work and declared integration points |
| `../manuscript/` | The paper: `00_abstract` … `07_scope_and_related_work`, `99_references`, plus `config.yaml`, `references.bib` and the `README`/`AGENTS`/`SYNTAX` guides |
| `../src/README.md`, `../src/AGENTS.md`, `../src/STYLE.md` | Source-tree conventions |
| `../tests/README.md`, `../tests/PATTERNS.md` | Test-tree conventions |
| `../scripts/README.md`, `../scripts/CONVENTIONS.md` | Orchestrator conventions |
| `../STANDALONE.md` | The fork contract — why this package carries no `infrastructure/` dependency |

## One rule for this directory

Documentation here describes what the code **does**, verified against the code
at the time of writing. Where a number is involved, either cite
`_generated/COUNTS.md` / `output/data/manuscript_variables.json` or describe the
gate that produces it. A figure typed into prose is stale from the next commit
onward.
