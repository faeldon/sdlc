VERDICT: PASS

I found nothing Critical or Required. I read `factory.py`'s weighing logic, `_dispose()`, the builder's landing report and the spec. I ran `tests/test_factory.py`, `tests/test_land.py` and `tests/test_skills.py` (694 passed). The builder's report shows `./check.sh` green and `sdlc.py drift` empty. I did not read the diffs for `land_parts`, `land_signals`, `land_question`, the docs, the agent prompts or the tests, and I did not run `check.sh` or `drift` myself.

## Notes
- **Landing-round fix:** the builder's conflict-resolution change is sound. `agent_findings()` weighs nits from build rounds only (`latest` and `built`), and `reworked_round()` reads build rounds only, so landing round numbers (which restart at 1) can't confuse them. A nit raised only in a landing round is `minor` with `NIT_REASON` and is never filed. That matches what `_dispose()` already filed on the yes.
- **Rerun:** `_dispose()` filters out nits `filed_nit()` finds already in the register before it asks `next-entry` for ids. It takes one `--count` for seeds and nits together, and it zips ids to nits with `strict=True`.
- **Context docs:** the README, the land skill, `skills/ship/factory.md`, the guide and `templates/inbox.md` all describe the new behaviour, so I found no stale context line.
- NIT: plugins/factory/scripts/factory.py:2140: [correctness] The landing-round rule (a nit only a landing round raised is `minor` and never filed) has no test, which the builder said in `land-1.md`. Add one test: a landing round that re-raises a handed cheap nit and adds a new one leaves the filed set unchanged.
- Unsure: I did not check whether `NIT_COSTS` and `NIT_VALUES` are pinned against `sdlc.py`'s copies. The tests pass, so a pin probably exists.
