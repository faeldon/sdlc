---
id: 056
slug: ship-reads-rare-branches
tier: 2
impact: patch
stage: shipped
created: 2026-11-13
updated: 2026-11-13
shipped: 2026-11-13
idea: 2026-11-04-6
depends_on:
serves: none
---

# 056 — Ship reads its rare branches only when preflight says they apply

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`skills/ship/SKILL.md` is the plugin's largest skill, now 543 lines (487 when the retrospective of
2026-11-04 raised this), about 8,500 tokens, and every ship run reads all of it. 8 of that window's
14 changes edited it, each adding a branch every run then reads whether it applies or not: agent
verdicts from a factory run, Pre-existing findings filed as bugs, the `closes:` issues asked about
one at a time, the `How to recover:` paragraph for an irreversible path, undone items. Most runs
need none of them, and `preflight` already says which apply (its `undone`, `closes` and `risk`
parts, and whether a `decision.md` exists), but the skill doesn't use that to skip anything. So
every feature makes every plain ship more expensive, and the one file every change has to edit
grows.

## Outcome

- A ship run on a plain change (nothing undone, no `closes:`, no sensitive or irreversible path,
  no factory files) reads `SKILL.md` alone, and that file is measurably shorter than today's 543
  lines; the spec names the before and after.
- Each rare branch is a file beside `SKILL.md` that ship reads only when the `preflight` part that
  calls for it is non-empty, and `SKILL.md` says, for each, the condition that reads it.
- The WAIT heading, the question `preflight --question` words, and every rule that binds every run
  stay in `SKILL.md`.
- `tests/test_skills.py` covers each side file's bash blocks as part of ship's: each command has an
  `allowed-tools` rule, each rule is used, and no file adds a second WAIT. `./check.sh` passes.
- The ship cases (`evals/ship`, `evals/ship-open-finding`) still pass on a `run-cases` run of ship's
  scope.

## Affected

- **Area:** the ship skill and the tests that pin skills.
- **Files & components:** `skills/ship/SKILL.md`, new files under `skills/ship/`,
  `tests/test_skills.py` (its `SKILLS` glob reads only `SKILL.md` today, and several tests read
  ship's text directly), possibly `scripts/sdlc.py`'s `preflight` if a branch has no part to
  trigger it, `evals/ship*`, and `AGENTS.md`'s invariant on skills.
- **Downstream:** every host's ship run, and the person approving its WAIT, who must see the same
  findings and question as before. `landing_reach()` should read the new files as skills, live at
  `/reload-plugins`.
- **Contracts:** "a skill's WAIT step: what it approves, or when" (always Tier 2); the narrow
  `allowed-tools` invariant, since a side file's commands need rules in ship's frontmatter, written
  exactly as run; every script call stays `uv run --quiet --script
  "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py`.

## Constraints

- One `WAIT` heading, in `SKILL.md`, approving what it approves today.
- When a branch applies, the run behaves as it does now: the same findings, the same commit lines
  (`How to recover:`, `Closes`), the same question.
- Whether a side file is read is decided by `preflight`'s output, never by the skill's own reading
  of the diff: risk stays the script's call.
- No new command in the skill for a list ship needs: it becomes a `preflight` part.

## Open questions

- ~~Which branches move out? The seed names five; do others qualify (the fresh review, skill evals,
  nits), and is any too entangled with the four passes to move?~~ Resolved: six, agent verdicts,
  undone items, closes, how to recover, the fresh review and the skills' cases; Pre-existing bugs
  (triggered by the review, not `preflight`), nits, `fixes:` and acceptance checks stay.
- ~~How does the skill name a side file: a path through `${CLAUDE_PLUGIN_ROOT}` or one relative to
  the skill's directory, and does it work from a `--plugin-dir` session and from the cache?~~
  Resolved: `${CLAUDE_PLUGIN_ROOT}/skills/ship/<file>`, which the harness substitutes in a skill's
  text either way.
- ~~Which `preflight` part triggers each file, and does any branch (agent verdicts, `decision.md`)
  need a new part or flag?~~ Resolved: a new `branches` part lists the files that apply, from
  `SHIP_BRANCHES` in the script; agent verdicts read `decision.md`'s presence on disk.
- ~~How does `test_skills.py` find side files: every `*.md` in a skill's folder, or only those
  `SKILL.md` names, and does it fail on a side file `SKILL.md` never names?~~ Resolved: every `*.md`
  in the folder, each of which `SKILL.md` must name.
- ~~Does setup's rare branches (2026-11-04-7, also under M9) want the same mechanism, so this change
  sets the pattern for it?~~ Resolved: deferred to that seed; the tests here are generic over every
  skill folder, so it inherits them.
