# Manuscript — moonraker (mission DRAX)

Repository-wide agent rules: [`../docs/agent_instructions.md`](../docs/agent_instructions.md).
This file covers manuscript-specific editing: file roles, `{{VARIABLE}}` token
protocol, and figure references.

## File inventory

| File | Role | Tokens |
|---|---|---|
| `00_abstract.md` | Abstract + summary | `BOND_TITLE`, `BOND_SUBTITLE`, `SHUTTLE_*`, `ORBIT_*`, `CENTRIFUGE_*` |
| `01_introduction.md` | Introduction: the three concept areas across seven domain modules, plus reader's guide | `BOND_TITLE`, `CONFIG_*` |
| `02_methodology.md` | Models: CPM + crashing, Kepler + Hohmann + Clohessy–Wiltshire, g-profile + regimen | `CONFIG_*` |
| `03_results.md` | All results + all five figures | `SHUTTLE_*`, `ORBIT_*`, `TRANSFER_*`, `RENDEZVOUS_*`, `CENTRIFUGE_*`, `TRAINING_*`, `CRASH_*`, `CONFIG_*` |
| `04_conclusion.md` | Conclusion, incl. the centrifuge negative verdict | `BOND_TITLE`, `CONFIG_*`, `SHUTTLE_*`, `ORBIT_*`, `TRANSFER_*`, `CENTRIFUGE_*`, `TRAINING_*`, `CRASH_*` |
| `05_experimental_setup.md` | Parameters + environment | `CONFIG_*`, `PYTHON_VERSION`, `PLATFORM` |
| `06_reproducibility.md` | Determinism guarantees, re-derivation table, verification gate | — |
| `07_scope_and_related_work.md` | Explicit non-goals + a model→module→source table | `SHUTTLE_TOTAL_MIN` |
| `99_references.md` | Bibliography | — |
| `config.yaml` | Paper identity + `mission:` parameter block (source of truth) | — |

## Token protocol

Numeric values that come from computation MUST use `{{TOKEN}}` syntax. The
pipeline:

1. `scripts/z_generate_manuscript_variables.py` calls
   `moonraker.manuscript_variables.generate_variables()`.
2. It combines `manuscript/config.yaml` with
   `moonraker/mission_results.compute_mission_results()`.
3. The script writes `output/data/manuscript_variables.json` and resolves the
   numbered sections into `output/manuscript/`.

To add a token: add a key in `generate_variables()` (or, for a computed metric,
in `mission_results.compute_mission_results()`), use it in a section, and the
live cross-reference test (`test_all_manuscript_tokens_are_generated`) will
enforce that every section token exists.

Two cautions learned here. **Never write a literal `{{...}}` example inside a
numbered section** — the cross-reference test reads it as a real token and
fails; describe it in words instead, as this guide file may not (guide files are
excluded from resolution). And **check claims against the resolved copies under
`output/manuscript/`**, not the templates: a sentence can be true about a token
and false about its value, which is how a "not certified" verdict once sat
beside the words "comfortably inside the tolerance envelope".

## Figures

| Label | File (under `output/figures/`) | Generator |
|---|---|---|
| `#fig:timeline` | `timeline_critical_path.png` | `moonraker.figures.render_timeline_figure` |
| `#fig:orbit` | `orbit_period_windows.png` | `moonraker.figures.render_orbit_figure` |
| `#fig:centrifuge` | `centrifuge_g_profile.png` | `moonraker.figures.render_centrifuge_figure` |
| `#fig:hohmann` | `hohmann_transfer.png` | `moonraker.figures.render_hohmann_figure` |
| `#fig:training` | `training_weekly_load.png` | `moonraker.figures.render_training_figure` |

Refer to figures with Pandoc-crossref `[@fig:timeline]` and the markdown image
syntax `![caption](../output/figures/NAME.png){#fig:label}`.
