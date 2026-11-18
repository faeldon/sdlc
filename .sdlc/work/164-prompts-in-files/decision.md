DECISION: READY

**Why.** All three round-1 reviewers (code, test, behaviour) returned `VERDICT: PASS`, and the gate is green (`./check.sh`, 3019 passed, 28 skipped). Each of R1–R11 has a named test. The test reviewer reran the R3 cross-check against the merge-base's `plugins/factory/scripts/` and got 45 passed, and the behaviour reviewer got the same result its own way. That shows the 45 recorded copies come from the old script, so the prompts agents receive are byte-identical. `landing.py` is untouched, no agent's tools changed, no dependency was added, and nothing in the rounds suggests the spec was wrong.

**Open items**
- No unresolved CHANGE. One NIT from the `test` reviewer is already recorded as F1 in `findings.md`. It says the R5 refusal test only builds the `build` task, so a broken `mend.md` or `land-review.md` under `land-mend` has no test of its own. The same validation path covers it, so the risk is low.

**Decisions to confirm**
- None. There is no `decisions.md`, the builder raised no decisions, and the prompt names no open defaults.

**For the person at ship**
- Look first at `plugins/factory/scripts/factory.py`, at `PROMPT_PARTS`, `_prompt_file()`, `prompt_refusal()` and `prompt_part()`. Check that `_task()` refuses before any session starts and that `prompt_part` uses `substitute()`, never `safe_substitute()`. Two things there are not ordinary code-diff mistakes: a filled value being read as a template, and a half-filled prompt.
- Then skim a few `plugins/factory/prompts/*.md` files against their recorded `tests/prompts/*.txt` copies, for example `approve.md` and `land-review.md`. The golden test and the cross-check already prove they match byte for byte, so this is only for readability.
- Small inconsistency: the behaviour reviewer counted "46 recorded copies", but `tests/prompts/` holds 45 files. Its "46 passed" is probably the 45 cases plus `test_every_recorded_copy_is_a_case`. It's harmless.

- IMPACT: patch — the factory sends agents exactly the same prompts. The plugin now ships its prompt text as files under `plugins/factory/prompts/` and refuses a broken one before any session starts. Nothing a host does or can do changes.

**Each undone item's disposition**
- None. There is no `notes.md`, and the builder reports nothing was carried there.

**How to recover**
- The prompt names no irreversible paths. Per `plan.md`, `git revert` undoes the whole change: the script reads the files at run time and writes nothing outside the repo.
