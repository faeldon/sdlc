---
id: 090
slug: agents-rules-once
tier: 1
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: 2026-11-17-3
depends_on:
serves: none
---

# 090 — Each rule is said once in AGENTS.md

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`AGENTS.md` is this repo's policy doc and every session's context: `.claude/CLAUDE.md` imports it,
so each session here loads it whole. 23 of the 27 changes in the last retrospective's window edited
it. It was 447 lines then and is 513 now. Its Architecture section has grown into a
feature-by-feature account: about 25 bold-led paragraphs, from *Closing* to *The factory*, that
repeat what `docs/REFERENCE.md` and the docstrings in `scripts/` already say. It changed alongside
`docs/REFERENCE.md` 17 times and alongside `scripts/sdlc.py` 17 times.

Saying a rule in several places has already caused misses. In two Important findings, a rule was
restated in several places and only one of them got edited:
- 046: "six lines still said only publish pushes";
- 049: "the docs that list the extra-stop kinds leave out the new `fix` kind".

Each new feature adds another paragraph. Ship's context pass (`skills/ship/SKILL.md`, step 4) asks
whether a doc now says something false, or whether the diff adds something a future session needs.
It never asks whether that thing is already said somewhere else, so it proposes the next
restatement too.

## Outcome

- AGENTS.md's Architecture section keeps the boundaries (mechanism vs. judgment, mechanism vs.
  policy, what the core never imports or runs) and the rules that aren't obvious from any one
  function. For each feature's detail it points at the one place that holds it: a section of
  `docs/REFERENCE.md`, or a named function's docstring.
- No rule that is cut from AGENTS.md is lost: before the cut, each one is found said elsewhere, or
  moved there.
- *Invariants the tests enforce* stays, since that's what a session must know before editing.
- AGENTS.md is markedly shorter than its 513 lines. The spec-free target: the Architecture section
  is a map, not a manual.
- Ship's context pass also asks whether a proposed line is already said in another context doc or a
  docstring, and points at it rather than restating it. The skill's wording is the only change
  there.
- `./check.sh` passes.

## Affected

- **Area:** this repo's context docs, and ship's context pass.
- **Files & components:** `AGENTS.md`, `docs/REFERENCE.md` (where detail moves to, if it isn't
  already there), docstrings in `scripts/sdlc.py`, `scripts/retro.py`, `scripts/board.py` and
  `plugins/factory/scripts/factory.py` that receive a moved rule, and `skills/ship/SKILL.md`
  (step 4).
- **Downstream:** every session in this repo, which loads AGENTS.md through `.claude/CLAUDE.md`,
  and `docs/CONTRIBUTING.md`'s reader. Ship's context pass runs in every host, where the new
  question makes it propose fewer restatements in their context docs.
- **Contracts:** "Nothing public names the agent" and "Nothing about a project or a workspace"
  (`tests/test_nothing_local.py`) bind the rewritten text. `tests/test_skills.py` binds ship's
  `SKILL.md` (one WAIT, its rules, its side files).

## Constraints

- No rule disappears: a rule cut here must be said where the pointer leads.
- The boundaries and every rule a test enforces stay in AGENTS.md, where a session meets them
  before editing.
- AGENTS.md stays the file to edit. `.claude/CLAUDE.md` only imports it, since
  `claude plugin validate --strict` refuses a `CLAUDE.md` at the plugin's root.
- Ship's WAIT and what it approves are unchanged. The context pass's bar stays high: this adds a
  question, it doesn't lower the bar.

## Open questions

- Where does each paragraph's detail go when REFERENCE.md doesn't hold it? REFERENCE.md is
  host-facing, so internals (`_handoff()`, the board's pinned copies, `_own_script()`) may belong in
  docstrings or `docs/CONTRIBUTING.md` instead.
- Should a test hold the line, such as a cap on AGENTS.md's length or a check that each pointer
  names an existing heading or function, or is the context pass's new question enough?
- Is this one change, or one per area of the Architecture section, so each cut is reviewable?

## Approach

Go through the Architecture section paragraph by paragraph. For each sentence, find where else it's
said (REFERENCE.md, CONTRIBUTING.md, a docstring). Keep it in AGENTS.md only if it is a boundary or
a non-obvious rule. Otherwise make sure the other place says it, then replace the sentence with a
pointer. Then add a third question to `skills/ship/SKILL.md`'s context pass: is it already said in
another context doc or a docstring? If so, propose a pointer, not the line.
