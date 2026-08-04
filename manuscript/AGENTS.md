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
| `00_abstract.md` … `09_*` | Tokenised prose sections (results injected) |
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

All three figures (timeline, orbit, centrifuge) are produced by
`src/moonraker/figures.py` into `output/figures/` and referenced via Pandoc-
crossref — never hardcoded numbers or raw `\ref{}`. See `SYNTAX.md`.
