---
id: 024
slug: bugs-register
tier: 2
impact:
stage: build
created: 2026-10-25
updated: 2026-10-25
idea: 2026-10-25-10
depends_on:
serves: [O4, O2]
---

# 024 — One inbox for seeds, bugs and nits

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Change requests reach the plugin through three registers in three shapes: seeds and a `[bug]` tag
in `work/ideas.md`, linked by title, and review findings in `work/nits.md`, numbered `NNN-n`. The
intake seeds queued behind this one (reports from other sessions, then GitHub issues) will turn
outside reports into entries, and triage will reword and reclassify them: a title link breaks on
the first rewording, and a reclassified report would have to change file and id.

A bug in particular has nowhere to go. Today it is a `[bug]` tag in place of `[seed]`, which
`status` puts first in Next up (`sdlc.py:4065`) and nothing else reads. But a bug isn't a seed: it
has a severity, a repro and something already broken, and wants triage before it waits its turn.
One tag gives nothing to sort by severity, nothing for status or retro to count apart, and nothing
to link a fix to, or to the change that let the bug through, so retro's rework can't tell a planned
follow-up from an escaped defect.

## Outcome

- One `work/inbox.md` holds every change request, tagged `[seed]`, `[building]`, `[bug]` or
  `[nit]`, each with a `YYYY-MM-DD-n` id from one counter and its kind's facts as body lines.
  `work/ideas.md` still reads (a shim until 2.0.0); `work/nits.md` folds in; `sdlc.py
  migrate-inbox` moves a repo over.
- `idea:`, `fixes:`, `After:` and `Groups:` link by id (titles still read), so triage can reword
  or reclassify a report without breaking a link.
- Bugs carry a severity from the process doc; `/sdlc:bug` files, retires and retags them; `status`
  shows open bugs by severity and age, first in Next up.
- `/sdlc:intent <id>` promotes a bug (`fixes: [<id>]`); `/sdlc:ship` retires it; `/sdlc:close`
  writes an `Sdlc-Fixes:` trailer, so history keeps the link.
- `retro` counts bugs reported, fixed and retired in its window by severity, time from report to
  fix, open bugs by age, and escapes per introducing change against its tier.
- **Moves O4:** a retrospective can cite escaped bugs and time-to-fix as evidence about the product,
  not only rework counts that mix defects with follow-ups.
- **Moves O2:** a reported bug stays on record until a change fixes it, and history says which.

## Affected

- **Area:** the registers in `work/`, and everything that reads or writes them: status, check,
  intent, spec, ship, close, retro, setup, uninstall.
- **Files & components:** `scripts/sdlc.py` (the register reader, references, Next up, `check`,
  ship's deletion, close's trailers, retro, `nits`, new `next-entry`, `bugs`, `bug-commit`,
  `migrate-inbox`), `scripts/metrics.py` (`parse_trailers()`), `templates/` (`inbox.md` replacing
  `ideas.md` and `nits.md`; `notes.md`, `direction.md`), `.sdlc/deprecations.toml`, a new
  `skills/bug`, the intent, spec, ship, close, retro, status, setup and uninstall skills, the
  factory's notes text, `docs/REFERENCE.md`, `docs/CONTRIBUTING.md`, `README.md`, `AGENTS.md`,
  `.sdlc/SDLC.md` and `defaults/SDLC.md`, `.sdlc/DIRECTION.md`, `work/ideas.md` and `work/nits.md`
  (migrated), `tests/`.
- **Downstream:** every host's `work/ideas.md` (released) and retro; the trailer contract that
  retro and anyone mining history reads; the local-channel and GitHub-triage seeds, which file into
  the inbox.
- **Contracts:** the trailer contract (extend, never redefine); frontmatter read as text
  (`frontmatter_list()`); a shim with its `deprecations.toml` entry; one WAIT per writing skill;
  only publish pushes; nothing names a host (a bug's repro is written in neutral terms).

## Constraints

- A host with a `work/ideas.md` keeps working untouched until it migrates: no entry, tag or Next up
  order lost.
- Ids rarely collide across parallel branches, and a collision is reported, never silent (nits used
  to rule it out by taking the raising change's number).
- Measuring never refuses: a missing or malformed register is reported, never fatal.
- Release and publish never read the register, as with nits.

## Open questions

- ~~Bug ids: a global `B<n>` (collides across parallel branches) or `NNN-n` from the raising change,
  as nits do? What id does a bug get when no change raised it?~~ Resolved: neither. Every entry in
  the one inbox, nits included, gets a date-based `YYYY-MM-DD-n` from one counter, so intake can
  reword or reclassify a report under one id. Spec R5–R7.
- ~~The `[bug]` tag in `work/ideas.md`: keep reading it as a shim with a deprecation entry, migrate
  it at setup, or drop it with a `drift` breaking note?~~ Resolved: it stays the bug marker, now in
  `work/inbox.md` with a `Severity:` line. It was never released, so it needs no shim; the file it
  lived in gets one. Spec R1–R2.
- ~~Severity scale: fixed words (`high`/`med`/`low`), or the process doc's to define?~~ Resolved:
  the process doc's `- **severity:**` bullet, falling back to the default doc's `high` · `med` ·
  `low`. Spec R10.
- ~~Who writes an entry before the intake seeds exist: a small `/sdlc:bug` skill, `/sdlc:intent`
  offering to file instead of open, or by hand?~~ Resolved: a `/sdlc:bug` skill, filing, retiring
  and retagging from the main checkout through `sdlc.py bug-commit`. Spec R12–R13.
- ~~Does `Sdlc-Fixes:` come from the intent's `fixes:` at close, or from the entries ship
  retired?~~ Resolved: from `fixes:`, with each entry's fields read from the branch's history;
  ship deletes the same ids. Spec R16–R17.
- ~~How retro attributes an escape: only through `introduced_by:` set at triage, or also a
  path-based guess it only reports?~~ Resolved: only a confirmed `Introduced by:`; the rest count
  as unattributed. Spec R12, R18.
