- KEPT: ux: C1: tests/fixtures/board/changes/006-draft-purge/runs/stopped.md:2: the stop record the shot is built from still has the old run-on `NEXT:` line with "mend", so the 390px shot doesn't show the shortened text.

## Notes
- The shot's fixture copy, `.sdlc/reports/shots/120-board-nits/round-2/fixture/006-draft-purge/runs/stopped.md`, holds that old line. It comes from `tests/fixtures/board/changes/006-draft-purge/runs/stopped.md`, which isn't in `git status`, so the change never touched it.
- `WAYS["mend"]` in `plugins/factory/scripts/factory.py` already reads "rerun /sdlc-factory:build {id}, or /sdlc:ship {id}". The code is right, but the fixture was never regenerated to match it, so the reshoot should use a fixture with the current `NEXT:` text.
- Decision D4 says a stop recorded before this change may keep its old line until the next `verdicts --record`. That applies to real hosts. It doesn't excuse the fixture, which should show the intended outcome.
- The "Settled" item was not one of the numbered changes, so I gave it no line. The current `WAYS_WHY["mend"]` already says "Rerunning /sdlc-factory:build {id} asks an agent again, once…", so "mends it once" is gone.
- I only read files and ran grep. I ran no tests and no `checks.md` commands.
