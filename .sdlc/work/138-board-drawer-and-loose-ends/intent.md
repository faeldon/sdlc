---
id: 138
slug: board-drawer-and-loose-ends
tier: 1
impact: patch
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea: [2026-11-18-8, 2026-11-18-10, 2026-11-18-11, 2026-11-18-12]
depends_on:
fixes: [2026-11-18-9]
serves: none
---

# 138 — The board's drawer shows the file asked for, and says when it's empty; three small leftovers tidied

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

**The drawer, `scripts/board.html`:**

- `show()` (`:576`) sets `doc` whenever its fetch resolves, whichever file was asked for last.
  Click two files quickly, and if the older file's response arrives second, the pane shows that
  older file while the list highlights the newer one (2026-11-18-9, found by 124's review). The
  board then misstates what's in a change's folder, and the person reads the wrong file without
  knowing it.
- A `.md` file with no text (`doc.text` is `""`) draws a blank pane: `??` keeps the empty string,
  and the markdown branch renders an empty `div` (2026-11-18-8, left by 124). The drawer looks
  broken where it should say the file is empty, in the style of "This folder holds no file yet."

**Three leftovers from today's landings, each a line or two:**

- `/sdlc-factory:spec`'s WAIT words its question in the skill
  (`plugins/factory/skills/spec/SKILL.md:89`). Since 125, the build gate's question is worded by
  the script (`build_question()`). The spec gate is the one factory gate that isn't
  (2026-11-18-10). The seed itself notes the question's only placeholder is the folder name, so
  little can go wrong in it.
- `templates/findings.md`'s note, and its copy `FINDINGS_HEAD` (`factory.py:268`), still say only
  "the factory's `carry` writes its agents' findings into it". Since 127, the landing writes its
  rounds' findings there too (2026-11-18-11).
- `skills/triage/SKILL.md:55`'s `dangling` bullet offers every dangling issue to be triaged again,
  including one an unpushed commit closes. Since 128, that issue only waits on the push
  (2026-11-18-12).

## Outcome

- Clicking a second file before the first one loads shows the second, and never the first under
  its highlight. A test runs the page's `show()` under the stand-in DOM with two fetches resolving
  out of order, and finds the newer file in `doc`.
- An empty `.md` file shows a note saying the file is empty, never a blank pane. A test renders one
  and finds the note.
- The spec gate's question is printed by `factory.py`, worded once, and the skill asks exactly what
  it prints. Or the seed is retired as not worth it, with the reason. See the open question.
- `templates/findings.md`'s note and `FINDINGS_HEAD` name the landing as a writer, the template's
  pinned test still passes, and `sdlc.py record` has run, so `drift` reports nothing.
- Triage's `dangling` bullet says that an issue an unpushed commit closes waits on the push, and
  isn't offered again.

## Affected

- **Area:** the board's page, the factory's spec skill and script, a template shipped to hosts,
  and triage's skill.
- **Files & components:**
  - `scripts/board.html`: `show()`, and the drawer's paint of a file.
  - `plugins/factory/skills/spec/SKILL.md` and `plugins/factory/scripts/factory.py`: a `spec`
    question beside `build_question()`, and `FINDINGS_HEAD`.
  - `templates/findings.md` and `.sdlc/setup.json`.
  - `skills/triage/SKILL.md`.
  - Tests in `tests/test_board.py`, `tests/test_factory.py` and `tests/test_defaults.py`.
- **Downstream:**
  - The board's viewers.
  - Hosts, which receive `templates/findings.md`'s note: `templates/` is marked irreversible, so
    ship asks for `How to recover:`.
  - The spec skill's WAIT, which `tests/test_skills.py` checks.
  - Depends on no open change. 137 may change the factory's gates too, but not the spec gate's
    wording.
- **Contracts:**
  - The page builds every node with `textContent`.
  - A change to `templates/` reruns `sdlc.py record`.
  - `FINDINGS_HEAD` is a pinned copy of the template's note.
  - Every WAIT asks in a dialog.
  - The factory never imports `sdlc.py`.

## Constraints

- The drawer keeps the behaviour 124 settled: headings below the title, the task-box label, the
  raw toggle.
- The findings note stays a `>` note: `tests/test_defaults.py` keeps a doc's shape.
- `findings.md`'s note changes in place, never into a new section a host's parser would read.

## Open questions

- Is the spec gate's question worth moving into the script, given the seed's own judgment that
  there's nothing in it to get wrong? Or is it retired here as `minor`, with its reason?
- Should the drawer ignore a stale response, by checking that the path matches the one asked for
  last, or cancel it (`AbortController`)? The second also saves a request.

## Approach

- **The drawer:** in `show()`, keep the path asked for last, and set `doc` only when the
  response's path still matches it. In the paint, show a "This file is empty." note for a file
  whose text is `""`. Add both to `tests/test_board.py`'s node-run tests, beside 124's.
- **The findings note:** edit `templates/findings.md`'s note and `FINDINGS_HEAD` together, then run
  `scripts/sdlc.py record` from this change's checkout.
- **Triage:** add half a sentence to its `dangling` bullet.
- **The spec gate:** if kept, add `spec_question()` beside `build_question()`, printed by
  `start … spec`, and have the skill ask what it prints, as the build skill does. Otherwise retire
  2026-11-18-10 with its reason at ship.
- No open nits sit on these paths.
