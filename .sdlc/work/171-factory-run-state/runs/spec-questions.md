
I wrote no files. The draft is above, in full; the summary below is the question list.

**Settled from the code:**
- **Where the boundary falls** (the intent's open question): the new module gets `loop_state()` and the seven helpers only it calls. `cmd_agent`'s prompt building stays in `factory.py`, because it's a separate reason to change and the one place `claude` runs. If you'd rather move it too, the move roughly doubles in size, and a second module like `prompts.py` gets the same loading and test rules.
- **Whether `verdicts` moves:** it stays. It's a thin wrapper around `loop_state()` plus the two record writers the board's tests pin, so moving it would also change `tests/test_board.py`.
- **Nit -68:** both halves are out of date. The lookup it names is gone, and two tests use `RUN_STOPS`. It gets answered, not changed.
- **Nit -84:** `_settle_counter()` stages `.sdlc/last-id` before `_stray()` reads git status, so it already passes. A test makes that explicit.
- **Nit -69:** answered with a comment. Making the lock inheritable would change behaviour mid-move and wouldn't work on Windows.
- **Idea -67:** the Windows kill test can't use the fake `claude`, because Windows can't start a shebang file. It blocks in the gate's check instead.

**Left for you:**
1. **Touch `landing.py` or not.** Fixing -80 (a one-line guard) and commenting -69 both edit `landing.py`. That file is in `[review] sensitive`, so the whole change gets a full-depth review with the security reviewer and can't land as `by=auto`.
   - Default: edit it. The intent asks for the nits fixed, and a deep review suits a change to the loop.
   - Other choice: answer both in `notes.md` only. The review stays light, and -80's guard waits for a change to `landing.py`.
2. **If the Windows test finds a real Windows bug in the train.** No train has run end to end on Windows yet, so the new test may turn up a real failure.
   - Fix it here: the change grows beyond a pure move, in sensitive code.
   - File it as a `[bug]` and mark the test `xfail` on Windows, naming the bug: the move stays pure.

   Either is reasonable. The plan should name which before the build.
3. **`AGENTS.md`.** Its *Modules loaded by path* paragraph doesn't name the new module. That's left to ship's context check, as a one-clause edit if it proposes one, which would be the only change outside the factory.
