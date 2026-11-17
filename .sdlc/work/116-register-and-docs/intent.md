---
id: 116
slug: register-and-docs
tier: 1
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: [2026-11-17-65, 2026-11-17-66, 2026-11-17-28]
depends_on:
serves: none
---

# 116 — Correct the work/ comments, idea's themes and the tracker docs

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Three things still read wrong after today's changes:

- **2026-11-17-65:** six `#` comments in `scripts/sdlc.py` still call the change folder `work/`:
  above `ENTRY_RE`, `OPEN_ITEM_RE`, `DOC_TEMPLATES`, `LAST_ID`, `config`'s `"work"` key, and the
  trackers section. 102 brought the docstrings up to date but left comments out of its scope.
- **2026-11-17-66:** `/sdlc:idea --themes` leaves out entries tagged `[building]` but not those an
  open change's `idea:` names. Since 100, the `idea:` line is all that marks a seed taken, so it
  may propose a `Theme:` for a seed being built. That's harmless (an update, which `inbox-commit`
  allows), but it could read `status`'s `building` list to match.
- **2026-11-17-28:** AGENTS.md points at CONTRIBUTING.md's *Writing a tracker* for the tracker
  interface, which leaves out the intake methods core calls when a tracker has them: `mark()`,
  `unmark()`, `needs_info()`, `open_marks()`, `open_numbers()`, `closed_by()`.

## Outcome

- No comment in `scripts/sdlc.py` calls the change folder `work/`, except where it names the old
  `HISTORY_WORK` on purpose.
- `/sdlc:idea --themes` proposes no theme for a seed an open change's `idea:` or `fixes:` names.
- CONTRIBUTING.md's *Writing a tracker* lists every intake method core calls, each with what it
  does and when core calls it.
- A test pins the themes rule.
- **Serves no outcome:** these are corrections to the plugin's own text and one skill's reading.

## Affected

- **Area:** `sdlc.py`'s comments, the idea skill, the contributor docs.
- **Files & components:** `scripts/sdlc.py`, `skills/idea/SKILL.md` (and `sdlc.py`'s themes
  listing if it is the script's), `docs/CONTRIBUTING.md`, a test.
- **Downstream:** contributors, and anyone running `/sdlc:idea --themes`.
- **Contracts:** `HISTORY_WORK` stays named where history is read; the register is committed only
  by `inbox-commit`.

## Constraints

- Comments only in `sdlc.py`'s first part: no behaviour change.
- The themes rule reads the open changes the way `status` does (`_open_claims()`), not a copy.

## Approach

Reword the six comments. Have the themes listing skip what `_open_claims()` returns, in the
script if the listing is there, else in the skill by reading `status`'s `building`. Add the six
intake methods to CONTRIBUTING's section from `scripts/trackers/github.py` and the core calls.

## Open questions

- None.
