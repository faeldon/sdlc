VERDICT: PASS

## Notes

**Trust boundaries the diff touches.** The diff opens no new entry point for untrusted data. The moved code is `loop_state()` and its helpers. It reads the same model outputs as before (reviewer verdicts, `verified.md`, `decision.md`, the builder's `## Evidence`), and the same git output through `factory._git`. It still treats them as untrusted text it parses. The new module runs no process of its own and writes nothing. It doesn't import `sdlc.py` and doesn't run `claude` or a host's command. Under STRIDE:

- **Tampering and elevation:** the factory's one entry point to `claude` (`cmd_agent`) and the gate (`_run_check`) stay in `factory.py`, unchanged.
- **Repudiation:** the run's records (`cmd_verdicts`, `stop_text`, `step_text`, `read_step`) stay in `factory.py`.
- **Spoofing, information disclosure and denial of service:** no surface for any of them is added.

**The pure move (R5), checked mechanically.** I parsed `run_state.py` and the base's `factory.py` (HEAD) with `ast`. I stripped `factory.` from each moved function's source and compared it with the base's function of the same name. All nine match exactly: `reworked`, `_untouched`, `settled`, `decision_preamble`, `loop_state`, `early_stop`, `cheap_nits`, `read_gate` and `_gate_state`. The only top-level assignment is `factory = None`. In `factory.py` the diff adds only the three re-pointed call sites, the loader and a `_Names` docstring. The loader is a copy of `_load_landing()` with a fixed sibling path, so nothing it loads comes from config or input. No decision a model's output feeds changes, so no verdict, gate or risk check is weakened.

**`landing.py` is on `[review] sensitive`, so I read it closely.**

- **The nit -80 guard:** `answered` is now false when `reviews/land-<n>/` is missing. Before, an empty folder already gave `any(...) == False`, so a missing folder now behaves like an empty one rather than raising. The fix is still checked by `land_ask`/`land_verdict` before anything is taken into an answered round, so the guard doesn't let an unreviewed fix skip review.
- **The nit -69 comment:** it is accurate and changes no code. It also states the residual risk honestly: an orphaned agent after a SIGKILL of the loop alone, which the person avoids by killing the process group.

**Tests.** The new Windows test calls `taskkill` with an argument list (`["taskkill", "/T", "/F", "/PID", str(pid)]`): no `shell=True`, and only a process id is interpolated. `CREATE_NEW_PROCESS_GROUP` is read only inside the test body, after the skip check.

**Decision D1** (`decision_preamble` moved as well) is a judgment about where the line falls and has no effect on security.

**What I checked and ran:**
- Read `intent.md`, `spec.md`, `decisions.md` and `build/round-1.gate.md`. The gate is green: `./check.sh` exited 0.
- Read the diffs of `landing.py` and `test_skills.py`, the new parts of `test_land.py` and `test_train.py`, and the loader in `factory.py`.
- Ran the `ast` comparison above, reading only.

I didn't run the gate myself.

**Done well:** the move is exact. Constants stay in `factory.py`, so `factory_records.py`'s copies are still checked against the same names. The new module's docstring states its contract, including that it writes nothing and runs no process.
