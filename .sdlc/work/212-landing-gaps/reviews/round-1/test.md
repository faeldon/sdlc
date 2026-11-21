VERDICT: PASS

I mutated line 2110 of `landing.py` (the readiness refusal's cause, `"refusal"` → `"review"`). The new test failed, and I restored the file afterwards. The tree matches the diff stat.

## Notes

The intent is Tier 1, so it has no `R<n>` list. I mapped each Outcome bullet to a test instead.

- **Outcome 1, `--dereference-files` refused, with its prefixes.**
  - `READ_ONLY_REFUSALS` now holds `--dereference-files`, `--dereference-fil` and `--dereference-files=x`. The prefix case would pass today only because the new `GREP_FOLLOWS_LONG` entry exists. The old `--dereference-recursive` entry doesn't match it.
  - These tests can fail, and each fails if its code is removed.
  - I did not mutate the grep code. I confirmed the prefix reasoning by reading it.
- **Outcome 2, a readiness refusal ejects with `cause: refusal`.**
  - `test_a_train_names_a_readiness_refusal_as_its_cause` drives the train to the refusal and asserts `cause == "refusal"`. It also asserts that nothing was committed.
  - The mutation above made it fail, so it pins that path.
- **Decisions D1 and D2.** Both are open defaults, and the tests cover them.
  - `--filter`, `--pager`, `--view`, `--save-config`, `--config` and `---FILE` are refused.
  - `dereference-recurse` is refused in `-d dereference-recurse`, `-ddereference-recurse`, `-rd dereference-recurse` and `--directories=dereference-recurse`.
  - The pass cases `-d recurse`, `--directories=recurse`, `--no-dereference` and `--no-config` check that the list does not over-refuse.
- **Constraint "only grows stricter".** The diff only adds refusals. The existing pass cases still pass.
- **No `checks.md`.** The change has none, and none is needed.
- **Gate.** `build/round-1.gate.md` records `3744 passed, 29 skipped in 239.40s`, and plugin validation passed. I did not run the whole suite. I ran only the one named test, once with the mutation (1 failed) and once without (1 passed).

- NIT: tests/test_train.py:2340: no case checks a bare `-d dereference-recurse` word that is really a grep pattern, which D2 accepts refusing. A pin would document the trade-off. {tests S low}
