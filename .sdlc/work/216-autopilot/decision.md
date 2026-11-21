DECISION: READY

**Why:** Round 4 is all `VERDICT: PASS` from code, test, security and behaviour. The full gate is green (3947 passed, 29 skipped). The three defaults the reviewers raised as unbuilt (D8, D9, D10) are now built and tested. Every ledger line D1–D11 is ticked. The person confirmed D1–D5 and D7–D10, D6 was settled by an earlier approver, and D11 is `→ decided: seen`. The departures from the spec in `notes.md` are each explained there and were confirmed as defaults.

**Open items:**
- None. No CHANGE remains in round 4.

**Decisions to confirm:**
- No blocking decision is unticked.
- No default is open. All of D1–D11 are ticked.

**For the person at ship:**
- Look first at `plugins/factory/scripts/autopilot.py` and the factory's `autopilot_running()` and `take_markers()`, which decide who may pass `--by autopilot`.
- Then check `_default_guards()` (D8, sensitive paths held by default) and the `candidates()`/`open_wave()` handling of seeds that carry an `Issue:` line (D9, named in `--seeds` only, opened with `closes:`).
- Approved by the person: D11, in `decisions.md`. Under autopilot a spec and an intent are built on with only the run's yes, which changes the promise in `plugins/factory/README.md` (*The approvals*) and `spec.md` *Contracts touched*.
- Approved by the person: D10, in `decisions.md`. `--by autopilot` stops accidental inheritance of the marker, not a same-user process that sets it on purpose, and the docs now say so.
- `spec.md` R19 still gives the default guards as the docs plus `irreversible`. D8 adds `[review] sensitive`, so the spec text is out of date.

- IMPACT: minor — a host can newly run `/sdlc-factory:autopilot` and set `[autopilot]` limits, guards and the `*_weights` tables, and `sdlc.py status --json` is new.

**Undone items:**
- UNDONE: The board shows nothing of `opened_by: autopilot` or a run under way: `status` does; the board's is seed 2026-11-21-34, which waits on this change. → dropped: already carried by seed 2026-11-21-34, so a second seed would duplicate it.
- UNDONE: `next_up`'s cheap-nits lines (`rule: nits`) carry no seed id, so autopilot never takes them, though `READY_RULES` lists them. → seed: Let autopilot take `next_up`'s cheap-nits lines
- UNDONE: `test_autopilot_end_to_end` drives the loop in process with `run_step` stood in for, as the train's tests do. Since round 1, `test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does` runs a real `run_step` child under the lock, but no test runs the whole loop's subprocesses with a stand-in `claude`. → seed: Test the whole autopilot loop's subprocesses with a stand-in `claude`
- UNDONE: The retrospective's overturn rate for autopilot's calls (the spec's question 6) is left for a later seed, as the intent's resolution says. → seed: Retro overturn rate for autopilot's calls
- UNDONE: pre-existing: plugins/factory/scripts/factory.py:4292: `_claude()` passes `TRAIN_RUN_ENV` on to the agent sessions a `train --run` starts (`train-resolve`, `land-fix`, which edit). So an agent's own `factory.py train …` passes the `train_running()` check at landing.py:1978, which is meant for the loop's own children. → seed: Stop `_claude()` passing `TRAIN_RUN_ENV` to editing agent sessions. I did not file it as a bug: the Bugs severity words (`high`, `med`, `low`) describe wrong output or lost work, and none fits a guard weakness, so I carry it as a seed.
