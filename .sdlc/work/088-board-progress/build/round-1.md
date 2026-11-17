The step track is built: each factory card on the board now shows how far its run has got and how long the current step has been going, with an estimate where history allows. The full gate passes with 1901 tests, and nothing is committed (`HEAD` is still `e34b861`).

**Slices built**
1. **The factory writes a step record.** `factory.py verdicts --record` now writes `runs/step.md` on every reading, a stop included. The record holds `STEP`, `ROUND`, `LIMIT`, `REVIEWERS` and `SINCE`, plus `AFTER` on a `decide`. `SINCE` stays the same while the step and round don't change. `loop_state()` never reads the file (R1–R3).
2. **The card's step track.** `board.py`'s new `_progress()` maps the record onto the six steps: build, gate, reviews *n/m*, verify, rework, approve.
   - `fix` shows on the gate as `fixing`; `decide` shows `paused` at the step it stopped on; `done` or a valid `decision.md` marks every step done.
   - A stopped run has no track (`progress: null`).
   - The review count is recounted from the round's folder on every request.
   - With no record, a first build still shows as running, timed from `runs/builder.sessions`. A record that won't read is a `problems` line on the card (R4–R7).
3. **The estimate.** `typical_times()` and `step_samples()` take the median time of each step at each tier from the newest 20 closed factory changes, reading their files at `Close^`. A figure is shown only when 3 or more changes give one, and the bar stops at 95%. History is re-read only when the base branch's tip moves, and the cache is in memory (R8–R10). On this repo's real history the first read took about 0.45s and later ones about 0.24s.
4. **The plan hint.** It counts the files `plan.md`'s `## Files to change` names and how many the branch has touched, for Tier 2 changes only. I moved `_seen()`'s reading into a shared `_touched()` helper. `TEMPLATE_READS` now lists that heading, so a host's `plan.md` template that drops it is reported by `drift` (R11–R12).
5. **The page.** `progressRow()` in `board.html` draws the track, `R<n> of <limit>`, the bar and its "estimate (k runs)" label, or "so far" when there's no typical time, and the plan line. Every node goes through `h()` (R13).
6. **Docs.** `AGENTS.md` (*The board* and *The factory*), `docs/REFERENCE.md`, `board.py`'s and `factory.py`'s docstrings, and the factory's build skill (R15).

**Tests added**
- In `tests/test_factory.py`: the record matches `verdicts`' own reading, its time holds while the step does, `decide` keeps the step it paused at, and the loop never reads the record.
- In `tests/test_board.py`:
  - the track for every step;
  - a decision or stop overriding the record;
  - review counts going up as files land;
  - the first-build fallback, and no track without a record;
  - a garbled record;
  - the board's copies matching `factory.py`'s, with the factory's writer read back through the board's reader;
  - the 95% cap and the 3-change minimum;
  - the per-step split by role and order;
  - history read once per tip;
  - the plan hint;
  - the bar's width coming only from `fraction`.

  I also extended `test_the_board_writes_nothing` and the assertion that a change built by hand has no `progress`.
- In `tests/test_setup_lifecycle.py`: a `plan.md` template override without `## Files to change` is reported.

**Differences from the spec**
- I added an `AFTER:` line to the record. Without it, the step a run paused at would be lost once the record says `decide`, and R4 needs that position.
- The factory now has a named `SECONDS_RE` for the gate's `Seconds:` line, so the board's copy can be pinned to it.
- The bar's label starts with the elapsed time: `<elapsed> · ~<typical> typical · estimate (k runs)`.

**`plan.md`:** written before the code, and updated to list three tests beyond the spec's names. **`notes.md`:** nothing left undone, so none was written.

- DECISION: [default] Should the plan hint read only list-item lines of `## Files to change`? Options: every line, as the spec says; list items only. Going ahead with every line. It is loose in practice: this change's own plan counts 14 "files" because wrapped lines contribute dotted names like `progress.fraction`. I'd recommend list items only as a follow-up.

## Evidence

```
$ ./check.sh > /tmp/088-gate.log 2>&1; echo "exit: $?"; grep -E "passed|failed|would reformat|All checks|Validation" /tmp/088-gate.log | tail -6
exit: 0
All checks passed!
1901 passed in 35.24s
✔ Validation passed
✔ Validation passed
exit: 0
```

```
$ uv run --group dev pytest -q -m portable
198 passed, 1703 deselected in 42.17s
exit: 0
```

```
$ uv run --group dev pytest -q tests/test_board.py tests/test_factory.py tests/test_setup_lifecycle.py
232 passed in 37.78s
exit: 0
```

```
$ uv run --quiet --script scripts/sdlc.py drift
"breaking": [],
"refresh": [],
"report": [],
exit: 0
```

```
$ uv run --group dev pytest -q tests/test_factory.py -k "step_record or step_it_read or decide_record"   (before the factory code)
4 failed, 132 deselected in 4.78s
exit: 1
```

```
$ uv run --group dev pytest -q tests/test_board.py   (before the board code)
15 failed, 19 passed in 11.56s
exit: 1
```

```
$ uv run --group dev pytest -q tests/test_board.py tests/test_setup_lifecycle.py   (before the plan hint and TEMPLATE_READS)
2 failed, 93 passed in 13.28s
exit: 1
```

```
$ uv run --group dev pytest -q tests/test_board.py -k bar_is_drawn   (before the page code)
1 failed, 38 deselected in 0.07s
exit: 1
```
