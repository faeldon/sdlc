---
id: 060
slug: rework-as-declared-fix
tier: 2
impact: minor
stage: shipped
created: 2026-11-16
updated: 2026-11-16
shipped: 2026-11-16
idea: 2026-10-25-12
depends_on:
serves: [O4]
---

# 060 — Rework as a declared fix, with surviving lines as the cross-check

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Retro's `rework` is meant to count a later change fixing an earlier one, but it pairs any two
changes closed within `REWORK_DAYS` (7) that share a file. Since 021 it leaves out
`rework_common`, the files more than a third of the window's changes touch. Even so, the current
window, 19 changes since the retrospective of 2026-11-04, holds **50 pairs**, and as far as anyone
knows none of those changes was written to fix the other: most are same-week changes adding to a
shared skill, test or tracker file. 046-push-at-close "reworks" 041-windows-lock through
`scripts/trackers/github.py` and `tests/test_adoption.py`; 047-cut-extra-stops "reworks"
042-permission-stops through `scripts/metrics.py`. The seed counted 42 in the window before.

A figure that high and that loose can't direct anything: a retrospective ignores it or argues it
away. The direction doc carries M5 ("Rework and first time say what happened") because "rework
still counts shared files, not fixes". `[bug]` entries already record `Introduced by:` and close
writes `Sdlc-Fixes:`, so the plugin can say what a fix answers to; rework is the one signal still
guessed from file overlap.

## Outcome

- A change can say which earlier changes it reworks, on a `reworks:` frontmatter line (one or more
  change ids, read as text like `depends_on:`). `/sdlc:intent` asks for it when the problem traces
  to an earlier change, and `check` refuses an id that names no closed, dropped or open change.
- Retro's rework counts these declared links, whatever the gap in days, and a fixed bug whose
  `Introduced by:` names a change as one too (`via: bug`).
- Retro cross-checks by blame: lines an earlier change added that a later one in the window
  modified or deleted. Appending to a shared file no longer counts; replacing what the earlier
  change wrote does. A hit with no `reworks:` link is listed as a question for the retrospective,
  never counted.
- The file pairs, `REWORK_DAYS` as a match rule and `rework_common` go. Tests pin the declared
  count and the blame cross-check, an append that doesn't count and a replacement that does.
- Close's in-change rework (`Sdlc-Rework`) is unchanged.
- **Moves O4:** a retrospective's rework count holds only changes that fixed an earlier one,
  declared or found by blame, so a direction call can rest on it instead of being argued away.

## Affected

- **Area:** the retrospective's rework signal, and the intent stage that feeds it.
- **Files & components:** `scripts/sdlc.py` (retro's rework, `REWORK_DAYS`, `rework_common`,
  `check`, frontmatter reading beside `depends_on:`); `skills/intent/SKILL.md` (the question),
  `skills/retro/SKILL.md` (how rework reads); `templates/intent.md` if the key gets a line there;
  `tests/test_retro.py`, `tests/test_sdlc.py`, `tests/test_skills.py`; `docs/REFERENCE.md`,
  `AGENTS.md`.
- **Downstream:** `/sdlc:retro` and the direction doc it writes; every host's retrospectives (the
  figure's meaning changes, and a window straddling the change mixes intents with and without
  `reworks:`); hosts get the new key and question with the plugin update, and a changed
  `templates/intent.md` through setup (`templates/` is irreversible).
- **Contracts:** frontmatter read as text, never YAML; `stamp_shipped` edits lines in place;
  `fixes:` keeps its meaning (inbox bugs, not changes); `TEMPLATE_READS` and `drift` if the template
  changes; metrics trailers (`Sdlc-Rework` untouched); the intent skill's WAIT unchanged.

## Constraints

- A history full of intents without `reworks:` still reads: none declared counts zero, never an
  error.
- Blame findings never count on their own; they are questions for the retrospective, so a planned
  follow-up isn't called a fix.
- `reworks:` stays its own key, apart from `fixes:`: a change can carry both, a bug it fixes and
  the change that let it through, which that bug's `Introduced by:` already records, so retro can
  cross-check the two.
- The intent skill asks only when the problem traces to an earlier change: no new stop for a change
  that doesn't.

## Open questions

- ~~How is the blame cross-check bounded in cost (which windows, which hunks, `git blame` per file
  or `git log -L`)?~~ Resolved: only lines a change in the window removed or replaced, blamed at its
  base, matched to earlier changes in the window; appends cost nothing.
- ~~Does `check` refuse a `reworks:` id that names no closed change, or only one that names
  nothing, since an open change could be reworked too?~~ Resolved: it refuses one naming no closed,
  dropped or open change, reusing the walk it makes for `Introduced by:`.
- ~~Does `templates/intent.md` get a commented `# reworks:` line? It's irreversible for hosts, and
  needs a `TEMPLATE_READS` and drift decision.~~ Resolved: no; the skill writes the line when
  asked, as it does `fixes:` and `closes:`.
- ~~Does the retro skill's process pass change wording beyond "rework", given the direction doc's
  M5 verdict reads this figure?~~ Resolved: its `rework` bullet and the architecture and process
  passes' `rework_common` references are rewritten; `rework_questions` is read as questions.
- ~~Does a `[bug]`'s `Introduced by:` count as declared rework when the fixing change says
  nothing, or only as the cross-check?~~ Resolved: it counts, as `via: bug <id>`, merged with a
  `reworks:` link for the same pair.
