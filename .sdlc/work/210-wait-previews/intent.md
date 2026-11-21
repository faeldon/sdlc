---
id: 210
slug: wait-previews
tier: 2
impact: minor
stage: shipped
created: 2026-11-21
opened: 2026-11-21T03:58Z
updated: 2026-11-21
shipped: 2026-11-21
idea: 2026-11-21-2
depends_on:
serves: none
origin: self
---

# 210 — Each WAIT shows its draft in the dialog's preview

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

In the seed's words: "Every skill's WAIT shows the draft it approves inside its AskUserQuestion
dialog, as the preview of its yes option: the seed or bug entry, the intent, the spec's
requirements, the commit message and files, whatever that yes writes. A long draft shows its
approving part and names the file holding the rest. Today the draft is shown only as message text
before the dialog, so a draft that never reached the screen, or scrolled off it, is approved
unseen. That happened on 2026-11-21, when seed 2026-11-21-1 was committed without the person ever
seeing its text. test_every_wait_asks_in_a_dialog would also check that each WAIT names what its
preview holds."

On 2026-11-21 the model drafted the `/sdlc:idea` entry only in its reasoning, and the dialog asked
"Append this idea…" with nothing visible above it; the person said yes and it was committed
(`04a2d17`). Every writing skill has the same gap: its rule is "show it, then ask", and nothing
checks the showing happened. The factory's `land` is the one exception: it already puts
`land-check`'s `shown` in the yes option's preview.

## Outcome

- Every skill with a WAIT puts what its yes writes in the `preview` of its yes options: the
  entry, the intent, the spec's requirements, the commit message and paths, the files and edits. A
  long draft shows its approving part and names the file holding the rest.
- `tests/test_skills.py`'s `test_every_wait_asks_in_a_dialog` also fails on a WAIT whose text
  doesn't say what its preview holds.
- Where a script already renders the question (`preflight --question`, `land-check`'s `shown`,
  `start`'s `question`), it also renders the preview, so no skill words its own.

## Affected

- **Area:** every writing skill's WAIT step, and the scripts that word questions.
- **Files & components:** `skills/*/SKILL.md` (intent, spec, ship, close, drop, setup, release,
  publish, retro, uninstall, bug, triage, idea; the factory's spec, build, eval, review, land,
  decide); `scripts/sdlc.py`'s question renderers; `tests/test_skills.py`; `docs/CONTRIBUTING.md`
  where the WAIT rule is.
- **Downstream:** every person approving anything; the metrics that read a dialog's answer as the
  approval.
- **Contracts:** the skills' invariants in `tests/test_skills.py` (one `WAIT` heading, 2–4
  answers, only a chosen yes approves); *Narrow `allowed-tools`*; `defaults/` and `templates/`
  untouched.

## Constraints

- The literal question text and its answers don't change: only a preview is added, since metrics
  read the answer in the WAIT's span.
- A skill with no dialog tool still asks as text, with the draft above it.
- Nothing is written before the yes.

## Open questions

- ~~How long can a preview be before it's cut, and what does the cut part say?~~ Resolved: 40
  lines; the approving part is kept and the last line is `… <k> more lines in <path>` (spec R3, R4)
- ~~Is the preview written by the script for every skill, or only where a script already words the
  question?~~ Resolved: only where a script words the question; the rest is the skill's own
  drafted text (spec R5–R9)
- ~~Does a WAIT with nothing to preview (a retirement, say) need one?~~ Resolved: no WAIT is
  exempt; a retirement previews the entry and its reason (spec R9)
