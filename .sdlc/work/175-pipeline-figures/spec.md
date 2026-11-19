---
id: 175
slug: pipeline-figures
kind: spec
created: 2026-11-19
updated: 2026-11-19
---

# 175 — The retrospective reports the pipeline's gates, trains and reviews · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Nits taken in: 2026-11-19-19, 2026-11-19-21

Assumptions checked in the code. A closed change's run records are read at its own commit, the
`Close` commit's parent (`retro._records_at()`, `closed_changes()`'s `sha`), as `_autonomy()` and
`_cost()` already read them. Gate records carry `Seconds:` but no slot wait: `gate_slot()` yields
`waited` and `cmd_gate()` prints it, but neither `factory.py gate` nor `sdlc.py gate` writes it to
the file. No committed record holds the review depth: `depth()` computes it on each reading and
`step_text()` leaves it out. Mends are already counted in `autonomy.spurious_stops`.

Assumptions the plan must confirm from history before building on them: `runs/step.md`,
`runs/land-step.md`, `runs/land-train.md`, `build/land-*.gate.md` and `build/land-accept.md` are
present at a factory change's own commit (each is amended in with the landing's records). If one
isn't, the figure that reads it is reported missing for every change, and the plan says so. It
doesn't become a zero.

1. R1. `retro()`'s JSON gains a `pipeline` key holding every figure below. Each figure carries
   its `n`, and a rate, share, median or percentile is `null` when `n` is 0, never 0. A test
   on a window with no factory change asserts every such figure is `null` and every `n` is 0.
2. R2. `pipeline.gates.window` and `pipeline.gates.previous` give, separately for the round gate
   (`build/round-<N>.gate.md`) and the landing gate (`build/land-<n>.gate.md`), the attempts'
   `seconds` and `wait` as `{n, median, p85}`. The window is this retrospective's changes and
   `previous` is the window before it (`_previous_window()`; `null` when there is none). The
   hand gate's `build/gate.md` is in neither. A fixture test asserts the medians and 85th
   percentiles over known `Seconds:` values. It also asserts that an attempt without a
   `Waited:` line counts in `seconds.n` but not in `wait.n`.
3. R3. `factory.py gate` and `sdlc.py gate` write a `Waited: <seconds>` line after `Seconds:` in
   every attempt. Its value is the slot wait `gate_slot()` / `_hand_slot()` yielded, 0.0 for
   none. `test_the_record_is_the_factorys_shape_line_for_line` still passes with `Waited:`
   masked as `Seconds:` is. A factory test fails if an attempt is written without the line.
4. R4. `pipeline.red_gate` gives `builds` (round gate files in factory changes), `red` (those
   with any `FAIL` attempt), `rate` (red over builds) and `n`. A fixture with one red-then-green
   build and one green build reports `rate: 0.5`.
5. R5. `pipeline.landing` is over the factory changes whose commit holds `runs/land-step.md` (a
   factory landing). Its `coverage` and `missing_because` come from `_coverage()`, under
   `built by hand` or `no landing record`. It gives:
   - `gates`: attempts in `build/land-*.gate.md`, total and `per_change`.
   - `ejections`: rows of `runs/ejections.jsonl` by `cause` (`gate`, `review`, `refusal`,
     `stop`), with a total and the changes with any.
   - `bisections`: distinct `FAIL` gates (by commit and file) at a prefix above 1 in the
     window's `runs/land-train.md` records, since a red gate over more than one change is one
     the train must bisect.
   - `base_moves`: each change's last `MOVES:` in `runs/land-step.md`, total, `per_change` and
     the changes with any.
   - `accept_stops`: attempts in `build/land-accept.md`, each a stop for the person.
   - `conflicts`: `landing` counts the `resolve` rows in `runs/land-times.jsonl`, and `ship`
     counts the files `conflicts.md` names.

   A fixture of two trained changes sharing one red tip gate asserts that `bisections` counts
   it once, and a fixture with one ejection by `gate` asserts `ejections.gate == 1`.
6. R6. `factory.py`'s `step_text()` writes `DEPTH: full` or `DEPTH: light` (the reading's
   `depth`), and `read_step()` and `factory_records.read_step()` return it as `depth`. The
   existing pin of the two `read_step()`s fails if either side drops it.
7. R7. `pipeline.depth` gives `full`, `light`, `share` (full over both) and `n`, over the factory
   changes whose committed `runs/step.md` names a depth. A run never lightens (`depth()`), so
   its last reading is its deepest. An older run with no `DEPTH:` line is in `missing_because`
   (`depth not recorded`), never `light`. A fixture with one full run, one light run and one
   older run reports `share: 0.5, n: 2`, with the older run missing.
8. R8. `pipeline.unreviewed` gives, over the changes whose own commit carries `Sdlc-Landed` by
   `auto` or `person` (`rec["landed"]`), `with_paths` (`unreviewed=` a count above 0), `paths`
   (their sum), `unknown` (`unreviewed=unknown`), `none` and `n`. A fixture with one landing of
   each kind asserts each count.
