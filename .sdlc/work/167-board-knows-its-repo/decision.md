Reviews and gate record read; writing the decision now.

DECISION: READY

**Why.** All five round-1 reviewers (code, test, behaviour, ui, ux) gave `VERDICT: PASS`. The code and test reviewers each matched R1–R14 to its code and a test that fails without it, and the builder showed eight of the new tests failing before the code went in. The gate passed on `./check.sh` (3062 passed, 28 skipped, validation passed). The spec named one departure from the intent: the board takes a free lock for two syscalls. The intent's struck open question records that the person approved it with the spec, so no reviewer found it to be a mistake.

**Open items**
- Nit (code): `scripts/board.py` `train_run_held`: `msvcrt.locking` on a read-only handle is never run locally, only in CI's Windows job. It fails safe to "not held". It is findings F1, marked `minor`.
- Nit (test): `tests/test_board.py:660`: `_bare_repo` sets no git `user.name`/`user.email` and may fail on a clean CI box. It is findings F2, marked `recorded`.
- Note (ux): the "running unattended" line looks the same as the card's other meta lines. Not blocking.
- Note (ui): a very long repo name could crowd the header at phone width. This is existing header code, not this change. Not blocking.

**Decisions to confirm**
- None. The change has no `decisions.md`, no blocking line and no open default.

**For the person at ship**
- **`cmd_board()` in `scripts/board.py`:** check the order already / other repo / not a board. In particular, a board with no `repo_id` (from an older plugin copy) is now refused. Any 5170 board you started from an older copy will be refused until you restart it or pass `--port`.
- **`train_run_held()`:** it opens the lock `O_RDONLY` with no `O_CREAT`, releases a lock it got at once, and closes the descriptor in a `finally`. `_mark_unattended()` should try the lock only while a train card isn't stopped.
- **Stray board process:** the behaviour reviewer's hand run left a foreground `sdlc.py board` on some port. Its `pkill` was denied, so that board may still be running on your machine. Check `pgrep -fl "sdlc.py board"`.
- **Running boards:** `sdlc.py` is untouched, so a running board picks this up on reload with no restart.

- IMPACT: minor — a second repo's `board`/`/sdlc:dashboard` is now refused instead of silently reporting another repo's board (a fix), and the board newly shows when a `train --run` loop is taking a landing's steps, which a person can now see and couldn't before.

**Each undone item's disposition**
- None. The build put nothing in `notes.md` and the change has no `notes.md`.

**How to recover**
- The prompt names no irreversible paths. Per `plan.md`'s Rollback, `git revert` undoes it all: the board writes nothing, and the lock is only ever opened read-only, never created.
