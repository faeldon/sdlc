DECISION: READY

**Why.** Both round-1 reviewers returned `VERDICT: PASS`, and the gate record is green: `./check.sh` exited 0, with 3450 passed and 29 skipped. Every outcome in the intent is met. `by()` now goes through `uv_script()` and its offline fallback. The kill tests share one named bound. Each of the 26 nits has either a test (most checked against deliberately broken code) or a written reason in `notes.md`. The change touches only `tests/` and the change folder, as the plan says, and nothing in the reviews suggests the intent was wrong.

**Open items**
- None unresolved. The code reviewer's NIT on `tests/uv_run.py:17` (`UNCACHED` matches broadly) is recorded as F1 in `findings.md` and is low value.

**Decisions to confirm**
- None. There is no `decisions.md`, the builder raised no decisions, and the prompt names no open defaults.

**For the person at ship**
- **`tests/uv_run.py`:** look here first. It is the new shared helper, and both `test_adoption.py` and `test_train.py`'s `by()` now depend on it. Check whether `UNCACHED` is too broad: if a script fails and its output happens to say "offline", the test would be skipped instead of failing (F1).
- **The kill tests:** the intent asked for "drops its long polls", and the builder says there were none to drop. Each poll waits 0.05 s and stops as soon as its marker file appears, so the 20–27 s each test takes is the train's own landing. Both waits already used 120 s; they now share one named bound, `STARTED_WITHIN`, with its reason beside it. `notes.md` explains this, and the behaviour reviewer saw the train tests finish in 25 s.
- **Two `test_retro.py` assertions may have missed the gate:** the ones for -56 and -67 were added while the gate was running. The builder reran them by name and they pass, and the landing gate will run them again.
- **The intent's open question** (land after R5's split of `test_factory.py`?) can be struck. This change doesn't touch that file.
- **No published interfaces are touched.**

- IMPACT: none — only tests and the change folder changed; nothing a host or a user receives is different.

**Each undone item's disposition**
- UNDONE: `retro.py`'s workarounds block gives `unknown` a `count` and `rows` but no `n`, though `_workarounds()`'s docstring says "each count carries its `n`" (nit 2026-11-19-56). That is a code change, and this change is tests-only, so its test pins the row's `change` key and leaves `n` alone. → seed: Give the workarounds' `unknown` block its `n`, as `_workarounds()`'s docstring says
- UNDONE: The intent's open question, whether this change should land after R5's split of `test_factory.py`: this change doesn't touch `test_factory.py`, so the two can't conflict on it. The person can strike the question. → dropped: answered; the change doesn't touch `test_factory.py`, so it can't conflict with R5's split
