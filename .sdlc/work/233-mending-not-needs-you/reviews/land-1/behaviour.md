VERDICT: PASS

The end-to-end behaviour matches the Outcome and Approach in `intent.md`. I read the diff and ran the mend-related tests (66 passed). The change has no `checks.md`.

## Notes
- **Mend under way:** `agent --task mend` writes `runs/step.md` (`STEP: mend`, `ROLE:`, `SINCE:`) before the session starts. `needs_of()` then adds nothing for a `mend` stop, via `mend_running()`.
- **Board and `status`:** the board card stays in Building with a `mending <role>` step. `status` marks the change `mending` and prints "the factory is mending the …: wait for it".
- **Mend left past its timeout:** once now is past the agent's 3-hour timeout, `needs_of()` adds "stopped: mending the <role> since HH:MM with no reply: rerun /sdlc-factory:build N if no session runs it", as the Outcome asks.
- **Mend used up, or any other stop:** the way is no longer `mend`, so the stop reaches Needs you at once, as before.
- **Failed session:** `_unrecord_mend()` puts `step.md` back as it was, so no card says `mending` with no session running.
- **Constraint:** only files and their times decide, and nothing guesses whether a session is alive. `factory_records.py`'s copies are pinned by `tests/test_modules.py` (50 passed in the landing record).
- **Landing round's conflict resolution:** the markers are gone, and the `record_closes` placement from 227 and the park comment from 229 are kept. The behaviour is unchanged by the rebase.
- **Not run:** I didn't run the whole suite. The gate record for the landing round (`land-1.gate.md`) shows `GATE: PASS`, exit 0.

## Evidence
$ cd <path-to-clone>/.claude/worktrees/233-mending-not-needs-you; D=.sdlc/work/233-mending-not-needs-you; ls $D $D/build; cat $D/intent.md | head -60; cat $D/checks.md; cat $D/build/round-*.gate.md | tail -15; git diff --stat 97cf59ddc164a284e55b37a53ff1d4303f16cb81...HEAD
(listed the change folder; `checks.md` is absent, so `cat` printed "No such file or directory"; the diffstat shows 37 files changed, 931 insertions, 25 deletions; the round-1 gate record ended "Validation passed")
exit: 0

$ sed -n 60,90p $D/intent.md; cat $D/build/land-1.md; head -12 $D/build/land-1.gate.md; tail -4 $D/build/land-1.gate.md; git diff 97cf59ddc164a284e55b37a53ff1d4303f16cb81...HEAD -- scripts/sdlc.py scripts/board.py scripts/factory_records.py
(printed `GATE: PASS`, `Verdict: PASS`, `Exit: 0` for the landing gate, then the diff of the three files)
exit: 0

$ git diff 97cf59ddc164a284e55b37a53ff1d4303f16cb81...HEAD -- plugins/factory/scripts/factory.py | head -150; uv run --quiet --group dev pytest -q tests/test_board.py tests/test_modules.py tests/test_factory_agent.py tests/test_sdlc.py -k "mend or mending or modules"
..................................................................       [100%]
66 passed, 710 deselected in 25.40s
exit: 0
