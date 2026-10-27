---
id: 032
slug: process-guide-in-plugin
tier: 2
impact: minor
stage: shipped
created: 2026-10-27
updated: 2026-10-27
shipped: 2026-10-27
idea: 2026-10-27-5
depends_on:
serves: [O1, O2]
---

# 032 — Keep the plugin's process guide in the plugin, and only a host's answers in .sdlc/

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`/sdlc:setup` copies all of `defaults/SDLC.md` (499 lines) and `defaults/REVIEW.md` (69 lines)
into a host, though only a small part of either is the host's. In `SDLC.md` that is its eight `<`
prompts and a few settings: the failure to stop, worktree needs, Stage 1 push-backs, the gate's
prose, the path to users, scans, the always-Tier-2 carve-outs, severity words, change types and
the nit rubric. In `REVIEW.md` it is the failure classes the host adds to the default passes.

The other ~470 lines describe the plugin itself, so a host that edits them only makes its copy
wrong. Keeping a host's ~30 lines while carrying the plugin's updates to the rest is most of what
`drift()`'s block hashes (`doc_units()`) and its three-way compare exist for, and every plugin
update that touches the guide becomes a setup diff each host has to review.

This repo pays the same cost: `.sdlc/SDLC.md` (521 lines) and `.sdlc/REVIEW.md` (102 lines) must
keep every default heading in order and every default review bullet word for word
(`tests/test_defaults.py`), so an edit to either default is made twice, and
`scripts/sdlc.py record` must be rerun before the gate passes.

## Outcome

- Setup writes `.sdlc/SDLC.md` and `.sdlc/REVIEW.md` holding only the host's answers and
  additions, each with a note linking the plugin's guide at the installed version.
- Every skill and factory agent that reads `docs.process` or `docs.review` (bug, intent, retro,
  setup, ship, spec, triage; the factory's spec-writer and code reviewer) reads the plugin's guide
  and the host's answers together, with `config` naming both, so no reader builds the path itself.
- `severities()`, and anything else that parses those docs, finds the host's answers where they now
  live and falls back to the plugin's defaults where the host has none.
- `drift` no longer block-hashes guide text a host doesn't hold. Setup or `status` reports when the
  plugin's guide changed since setup's record, as a note to read, never a refresh and never a
  problem.
- An existing host migrates once: setup cuts its docs to its answers, keeping whatever it edited,
  shown as a diff behind setup's WAIT, as a shim with a `remove_in` in `.sdlc/deprecations.toml`.
- This repo's own `.sdlc/SDLC.md` and `.sdlc/REVIEW.md` hold only its answers, and the "process
  docs track the defaults" invariant in `AGENTS.md` and `tests/test_defaults.py` is replaced by
  whatever the spec settles.
- `HEALTH.md`, `PRODUCT.md`, `PROJECT.md` and the direction doc stay as they are: wholly the host's.
- **Moves O1:** a new host's setup diff shrinks from ~570 lines of copied guide to its answers, so
  it reaches its first closed change having read and filled only what is its own.
- **Moves O2:** a plugin update reaches every host's guide at once. No host keeps a stale copy
  because it skipped a setup diff, and none loses its own answer in a three-way merge.

## Affected

- **Area:** setup's copy and record, `drift`, config's doc resolution, and every reader of the
  process and review docs.
- **Files & components:** `defaults/SDLC.md` and `defaults/REVIEW.md` (possibly split into guide
  and answers templates); in `scripts/sdlc.py`, `load_config()`/`cmd_config()` doc paths and the
  review fallback (`DEFAULTS_DIR / "REVIEW.md"`), `severities()`, `doc_units()`, `drift()`,
  `cmd_record()`, readiness and the migration shim; `skills/setup/SKILL.md` and the seven skills
  and two factory agents above; this repo's `.sdlc/SDLC.md`, `.sdlc/REVIEW.md` and
  `.sdlc/setup.json`; `tests/test_defaults.py` and the drift and setup tests; `AGENTS.md`,
  `docs/REFERENCE.md` and README.
- **Downstream:** every host that has run setup, whose `.sdlc/SDLC.md` and `REVIEW.md` the
  migration rewrites; every session's skills, which read the docs at each stage; retro, which
  reads the process doc's signals.
- **Contracts:** "This repo's process docs track the defaults" (`AGENTS.md`, `test_defaults.py`),
  replaced; "One shape for the shipped docs", which a new answers template must keep; setup's
  record and `drift()`'s `breaking`/`RETIRED_KEYS`/`TEMPLATE_READS`; a shim's
  `.sdlc/deprecations.toml` entry; mechanism vs. policy (the plugin still knows nothing about
  what a host builds); confirm before writing (the migration is behind setup's WAIT).

## Constraints

- A host's own answers and edits are never lost: the migration keeps every block the host
  changed, and shows what it cuts before writing.
- A host that hasn't migrated keeps working until the shim's `remove_in`: skills reading a full
  old-style copy must not break or double the guide.
- `config` stays the only place doc paths are resolved; no skill guesses where the guide lives.
- The guide a host reads is the installed plugin's version: a stale cached copy reads its own
  version's guide, never a mix of two.
- Nothing about a host goes into the plugin's guide; host-specific text stays in the host's file.

## Open questions

- ~~What exactly is a host's "answer"? Do settings like the severity words and change types become
  structured, or stay prose?~~ Resolved: any `doc_units()` block of the host's doc; one with a
  guide block's key replaces it, a new one is added under its parent. The settings stay prose
  blocks.
- ~~How do skills read the two together, and does the host's text append or replace?~~ Resolved:
  `config` gives the guide's path and the host's, each reader reads both; replace by key, add
  otherwise.
- ~~How does the migration tell a host's edit from the plugin's older text, for hosts set up
  before the record?~~ Resolved: a block matching the recorded default's hash or the guide now is
  cut; anything else kept. Without a record, only the guide now is compared, and stale text shows
  as kept in the diff setup shows.
- ~~What replaces `drift`'s three-way compare for these two docs?~~ Resolved: a guide hash and a
  `guide-changed` report; `HEALTH`, `PROJECT`, `PRODUCT` and templates keep today's compare.
- ~~What does "the guide changed" compare, and where does it surface?~~ Resolved: the guide's hash
  in `setup.json`, through `drift` and so setup; `status`'s version nudge already exists.
- ~~What does this repo's `.sdlc/SDLC.md` hold afterwards?~~ Resolved: what setup's own migration
  keeps, its answers and plugin-only additions, reviewed as a diff.
- ~~Which `remove_in` does the migration shim get?~~ Resolved: 1.6.0, since a shim can't go in the
  release that brings it.