9. R9. Every figure in R2–R8 is read through `scripts/factory_records.py`. A new pure
   `pipeline_counts(show, listing)` returns one change's raw figures, or None for a change built
   by hand (no `decision.md`). `retro.py` opens no record file and spells no record's name, so
   `tests/test_modules.py`'s scan still passes once the new names (`land-train.md`,
   `land-accept.md`) are added to its `RECORD_FILES`.
10. R10. Each constant or regex the copy shares with the factory sits in `factory.py` under that
    name (`WAITED_RE`, `DEPTH_RE`, `LAND_TRAIN`, `TRAIN_GATE_RE`, `LAND_ACCEPT`), so
    `test_every_shared_name_is_the_factorys` pins it. `landing.py` reads `LAND_TRAIN` as
    `factory.LAND_TRAIN`, as it reads `factory.EJECTIONS`, and `accept_path()` builds from
    `LAND_ACCEPT`. A test fails if `factory_records.TRAIN_GATE_RE` stops matching a line
    `landing.train_record()` writes.
11. R11. `pipeline.changes`, each change's own figures, is printed only with `--metrics`, as
    `cost.changes` is. A test of `cmd_retro()` without `--metrics` asserts it is absent.
12. R12. Mends are not counted a second time. `pipeline` has no `mends`, and REFERENCE.md points
    to `autonomy.spurious_stops`, which already gives build and landing mends per change.
13. R13. Nit 2026-11-19-21: `_none_reason()` uses `(\s+[^\s=]+=\S*)+$`. One test asserts it
    still strips ` lead=failed runtime=failed` as before. Another asserts that 40 `a=b=c=d`
    tokens followed by a token with no `=` return within one second, run in a thread joined
    with a timeout so a regression fails rather than hangs.
14. R14. Nit 2026-11-19-19: `autonomy_counts()` gains a comment saying why only `default` lines
    are checked for `SUPERSEDED` and `SETTLED`: `factory.py decisions` writes those marks on
    defaults alone, so a blocking or look line never carries one. This is a comment only, with
    no change in behaviour, so no test is added.
15. R15. `docs/REFERENCE.md` *Retrospectives* describes `pipeline` the way it describes
    `autonomy` and `cost`. `docs/RETRO-SCORECARD.md` marks the Speed diagnostics (feedback-loop
    and landing time) and Quality's *risk exposure* as captured by S10, naming the keys. If
    `tests/test_feature_map.py` requires it, `docs/FEATURES.md` / `docs/PROCESS.md` list the
    new key. The plugin's factory README and `factory.py`'s docstring name the `Waited:` and
    `DEPTH:` lines.

## Design

**Records first (the factory).** Two lines are added to records the factory already writes,
since no figure exists without them:
- In `cmd_gate()`, `Waited: {waited}` follows `Seconds:` in the attempt section. `sdlc.py`'s
  `cmd_gate()` writes the same line from `_hand_slot()`'s `waited`, because the hand gate is
  pinned to the factory's shape line for line.
- `step_text()` appends `DEPTH: {out["depth"]}` when the reading has one. `loop_state()` already
  puts `depth` in `out`.

Readers that ignore unknown lines are unaffected: `read_gate_file()`, `gate_attempts()`, the
board's `gate_seconds()` and `read_step()` all match by line.

Neither line is a trailer. Both are record lines committed with the change, so the constraint
"no new trailer" holds. Records from before this change have neither line, so their figures go
in `missing_because`.

**The copies (`factory_records.py`).** Added beside the existing copies:
- `WAITED_RE` (`^Waited: (\d+(?:\.\d+)?)\s*$`) and `DEPTH_RE` (`^DEPTH: (full|light)\s*$`).
- `TRAIN_GATE_RE` (`^GATE: (\d+) (PASS|FAIL) ([0-9a-f]+) (\S+)\s*$`, the shape
  `train_record()` writes).
- `LAND_TRAIN` and `LAND_ACCEPT`.

`gate_attempts(path)` is split so its line reading is `read_gate_attempts(text)`, which also
returns `waited`. `gate_attempts()` keeps its signature for the hand gate. `read_step()` gains
`depth`.

The new `pipeline_counts(show, listing)` is pure, like `run_counts()` and `autonomy_counts()`,
and returns None without `decision.md`. Otherwise it returns:
- `gates`: each attempt as `{kind, seconds, waited, verdict}`, from `gate_kind()` over
  `listing("build")`.
- `builds`: per round gate file, whether any attempt failed.
- `landed`: whether `runs/land-step.md` exists, and its `MOVES:`.
- `ejections`: a Counter of causes.
- `train_gates`: `(prefix, verdict, commit, file)` tuples.
- `accepts`: the attempts in `land-accept.md`, read by `read_gate_attempts()`.
- `resolves`: the `resolve` rows of `read_land_times()`.
- `conflict_files`: from `conflicts.md`, parsed as `sdlc.conflicts_resolved()` parses it, over
  text. It is moved into the module or shared by a text form, the plan's call. Either way it
  stays one rule.
- `depth`: from `runs/step.md`, or None.

