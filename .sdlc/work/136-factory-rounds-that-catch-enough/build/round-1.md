All of R1–R10 is built, test first, and left uncommitted on the change's branch. The full gate passes: 2414 tests passed, 13 skipped, and `claude plugin validate --strict` passes. `HEAD` is still `d6a44d9`.

**What the four landed changes show (R6).** I read each change's records from history before planning:

| Change | Tier | Ran in the build rounds | What the landing kept | What would have caught it in a build round |
|---|---|---|---|---|
| 124 | 1 | code, ui, ux, all on haiku | ui: a heading bigger than the drawer's title; ux: an unlabelled checkbox | the same ui and ux reviewers on sonnet (R2) |
| 125 | 1 | code on haiku | behaviour: "no gate configured" when no base branch was read | the behaviour reviewer, which the light depth didn't run (R1) |
| 129 | 2 | code and test on sonnet | test: no test for a rule that the landing's own rebase added | nothing: no build round saw that code |
| 131 | 1 | code on haiku | nothing; the red landing gate was the machine-path problem 135 fixes | nothing: not a review miss |

So R1 and R2 each answer one real miss. Nothing in the records argues for adding `test` to a Tier 1's light rounds or for more rounds, so neither changed. The table and these reasons are now in `plugins/factory/README.md` under *Why these defaults*.

**Slices built:**
1. **R2:** every scaled reviewer runs on sonnet at either depth and tier. Haiku runs only where `[models]` asks for it. This also covers the landing rounds: 124's and 125's landing reviewers ran on haiku too.
2. **R1, R10:** unless a host sets `[light] reviewers`, the light depth adds `behaviour` at either tier, plus `test` for a Tier 2, each only when the full depth runs it. A Tier 1 light round now expects `code, behaviour`, and the build question says "code and behaviour".
3. **R9:** a host that sets `rounds`, `[light]` and `[models]` gets exactly those values back from `start`.
4. **R3:** if the verifier keeps the same change two rounds running in one run, the run goes to the approver with rounds left, and only an ESCALATE is accepted. A restart or upgrade starts the count again. This is computed from round files only, in a new `early_stop()`.
5. **R5:** a builder report line `- UNTESTABLE: R<n>: <why>` sends the run to the approver once that round is reviewed and verified. This holds even if every reviewer passed, so it always ends in an ESCALATE. `builder.md` documents the line.
6. **R7:** the approver's prompt names the repeated changes or the untestable lines. It asks for a next step under `## Reconsider the approach`: a requirement to rewrite, a model to try, or an approach to change. `approver.md` says the same.
7. **R4:** the review prompt, and the "Later rounds" paragraph of all six reviewer prompts, tell reviewers to raise an undone kept change again word for word.
8. **R8:** the retro report adds a line under its findings table: `Landing catches: k of n factory-reviewed changes`. It counts each change once, and only Important findings from a landing round that were fixed or recorded. `docs/REFERENCE.md` describes the new count.

**New tests:**
- `test_a_light_round_includes_the_behaviour_reviewer` and `test_the_behaviour_reviewer_never_deepens_a_light_run` (R1)
- `test_a_host_s_own_depth_and_models_are_kept` (R9)
- `test_a_change_kept_twice_escalates_before_the_rounds_run_out` (R3): it also checks that a different kept change still gets a rework, and that a restart starts fresh
- `test_an_untestable_requirement_escalates_after_its_round` (R5)
- `test_an_early_escalation_names_its_reason_to_the_approver` (R7)
- `test_the_review_prompt_asks_for_an_undone_kept_change_word_for_word` (R4)
- `test_readme_names_the_light_reviewers_and_models` (R6)
- `test_retro_counts_a_landing_catch_once_per_change` (R8)

I saw each one fail before the code that makes it pass. For R5, R6 and R9 I wrote the code first, so I proved those tests by breaking the code on purpose, watching them fail, and restoring it.

**Existing tests updated:** the model tests, the light-depth tests, the UI-join test, the two build-question tests, and `tests/test_bugs.py`, whose empty retro block now includes `landing_catches`.

**Changes from `plan.md`:** I also had to touch `skills/build/SKILL.md`, whose wording named haiku, and `docs/REFERENCE.md`. `read_decision()`'s refusal message now lists all three reasons a run stops instead of only "the rounds ran out". `scripts/retro.py` gained `import re`. `plan.md` now lists all of these.

**Left in `notes.md`:** one unticked line. The board and `runs/stopped.md` don't show `stuck` or `untestable`, so an early stop looks like a plain `approve` there.

No decisions raised.

## Evidence

$ ./check.sh
All checks passed!
249 files already formatted
2414 passed, 13 skipped in 119.71s (0:01:59)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_factory.py tests/test_retro.py -k "behaviour_reviewer or kept_twice or untestable_requirement or early_escalation_names or undone_kept or readme_names or host_s_own or runs_on_its_model or scale_like or light_depth or landing_catch"
22 passed, 402 deselected in 15.26s
exit: 0

$ uv run --group dev pytest -q tests/test_factory.py -k kept_twice
E       assert ('rework', 2, 3) == ('approve', 2, 3)
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k "early_escalation_names or undone_kept"
2 failed, 282 deselected in 7.22s
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py -k landing_catch
E       KeyError: 'landing_catches'
1 failed, 138 deselected in 11.09s
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py
139 passed in 93.80s (0:01:33)
exit: 0

$ uv run --quiet --script scripts/sdlc.py check
■ Problems: 0
    none ✅
exit: 0

$ git rev-parse --short HEAD
d6a44d9
