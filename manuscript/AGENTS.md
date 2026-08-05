---
title: "Manuscript directory: moonraker (DRAX)"
type: "manuscript_guide"
version: "0.2.0"
---

# Manuscript (`projects/working/bond/moonraker/manuscript/`)

Agent rules for this directory. Repository-wide rules:
[`../docs/agent_instructions.md`](../docs/agent_instructions.md).

## File roles

| File | Role |
|---|---|
| `00_abstract.md` … `07_scope_and_related_work.md`, `99_references.md` | Tokenised prose sections (results injected) |
| `preamble.md` | Rendering preamble |
| `README.md` | Manuscript-specific editing guide: file inventory, token protocol, figure table |
| `config.yaml` | Identity + the `mission:` parameter block (source of truth) |
| `config.yaml.example` | Reference copy of the config schema |
| `references.bib` | BibTeX bibliography |
| `SYNTAX.md` | `{{TOKEN}}`, figure and citation syntax |

## Token protocol

Every numeric metric in prose uses `{{TOKEN}}` from
`moonraker/manuscript_variables.generate_variables()`. The live cross-reference
test (`test_manuscript_variables.py::test_all_manuscript_tokens_are_generated`)
fails if a numbered section uses a token the generator does not provide.

Adding a token: add the key in `generate_variables()`, reference it in prose,
and the gate enforces consistency.

## Figure protocol

All five figures — timeline critical path, orbit period + launch windows,
centrifuge g-profile, Hohmann transfer geometry, and weekly training load — are
produced by `src/moonraker/figures.py` into `output/figures/` and referenced via
Pandoc-crossref, never hardcoded numbers or raw `\ref{}`. See `SYNTAX.md` and
the figure table in `README.md`.

## Honesty rule

Report what the model computes. Where a result contradicts the film or an
earlier draft — as the centrifuge certification verdict does — the prose
changes, not the model. Verdicts the prose leans on are pinned by tests in
`tests/test_mission_results.py` so they cannot silently invert.
