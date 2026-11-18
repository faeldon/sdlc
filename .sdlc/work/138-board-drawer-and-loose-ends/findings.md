# Findings

> What a change's review found, one `## ` section a finding, committed with the change.
> `/sdlc:ship` writes it after every review, and the factory's `carry` writes its agents' findings
> into it; `By:` names who raised one: `fresh` for ship's fresh-context reviewer, a factory role
> (`code`, `test`, …) for an agent, and no line on ship's own. A rerun keeps each id, marks one the
> diff no longer shows `fixed`, and never raises again one the person answered `wrong`,
> `intentional` or `minor`; an agent's `wrong` is its verifier's, never the person's, and the same
> fault worded differently is one more. `sdlc.py` reads each heading and its `Evidence:`, `Class:`,
> `Disposition:`, `Reason:`, `By:` and `Fix:` lines, counts ship's own alone into the
> `Sdlc-Findings` trailer (its `agents=` says how many it left out), words ship's question from
> the ones proposed `fix`, and `ship` refuses while one is still `open` or `fix`. On a diff that
> touches a sensitive path, this note also says `Fresh review: ran`, or `Fresh review: skipped,
> <why>`.

Skill evals: ran, 1 of 1

## F1. [important] [correctness] scripts/sdlc.py:7613-7618 (`cmd_intake`): the `try/except Exception` swallows the error, and `unpushed_closes()` returns None when git can't say.

scripts/sdlc.py:7613-7618 (`cmd_intake`): the `try/except Exception` swallows the error, and `unpushed_closes()` returns None when git can't say. Both paths then set `waits_on_push` to False for every dangling issue, so a dangling issue that an unpushed commit closes is offered to triage again, which is the bug this change fixes. Triage can't tell "read failed" from "nothing waits". Fix: when `closing is None` and any dangling entry has a `closed_by` match to check, say so in a field such as `dangling_error` (or a per-entry `waits_on_push: null`). Then have triage's `dangling` bullet not offer any dangling issue while that is set. Narrow the `except` to the errors `closed_by()` can actually raise, or drop it. Add a test for the None path, since no test covers it.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: fixed
By: code

## F2. [nit] [correctness] the skill now has the script's question twice, once as "Ask `start`'s `question`" and again as a literal blockquote.

plugins/factory/skills/spec/SKILL.md:88-91: the skill now has the script's question twice, once as "Ask `start`'s `question`" and again as a literal blockquote. The two can drift, which is what the change was meant to stop. Keep only the instruction to ask `start`'s `question` as printed, or leave the blockquote as a note that it's an example.

Evidence: plugins/factory/skills/spec/SKILL.md:88-91
Class: code review, round 1
Disposition: fixed
Reason: weighed S med: handed to the builder's rework, and not raised again
By: code

## F3. [nit] [correctness] the `# fmt: skip` on the `out["dangling"]` comprehension looks unneeded, since `ruff format --check` passes without it.

scripts/sdlc.py:7620: the `# fmt: skip` on the `out["dangling"]` comprehension looks unneeded, since `ruff format --check` passes without it. Remove it if the formatter agrees.

Evidence: scripts/sdlc.py:7620
Class: code review, round 1
Disposition: recorded
Theme: style
Cost: S
Value: low
By: code

## F4. [important] [correctness] a `.md` file holding only whitespace, such as a single newline, is not `""`, so `md` is true and `paint()` draws an empty `div`.

scripts/board.html:572: a `.md` file holding only whitespace, such as a single newline, is not `""`, so `md` is true and `paint()` draws an empty `div`. That is the blank pane this change exists to remove, and the "This file is empty." note never appears for it. Test the trimmed text in both the `md` check and the empty check, so a whitespace-only file gets the note.

Evidence: scripts/board.html:572
Class: ux review, round 1
Disposition: fixed
By: ux

## F5. [important] [correctness] the bullet tells the person to "say it is flagged `waits_on_push`".

skills/triage/SKILL.md:57: the bullet tells the person to "say it is flagged `waits_on_push`". That is a field name, not a description of what is happening. Say it in their terms, for example "it's waiting on the push, which /sdlc:publish or close will do". The sentence "One an unpushed commit closes waits only on the push" also reads wrongly; rewrite it, for example "An issue an unpushed commit closes is waiting on the push: never offer it again". Step 6's report should carry that same line, since nothing else tells the person about it.

Evidence: skills/triage/SKILL.md:57
Class: ux review, round 1
Disposition: fixed
By: ux

## F6. [pre-existing] [correctness] a card reads "decide D1 in the factory's supervisor".

scripts/board.py:626: a card reads "decide D1 in the factory's supervisor". A person doesn't know what the supervisor is or where to go. This change doesn't touch that text.

Evidence: scripts/board.py:626
Class: ux review, round 1
Disposition: recorded
By: ux

## F7. [nit] [correctness] the Step 6 paragraph is now one 168-character line, where the rest of the file wraps near 100.

skills/triage/SKILL.md:58: the Step 6 paragraph is now one 168-character line, where the rest of the file wraps near 100. Rewrap it at the same point as its neighbours.

Evidence: skills/triage/SKILL.md:58
Class: code review, round 2
Disposition: recorded
Theme: style
Cost: S
Value: low
By: code

## F8. [nit] [correctness] the docstrings cite "138 C1" and "138 C2", which a reader can't resolve, since those labels exist only in this round's review.

tests/test_board.py:1886-1915: the docstrings cite "138 C1" and "138 C2", which a reader can't resolve, since those labels exist only in this round's review. Say what they refer to, or cite the change's own rule.

Evidence: tests/test_board.py:1886-1915
Class: code review, round 2
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F9. [nit] [correctness] `test_no_build_question_for_a_refusal_or_a_spec` now checks only a Tier 1 spec refusal, since the Tier 2 spec does get a question.

tests/test_factory.py:4437: `test_no_build_question_for_a_refusal_or_a_spec` now checks only a Tier 1 spec refusal, since the Tier 2 spec does get a question. The name still promises "a spec" with no question. Rename it to say a Tier 1 spec, or drop "spec" from the name.

Evidence: tests/test_factory.py:4437
Class: code review, round 3
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: code
