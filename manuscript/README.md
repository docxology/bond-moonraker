# Manuscript — moonraker (mission DRAX)

Repository-wide agent rules: [`../docs/agent_instructions.md`](../docs/agent_instructions.md).
This file covers manuscript-specific editing: file roles, `{{VARIABLE}}` token
protocol, and figure references.

## File inventory

| File | Role | Tokens |
|---|---|---|
| `00_abstract.md` | Abstract + summary | `BOND_TITLE`, `BOND_SUBTITLE`, `SHUTTLE_*`, `ORBIT_*`, `CENTRIFUGE_*` |
| `01_introduction.md` | Introduction + reader's guide | `BOND_TITLE`, `CONFIG_*` |
| `02_methodology.md` | Models (CPM, Kepler, g-profile) | `CONFIG_DEADLINE_MIN`, `CONFIG_RESUPPLY_INTERVAL_DAYS`, `CONFIG_TARGET_G`, `CONFIG_SUSTAIN_S` |
| `03_results.md` | All results + all three figures | `SHUTTLE_*`, `ORBIT_*`, `CENTRIFUGE_*`, `CONFIG_*` |
| `04_conclusion.md` | Conclusion | `BOND_TITLE`, `CONFIG_*`, `SHUTTLE_*`, `ORBIT_*`, `CENTRIFUGE_*` |
| `05_experimental_setup.md` | Parameters + environment | `CONFIG_*`, `PYTHON_VERSION`, `PLATFORM` |
| `06_reproducibility.md` | Determinism + gate | — |
| `07_scope_and_related_work.md` | Scope + literature | — |
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

To add a token: add a key in `generate_variables()`, use it in a section, and
the live cross-reference test (`test_all_manuscript_tokens_are_generated`)
will enforce that every section token exists.

## Figures

| Label | File (under `output/figures/`) | Generator |
|---|---|---|
| `#fig:timeline` | `timeline_critical_path.png` | `moonraker.figures.render_timeline_figure` |
| `#fig:orbit` | `orbit_period_windows.png` | `moonraker.figures.render_orbit_figure` |
| `#fig:centrifuge` | `centrifuge_g_profile.png` | `moonraker.figures.render_centrifuge_figure` |

Refer to figures with Pandoc-crossref `[@fig:timeline]` and the markdown image
syntax `![caption](../output/figures/NAME.png){#fig:label}`.
