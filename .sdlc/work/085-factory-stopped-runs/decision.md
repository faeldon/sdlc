DECISION: ESCALATE

**Why:** All three round-1 reviewers passed. The builder's report and the code reviewer both trace every requirement (R1–R16) to code and a test. No `decisions.md` exists, so nothing was assumed without the person, and the two AGENTS.md rewordings are the ones the spec proposed under *Contracts touched*. One problem has to be settled before anything is committed. After the gate ran, the code reviewer's `./check.sh` came back 1865 passed and 1 failed. The failure is `test_nothing_local.py::test_nothing_in_the_repo_is_forbidden`, because `build/round-1.gate.md` contains the home-directory path from `claude plugin validate`. That file sits in the change folder, so shipping it as it stands would fail the gate on the branch and put a local path into this public repo's history. Only the person can decide whether to scrub it or how ship should handle it.

**Open items:**
- The change folder's `build/round-1.gate.md` (lines 43, 45, 61, 63) holds the home-directory path, and `./check.sh` is red because of it. It came from `factory.py gate`, not the builder. Raised by: code (marked Optional, but it breaks the intent's "`./check.sh` passes" and the "Nothing local" invariant).
- The gate recording absolute paths into a committed file looks like a factory bug present before this change. It probably affects every factory run, so file it as a `[bug]` whatever happens here. Raised by: code (implied).
- `board.py`'s `_stopped()` calls `read_text` with no `OSError` guard, while `sdlc.py`'s `factory_stop()` has one. Raised by: code (Optional).
- The stopped flag and the Needs you placement were never rendered: neither screenshot shows a stopped run, so both visual reviewers judged them from the code alone. Raised by: ui, ux.
- At 1280px the Needs you header ("a decision, a problem or a stopped run") wraps to three lines. Raised by: ui (minor).
- The ux reviewer didn't check R10's status wording, and the code reviewer only skimmed the new tests' bodies. Raised by: ux, code.
- One question in the intent is still not struck: "Does 078 need anything from this change…". The builder says 078 has since moved to `test` with an ESCALATE, so it is no longer the live case. The question needs striking or answering. Raised by: intent / builder notes.

**Decisions to confirm:** none. There is no `decisions.md`.

**For the person at ship:**
1. Decide what happens to `build/round-1.gate.md`: scrub the path, or keep it out of the commit. Then rerun `./check.sh` and confirm it is fully green.
2. Read the two reworded sentences in `AGENTS.md` (*The factory*: "`verdicts` decides from the rounds alone…" and "`sdlc` only reads the files a run leaves…"). They loosen a stated contract, from "writes nothing" to "writes only with `--record`".
3. In `factory.py`, check how `loop_state()` decides `way` and that `cmd_verdicts` writes or removes `runs/stopped.md` from the same `out` it prints.
4. In `board.py`, check the order of the checks in `next_action()` and `column()` (closed, then stopped, then pending).
5. Check the `print_status()` marker in `sdlc.py`.
6. If you can, load a scratch stopped run in `sdlc.py board` once, since no reviewer saw one rendered.

- IMPACT: minor — `factory.py verdicts` gains `--record`, and a stopped factory run now shows under Needs you on the board and as `stopped` in `/sdlc:status` with its next step: something users can newly see and act on. Running, deciding and ready runs read as before.