**The figures (`retro.py`).** `_pipeline(home, changes, previous)` runs
`sdlc.factory_records.pipeline_counts(*_records_at(home, rec))` over each window's changes and
builds the JSON:
- `gates` for `window` and `previous`.
- `red_gate`, `landing`, `depth` and `unreviewed` for this window.
- `factory` and `by_hand`, as `_autonomy()` gives them.
- `changes`.

Percentiles use the rule `lead_view()` already uses (`sorted[ceil(0.85·n) − 1]`), factored into
one helper both call, so the two can't drift. Coverage uses `_coverage()`, and shares use
`_share()`.

`retro()` calls `_previous_window()` once and passes the result to `process_views()` and
`_pipeline()`. `cmd_retro()` strips `pipeline.changes` without `--metrics`.

`unreviewed` reads `rec["landed"]`, which `closed_changes()` already parses from the change's
own commit, so it needs no record and no new trailer.

**Edge cases.**
- A change built by hand is only in `by_hand`.
- A factory change with no landing record (shipped by hand after a build) is outside
  `landing.n`, under `no landing record`.
- A gate file that won't parse gives no attempts, and is never a zero-second one.
- A train's shared red tip is counted once by `(commit, file)`.
- Base moves are per change. A train change's `MOVES:` is the train's count, so the total is
  reported as "moves seen while landing", not summed into a train total.

**The nits.** The `_none_reason()` regex is replaced, and `autonomy_counts()` gets its comment
(R13, R14). The new regex differs from the old only on a token that begins with `=`, which close
never writes.

## Contracts touched

- **Core reads a run's records only through `factory_records.py`, its copies pinned.** Every new
  read goes through `pipeline_counts()`, and every new name is `factory.py`'s, pinned by
  `test_every_shared_name_is_the_factorys`. `LAND_TRAIN` and `TRAIN_GATE_RE` move into
  `factory.py` so the pin reaches them (the `EJECTIONS` precedent). `RECORD_FILES` gains the two
  file names, so no other core file names them.
- **`factory_records.py` is pure.** `pipeline_counts()` takes `show` and `listing` and runs
  nothing.
- **`factory.py` never imports `sdlc.py`.** The `conflicts.md` parse is core's own record. It
  moves into or is shared within core, never into the factory.
- **`retro` is read-only but for its report.** `_pipeline()` only reads git objects.
- **The hand gate's record is the factory's shape** (`tests/test_hand_gate.py`). Both writers
  gain `Waited:` in the same change.
- **Metrics' trailer contract.** No trailer is added or redefined. `unreviewed=` is read as
  `metrics.py` defines it.
- **A figure no record holds is missing, never zero** (intent constraint, and retro's `surface`
  rule). Older runs without `Waited:` or `DEPTH:` and changes without landing records go into
  `missing_because`.
- **Windows** (`tests/test_windows.py`). There are no new writes except the two record lines,
  which go through the existing `write_text(..., newline="\n")`.
- **`.sdlc/REVIEW.md`'s "a finding counted for the wrong reviewer".** This change counts no
  findings, so it is not in scope.

No invariant needs to change.

## Alternatives rejected

- **A `Sdlc-Train` trailer written at close.** Every train figure is in the change's committed
  records, readable at its commit as `_autonomy()` reads it. The intent allows a trailer only for
  a figure that exists only while landing, and none does. The train's state file does vanish,
  but the figures it holds (gates, ejections, moves) are copied into each change's records.
- **Inferring depth from the reviewers in `reviews/round-*`.** Whether a reviewer set is light
  depends on the host's `[light]` config at the time, which history doesn't pin. A recorded line
  is exact.
- **Recording depth per round.** A run never lightens, so the last reading is the run's depth.
  One line in `step.md` is enough.
- **Counting landing conflicts from `runs/land-resolved`.** That file is overwritten on each
  resolve and removed on ejection. The `resolve` rows in `land-times.jsonl` are append-only.
- **Counting the hand gate in the gate figures.** The intent asks for the pipeline's gate, and
  the hand gate runs outside the factory's slot discipline. It writes `Waited:` only to keep the
  shape pin.
- **Rendering the figures in the report.** `autonomy` and `cost` aren't in the report body yet
  either. The intent asks for the JSON, and adding the report is its own change.
- **Repeating mends under `pipeline`.** `autonomy.spurious_stops` already has them, and two keys
  for one count drift apart.

## Verification

```bash
uv run --group dev pytest -q tests/test_retro.py tests/test_modules.py tests/test_hand_gate.py -n auto
uv run --group dev pytest -q plugins/factory -n auto      # the factory's gate and step tests
./check.sh
uv run --quiet --script scripts/sdlc.py retro | python -c "import json,sys; print(json.load(sys.stdin)['pipeline'].keys())"
```

What healthy output looks like:
- Every test passes, including the new fixture tests for R2–R8, R11 and R13, and
  `check.sh` ends green with `claude plugin validate --strict` passing.
- Run on this repo, `retro` prints `pipeline` with `gates`, `red_gate`, `landing`, `depth`,
  `unreviewed`, `factory` and `by_hand`, and no `changes` without `--metrics`.
- `depth.coverage.measured` is 0 and `wait.n` is 0 until runs built after this change land: the
  figures start missing, not zero.

