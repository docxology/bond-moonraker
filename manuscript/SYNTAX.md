# Manuscript syntax — moonraker (DRAX)

## `{{TOKEN}}` substitution

Numeric metrics use `{{TOKEN}}` syntax. Tokens come from
`src/moonraker/manuscript_variables.generate_variables()`, which combines
`manuscript/config.yaml` with the deterministic mission results.

To add a token: add a key in `generate_variables()`, use it in a numbered
section, and rely on `test_all_manuscript_tokens_are_generated` to keep prose
and generator in sync.

## Figures (Pandoc-crossref)

Reference figures with a markdown image and a label:

```markdown
![The shuttle-hijack critical-path Gantt chart.](../output/figures/timeline_critical_path.png){#fig:timeline}
```

Then cite in prose with `@fig:timeline` (narrative) or `[@fig:orbit]`
(parenthetical). Figure registry:

| Label | File |
|---|---|
| `#fig:timeline` | `../output/figures/timeline_critical_path.png` |
| `#fig:orbit` | `../output/figures/orbit_period_windows.png` |
| `#fig:centrifuge` | `../output/figures/centrifuge_g_profile.png` |

## Citations

Use Pandoc citation keys from `references.bib`, rendered via `[@key]` /
`@key`.
