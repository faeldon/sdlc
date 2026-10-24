---
id: 002
slug: setup-lifecycle
tier: 2
impact: minor
stage: shipped
created: 2026-10-24
updated: 2026-10-24
shipped: 2026-10-24
idea:
depends_on:
serves: none
---

# 002 — Keep a host's setup current, resettable and removable

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`/sdlc:setup` copies `defaults/SDLC.md`, `REVIEW.md`, `HEALTH.md`, `PRODUCT.md` and `PROJECT.md`
into a host once, after which the host owns them, and a host may override any of `templates/` in
`.sdlc/templates/`. Setup only covers a repo's first install, and nothing covers its life after:

- **Updating.** `claude plugin update sdlc@sdlc` changes none of those copies, and nothing says the
  defaults moved. Rerunning setup doesn't help: `readiness` only checks that a doc exists and has
  no `<` prompts left, so a copy missing a new default section, still carrying a removed review
  bullet, or a template override whose shape changed, all read `ok`. The same goes for
  `.sdlc/config.toml`: a key added, renamed or dropped in a newer version isn't reported, so a key
  the plugin no longer reads is silently ignored, and a new key takes its default without anyone
  choosing it.
- **Resetting.** A host that edited a copied doc or a template override and wants the plugin's
  version back has to find it in the plugin cache and copy it by hand, working out for itself
  which of its own edits it loses.
- **Uninstalling.** Nothing takes setup back out. Setup writes `.sdlc/`, a `.claude/worktrees/`
  line in `.gitignore`, allow rules in `.claude/settings.json`, and possibly an `AGENTS.md`, a
  one-line `CLAUDE.md`, or additions to an existing one. A host that stops using the plugin
  removes those by memory, while open changes may still sit in worktrees, on branches and in open
  GitHub issues.

This repo already guards against drift in its own copies: `tests/test_defaults.py` checks that
`.sdlc/SDLC.md` and `.sdlc/REVIEW.md` keep every default heading in order and every default review
bullet word for word. Hosts get no such check, so the process improvements a release makes reach
them only if someone diffs the files by hand.

## Outcome

- **Refresh.** Rerunning `/sdlc:setup` on a repo set up by an older version reports, per copied
  doc, the default sections and review bullets it lacks and the ones the defaults no longer have,
  and per `.sdlc/templates/` override, that its plugin template changed; and drafts the additions
  as diffs behind setup's single WAIT. It reports `config.toml` keys that are unknown, renamed or
  deprecated, and new keys the host may want to set, each with what it does.
- **Breaking kept apart.** What the host wrote is told apart from what's out of date: a section it
  added or reworded is shown and never overwritten. A change in a release that breaks a host's
  modified copy (a key renamed, a template field the script now reads) is reported as **breaking**,
  apart from the optional refreshes.
- **Reset.** A host can ask for one copied doc or template override, or all of them, back at the
  plugin's current default, and sees exactly what it loses (its own sections and edits, as a diff)
  before the WAIT.
- **Uninstall.** A host can ask setup to list everything it wrote and, after one approval, remove
  it. It first lists open changes (worktrees, branches, issues) and refuses while any are open,
  saying to close or drop them. It leaves `work/` history alone and commits nothing.
- **Tests prove it.** A scratch repo set up from older defaults reports the expected drift and none
  of its own additions; one reset gets the current defaults back; one uninstalled has none of
  setup's files and every file it had before.

## Affected

- **Area:** setup and readiness, and the shipped defaults and templates
- **Files & components:** `scripts/sdlc.py` (`cmd_readiness`, likely new subcommands for drift,
  reset and uninstall, `load_config`'s key handling), `skills/setup/SKILL.md` (perhaps a separate
  skill for uninstall), `defaults/`, `templates/`, `docs/REFERENCE.md`, `README.md`'s update
  section, and tests (`test_sdlc.py`, `test_adoption.py`, `test_skills.py`)
- **Downstream:** every host that has run setup and later updates or leaves the plugin: live
  consumers who didn't write these files' defaults and won't read the code
- **Contracts:** "Mechanism vs. policy" (the host owns its copies after setup), setup's single WAIT
  and narrow `allowed-tools`, "one shape for the shipped docs" (what makes comparing headings and
  bullets possible at all), and O2's nothing lost: uninstall is the one path here that removes
  files from a host

## Constraints

- Never overwrite or remove a host's file without a diff shown and a yes. A reset shows what it
  discards; an uninstall lists every path.
- Uninstall never touches an open change's worktree, branch, folder or issue, and refuses while
  any are open.
- Uninstall removes only what setup wrote: in a `CLAUDE.md`/`AGENTS.md` or `.gitignore` it didn't
  create, only the lines it added; in `.claude/settings.json`, only the plugin's rules.
- Setup still commits nothing, and none of this pushes.
- Keys are read as text, never through YAML or a round-trip, as with `stamp_shipped`.
- Nothing in the comparison may depend on this repo's own layout (`test_nothing_local`).
- A host with no copies (every doc falling back to a default) has nothing to refresh or reset.

## Open questions

- ~~How does setup know which version a host's copy came from: a stamp written at setup (in config,
  or in each doc's frontmatter, which the shape rules restrict), the plugin's git history of
  `defaults/`, or no stamp, comparing against current defaults only?~~ Resolved: a manifest, `.sdlc/setup.json`, written by `sdlc.py record` with the plugin version and a hash of each section and bullet of each default as copied; no manifest falls back to a two-way comparison (spec R1, R3)
- ~~How is a "breaking" change declared: by the release that makes it (a registry in `sdlc.py`, a
  changelog entry), or inferred from the diff?~~ Resolved: by the release, in `sdlc.py`: `RETIRED_KEYS` for config keys and `TEMPLATE_READS` for what the script reads from each template; breaking is what the plugin would now misread (R4–R6)
- ~~Does drift belong in `readiness` (`warn` items), in a new subcommand setup calls, or also in
  `/sdlc:status`, so it shows without anyone rerunning setup?~~ Resolved: a read-only `sdlc.py drift` that setup runs, a `drift` item in `readiness`, and one line in `status` when the manifest is older than the plugin (R12)
- ~~Should a host's rewording of a default review bullet count as drift, or only a bullet it lacks?~~ Resolved: a host's rewording is a host edit, never drift alone; it is reported only as a conflict when the default changed that bullet too (R2)
- ~~Should drift in the `AGENTS.md`/`CLAUDE.md` invariants setup proposed count, or only files copied
  from `defaults/` and `templates/`?~~ Resolved: only files from `defaults/` and `templates/`; the policy doc is the host's
- ~~How does uninstall tell the lines setup added from the host's own, with no record of what setup
  wrote? Does setup need to start writing a manifest?~~ Resolved: the manifest records what setup created; uninstall never edits `AGENTS.md`/`CLAUDE.md`, and lists their lines naming the plugin instead (R10)
- ~~Are reset and uninstall arguments to `/sdlc:setup` (`reset`, `uninstall`) or skills of their
  own? A separate skill gets its own WAIT and `allowed-tools`, which matters for one that removes
  files.~~ Resolved: reset is a `/sdlc:setup reset` argument; uninstall is its own skill, `/sdlc:uninstall`, so setup never carries a removal rule (R8, R11)
- ~~On uninstall, what happens to `landed` issues GitHub hasn't closed yet, `.sdlc/last-id`, and
  the `Close`/`Drop` history? Is keeping them the right default?~~ Resolved: issues, tags and history are kept; `.sdlc/last-id` goes with `.sdlc/`, since `next_id()` re-seeds from the `Close`/`Drop` history (R10)
