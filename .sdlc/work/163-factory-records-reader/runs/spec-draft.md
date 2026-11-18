---
id: 163
slug: factory-records-reader
kind: spec
created: 2026-11-18
updated: 2026-11-18
---

# 163 — One reader in core for the factory's records · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions checked in the code: the copies are in `scripts/sdlc.py` (lines ~3000–3122 for the hand gate, ~5051–5462 for the run's records), `scripts/closing.py` (`_factory_files`, `_agent_sessions`, `_agent_models`) and `scripts/board.py` (its own regexes at lines 52–88, `opening`, `_factory`, `read_step`, `read_land_step`, `read_land_times`, `cost`, `_reviewed`). `metrics.py` and `indicators.py` are pure and loaded once by `_load_metrics()`. `retro.py` reads no factory record. 162 has not landed: nothing in `scripts/` reads a lead time yet.

1. **R1. One module, pure, loaded once.** `scripts/factory_records.py` exists. `sdlc.py` loads it by path exactly once, as `factory_records`, the way `_load_metrics()` loads `metrics.py`, and never binds `sdlc` into it. The module imports no `subprocess`, uses no name `sdlc`, calls no `spec_from_file_location`, never names `sdlc.py` or `factory.py` as a file to load, and does nothing at load but define names. Test: `tests/test_modules.py::test_factory_records_is_pure_and_loaded_once`. It fails on a second load site, on a `subprocess` or `sdlc` reference in the module, or on an `sdlc.<name>` evaluated at load.
2. **R2. The board and close use the same module.** `board.py` and `closing.py` reach the module only as `sdlc.factory_records.<name>`. Neither loads it. Test: `tests/test_modules.py::test_the_board_and_close_read_records_through_sdlc`. It asserts no `spec_from_file_location` naming `factory_records.py` in either file, and that `sdlc.factory_records is sdlc._load_board().sdlc.factory_records`.
3. **R3. The copies live in the module and nowhere else.** Every name in *Design → What moves* is defined in `factory_records.py`. None of the old names (`FACTORY_*_RE`, `FACTORY_STOPPED`, `factory_reading`, `_factory_opening`, `_gate_attempts`, `_hand_placeholders`, `HAND_DEFUSE`, the board's `VERDICT_RE` … `NO_DECISION`, `opening`, `read_step`, `read_land_step`, `read_land_times`, `cost`, `_factory`, `_reviewed`, and the rest of the table) is still defined in `sdlc.py`, `closing.py` or `board.py`. Test: `tests/test_modules.py::test_the_record_readers_live_in_factory_records`. It uses a `RECORD_NAMES` set and an `OLD_NAMES` set, like `CLOSING_NAMES`.
4. **R4. The consumers stay in `sdlc.py`.** `needs_of`, `column`, `seen_stage`, `answered`, `decide_step`, `touched_paths`, `BY_STAGE`, `FACTORY_STOP_NEEDS`, `hand_gate`, `hand_build`, `cmd_gate`, `GATE_TIMEOUT`, `GATE_TAIL`, the slot copies (`SLOT_NAME`, `_try_lock`, `_gate_jobs_at`, `FACTORY_CONFIG`) and the `[ui]` copies (`_ui_at`, `_current_shots`, `UI_DEFAULTS`) stay defined in `sdlc.py`. The same test as R3 asserts it, so the module's boundary can't grow without someone noticing.
5. **R5. No record named outside the module.** No string literal in `scripts/*.py` or `scripts/trackers/*.py` other than `factory_records.py` names a factory record when it holds no whitespace. This covers f-string pieces. Docstrings are not counted, and neither is prose such as a help text or a problem message, which holds spaces. The names are `decision.md`, `decisions.md`, `stopped.md`, `step.md` (so also `land-step.md`), `verified.md`, `costs.jsonl`, `land-times.jsonl`, `gate.md` (so also `.gate.md`), `round-` and `.sessions`. Test: `tests/test_modules.py::test_no_factory_record_is_named_outside_its_reader`. The test keeps the list itself, so the module can't loosen it. Its checker also runs on a snippet, `(folder / "decision.md").read_text()`, and must report it, so the test is shown to fail.
6. **R6. Every copied constant equals factory.py's, by name.** The module gives each constant, regex and path it copies from `factory.py` the name `factory.py` uses. One test pins every name the two modules share, for each value that is a `str`, number, `Path`, compiled pattern (pattern and flags) or tuple of those. Test: `tests/test_modules.py::test_every_shared_name_is_the_factorys`. A copy added later under the factory's name is pinned with no new test, and changing either side fails it.
7. **R7. The behavioural pins read the module.** These existing tests now compare the module's function with the factory's, and nothing else in them changes:
   - `opening` (`tests/test_metrics.py::test_sdlcs_opening_is_a_pinned_copy_of_the_factorys`, `tests/test_board.py::test_the_boards_opening_is_a_pinned_copy`, merged into one test over `opening-cases.json`)
   - `read_step`, `read_land_step`, `read_land_times` and `cost` against `run_cost` (`tests/test_board.py`)
   - `reasons` against `escalation_reasons`, and `newest_round` (`tests/test_metrics.py`)
   - `placeholders` and `DEFUSE` shapes against `_placeholders` and `DEFUSE` (`tests/test_hand_gate.py::test_the_placeholders_are_the_factorys`)

   Each still fails when its pair drifts.
8. **R8. A pure move: output unchanged.** `status`, `status --all`, the board's `/state.json` (columns, cards, `needs`, `next`, problems text), the hand gate's record and verdict, and close's measure trailers come out the same on every existing fixture. The only edits to existing tests change where a test reads a moved name (`sdlc.FACTORY_X` → `sdlc.factory_records.X`, `board.X` → `sdlc.factory_records.X`, `sdlc._hand_placeholders(t, r)` → `sdlc.factory_records.placeholders(t, r, main)`). No expected value, fixture or assertion changes. Review checks this on `git diff <base> -- tests/`. The tests that hold the output are `tests/test_board.py`, `tests/test_sdlc.py`'s status tests, `tests/test_hand_gate.py::test_the_record_is_the_factorys_shape_line_for_line`, and the `_factory_files` tests in `tests/test_metrics.py`, `tests/test_archive.py`, `tests/test_factory.py` and `tests/test_hand_gate.py`.
9. **R9. Close's adapters keep their signatures.** `closing._factory_files(main, branch)`, `_agent_sessions(main, branch, folder)` and `_agent_models(main, branch, folder)` stay in `closing.py` with the same signatures and return values. Each supplies git reads (`sdlc._git(… "show" …)` and `ls-tree`) to the module's parser and parses nothing itself. The `_factory_files` tests named in R8 pass unchanged and are the check. `closing.py` remains the only place those git reads run.
10. **R10. Never raises, as before.** Every reader that was documented "never raises" (`reading`, `read_stop`, `read_land_stop`, `landing`, `first_build`, `upgraded_build`, `hand_gate`'s record read) keeps its exception handling unchanged. The existing tests of unreadable and garbled records are the check: `tests/test_sdlc.py` `factory_reading` cases, `tests/test_board.py` garbled and stopped cases, and the `hand_gate` problem tests.
11. **R11. The map says where the copies are.** `AGENTS.md` *Modules loaded by path* lists `factory_records.py` among the pure modules. *The board* and *The factory* paragraphs say the board, `status`, the hand gate and close read the factory's records through `scripts/factory_records.py`, its copies pinned by `tests/test_modules.py`. The module's docstring is its contract: what it holds, the rule for what moves into it, that it is pure, and that the factory's names are kept. `board.py`'s and `closing.py`'s docstrings point to it. Review checks this. `./check.sh` passes.

## Design

**The module.** `scripts/factory_records.py` follows the shape of `metrics.py`. It is pure: no `subprocess`, no `sdlc` binding, and nothing evaluated at load but definitions. `sdlc.py` gets a `_load_factory_records()` next to `_load_metrics()`, sets `factory_records = _load_factory_records()` at module level, and calls it as `factory_records.<name>`. Because `board.py` and `closing.py` are bound to a live view of `sdlc`'s globals, they reach the same module object as `sdlc.factory_records.<name>`. That answers the board question: the board is loaded only when `board` runs, but `status` needs the records on every run, so `sdlc` loads the module eagerly and the board borrows it. A second load would create a second module object, and a test's stand-in on one would not reach the other.

**The boundary.** The module holds two things:

1. Every constant, regex and path that is a copy of `factory.py`'s.
2. Every function that turns a factory record's text, or a change folder's record files, into fields.

It opens files on disk in a change folder, which is not a subprocess, as `metrics.py` reads transcripts. When a record has to come from git history (close's measure step reads the branch, and the board's typical times read `Close` commits), the caller passes callables. `show(rel) -> str | None` reads a file. `listing(rel) -> str` lists a tree. The module calls them and never runs git. The rules over the fields stay in `sdlc.py` (R4): `needs_of`, `column`, `seen_stage`, `answered`, `decide_step` and `FACTORY_STOP_NEEDS`. These are core's own policy, not copies, and they read no record. The same goes for the hand gate's runner, its write of `build/gate.md` (including reading back the earlier attempts it keeps), and `hand_build`, which runs git. The slot and `[ui]` copies are copies of `factory.toml` and the gate locks, not of a run's records, so they are out of scope.

**What moves.** Names take `factory.py`'s where it has one (R6). Otherwise a function keeps its name less the `factory_` prefix the module name already says.

| Now | In `factory_records.py` |
|-----|------|
| `sdlc.FACTORY_{VERDICT,DECISION,CHANGE,LEDGER,REASON,LOOK_SOURCE,KEPT,DROPPED,STOPPED,NEXT,PROBLEM,STEP,AFTER,ROUND,UPGRADED_FILE}_RE`, and board's `VERDICT_RE`, `DECISION_RE`, `CHANGE_RE`, `KEPT_RE`, `DROPPED_RE`, `LEDGER_RE`, `STEP_RE`, `ROUND_RE`, `AFTER_RE`, `PROBLEM_RE` | the same names without `FACTORY_`, one copy each |
| board's `LIMIT_RE`, `REVIEWERS_RE`, `SINCE_RE`, `STUCK_RE`, `UNTESTABLE_RE`, `MOVES_RE`, `TRAIN_RE`, `WAITS_RE` | same names |
| `sdlc.FACTORY_{REASON_KINDS,DECIDED,SETTLED,STOPPED,STEP,LAND_STEP,LAND_STOPS,LAND_STEPS,AGENT_TIMEOUT,RECONSIDER}`, board's `SETTLED`, `RECONSIDER`, `VERIFIED`, `COSTS`, `STOPPED`, `STEP`, `LAND_STEP`, `LAND_TIMES`, `LAND_STOPS`, `PAUSES`, `REVIEWER_ROLES` (→ `REVIEWERS`), `OPEN_BOX`, `NO_DECISION` | same names without `FACTORY_` |
| `sdlc.FACTORY_GATE_FAIL_RE`, `GARBLED_LEDGER` | `GATE_FAIL_RE`, `GARBLED_LEDGER` |
| `sdlc._factory_opening`, board's `opening` | `opening` |
| `factory_stop`, `factory_land_stop`, `factory_landing`, `factory_first_build`, `factory_upgraded_build`, `factory_newest_round`, `factory_reasons`, `factory_reading` | `read_stop`, `read_land_stop`, `landing`, `first_build`, `upgraded_build`, `newest_round`, `reasons`, `reading` |
| board's `no_verdict`, `read_step`, `read_land_step`, `read_land_times`, `cost`, `_factory`, `_reviewed`, and the `runs/builder.sessions` mtime read in `_progress` | `no_verdict`, `read_step`, `read_land_step`, `read_land_times`, `cost`, `card_reading(folder, problems)`, `reviewed`, `builder_started(folder)` |
| `closing._factory_files`'s parsing, `_agent_sessions`'s and `_agent_models`'s | `run_counts(show, listing, folder)`, `session_roles(show, listing, folder)`, `session_models(show, folder)`; closing keeps the three adapters (R9) |
| board's gate-seconds parse in `history_samples` | `gate_seconds(text)`; `history_samples` keeps its git walk and passes text |
| `HAND_GATE`, `ATTEMPT_VERDICT_RE`, `BUILD_RE`, `SECONDS_RE` (board's copy too), `_gate_attempts` | same names, `gate_attempts` |
| `CLONE_MARK`, `HOME_MARK`, `TMP_MARK`, `USER_MARK`, `TERM_MARK`, `HAND_DEFUSE`, `HAND_TERMS_FILE`, `_hand_login`, `_hand_terms`, `_hand_placeholders` | same marks, `DEFUSE`, `TERMS_FILE`, `_login`, `_terms`, `placeholders(text, root, main)` |

`placeholders` takes the main checkout as an argument. `sdlc.py` keeps the one `git worktree list --porcelain` call that `_hand_placeholders` makes now, in a small helper (`_hand_main(root)`, which returns the listing's first worktree or else `root`, exactly as today), and passes the result. The module stays free of subprocesses, and the record's text is the same.

**What stays in the board.** The track layout (`TRACK`, `AT`, `LAND_TRACK`, `LAND_AT`, `LAND_LABEL`, `LAND_TIMED`, `LAND_TIMES_STEPS`, `LAND_OPEN`, `CAP`), `_progress` and `_land_progress` (presentation over the parsed record, reading the file through the module), `typical_times`, `history_samples` (its git walk), and `step_samples`. `step_samples` maps cost rows onto the board's own track and is not a copy of anything in `factory.py`. Its JSON reading of `costs.jsonl` lines is unchanged. The `read()` labels in `_entry` (`"build/gate.md"`, `"runs/stopped.md"`, `"runs/step.md"`) become the module's path constants' `.as_posix()`: same text, and R5 holds.

**Two ledger readers, side by side.** The board's `_factory` and `sdlc`'s `factory_reading` each parse `decisions.md`. Unifying them would change the card's fields' derivation, so for a pure move both go into the module as they are (`card_reading`, `reading`), next to each other, and the docstring notes it. Merging them is S3's to do, from one module, with no further copy.

**Edge cases.** All of these keep their behaviour because the bodies move unchanged:
- A record that won't read gives a `problems` line, never an exception (R10).
- Close's measure step treats an exception in `_factory_files` as `rework=failed` (`finish()` in `measure_change`). That `try` stays in closing.py around the adapter.
- `first_build` and `upgraded_build` use `time.time()` and `stat`, which are allowed in a pure module.
- Windows: the module only reads, with `encoding="utf-8", errors="replace"` as now, and imports no `fcntl` or `msvcrt`.

**162 (lead time).** Whichever lands second rebases onto the other. If 162 lands first, its new read of a run's files in close's measure step moves into the module here; R5 fails until it does. If this lands first, 162 adds its parser to the module, with no new copy.

## Contracts touched

- **Modules loaded by path** (AGENTS.md): every module is loaded by path, never imported, and bound only when it calls `sdlc.<name>`; pure modules have no subprocess and no import of `sdlc.py`. The new module is loaded by path once, by `sdlc.py`, and is pure in exactly `metrics.py`'s sense (R1). The board and close reach it through their existing live binding (R2). The *Modules loaded by path* paragraph gains its name (R11), which updates the map. No rule changes.
- **The factory** (AGENTS.md): `factory.py` is never imported or run by core, and each side reads the other's files with copies of its parsing, pinned by tests. This design still copies, never imports: the module names no `factory.py` and loads nothing (R1). The pins become one name-wide test plus the behavioural ones (R6, R7). `factory.py` itself is not edited.
- **The board** (AGENTS.md): it writes nothing, serves only `127.0.0.1`, builds nodes with `textContent`, and reads with pinned copies. Nothing here touches the server, the routes or the page. The board still writes nothing; it now reads through the module.
- **Closing** (`[review] sensitive`, `tests/test_modules.py`'s line between `sdlc.py` and `closing.py`): a function lives in closing.py when only closing.py code calls it. The three adapters stay there, called only by `measure_change`. The parsing they used to hold moves to the module, which `test_the_line_between_script_and_module_holds` doesn't cover (it is not `sdlc`). Close's git steps, the lock and the push are untouched. Because closing.py is in the diff, the review is at full depth.
- **Metrics** (AGENTS.md): the trailer format and event list are a contract; measuring never refuses. The input values to `metrics.rework` and `metrics.happy` are the same (R8, R9), so the trailers are unchanged.
- **Windows** (`tests/test_windows.py`): no platform module at top level, `encoding="utf-8"` on every text read, `as_posix()` for shown paths. The module follows all three. It writes nothing, so the `newline` rule doesn't apply.
- **Nothing local** (`tests/test_nothing_local.py`): the `DEFUSE` shapes and marks move as they are. The module's docstring names no host and no path on this machine.
- **The hand gate's record** (`tests/test_hand_gate.py`): it is the factory's shape, line for line. The writer stays in `cmd_gate`; its parsing and placeholders move. The line-for-line test is unchanged (R8).

No invariant needs to change.

## Alternatives rejected

- **Bind the module to `sdlc` like `retro.py`.** That would let it call `sdlc._git` directly. But it would bring git into the copies and tie the pin tests to loading all of `sdlc.py`. The pure shape lets a test load the module alone and compare it with `factory.py`.
- **Let `board.py` load the module itself.** That makes two module objects, and a stand-in on one misses the other. It would also break the "loaded by path once" rule `test_the_modules_are_loaded_by_path` holds for each module.
- **Move `needs_of`, `column` and `seen_stage` in too.** They are core's rules, not copies of the factory's. `seen_stage` reads `findings.md` and git, which is core's own state. Moving them would turn a records reader into a policy module, and S3 counts records, not columns.
- **Move the hand gate's writer (`cmd_gate`'s record composition) too.** It runs a host command and writes. A pure reader that writes, or a writer split across two files, would weaken both. The line-for-line test already pins the shape it writes.
- **Unify the board's and `status`'s ledger readers now.** The fields differ in subtle ways (look lines, settled defaults, problems on the card), so the outputs could change, which breaks the pure-move outcome. That is left to S3, with both readers next to each other.
- **A test that bans `read_text` on record paths outside the module.** It can't tell a record path from any other `Path` without type information. A literal scan over the record names (R5), plus every path built from the module's constants, catches the realistic slip: a new reader with its own `"decision.md"`.
- **Keep the `FACTORY_` prefix inside the module.** Using `factory.py`'s own names is what lets one test pin every shared name automatically (R6). With the prefix, each new copy would need its own pin line, which is how the copies spread in the first place.
- **Edit `factory.py`'s comments that say "the board keeps its own copies".** They remain broadly true (the board's copies now sit in the module). Leaving the factory plugin untouched keeps this a core-only change.

## Verification

```bash
uv run --group dev pytest -q tests/test_modules.py           # R1–R6: all pass, the new tests included
uv run --group dev pytest -q tests/test_board.py tests/test_hand_gate.py tests/test_metrics.py \
  tests/test_archive.py tests/test_sdlc.py tests/test_factory.py   # R7–R10: pass, no expected value changed
uv run --group dev pytest -q -m portable                     # what CI's Windows job runs: passes
./check.sh                                                    # ruff, format, pytest -n auto, plugin validate: green
git diff <base> --stat -- tests/                              # only renamed reads and the new tests in test_modules.py
git diff <base> -- tests/ | grep '^[-+].*==' | grep -v 'factory_records\.'   # R8: empty but for the new tests' lines
rg -n '"[^" ]*(decisions?\.md|stopped\.md|step\.md|verified\.md|costs\.jsonl|land-times\.jsonl|gate\.md|round-|\.sessions)' scripts \
  --glob '!factory_records.py'                                # R5 by hand: only docstring or prose hits
uv run --quiet --script scripts/sdlc.py status --all         # same sections and needs as before the change
```

A healthy result: every command exits 0; `test_modules.py` reports the new tests; the `tests/` diff holds no changed expected value; and `status --all` run before and after on this repo prints the same columns and needs, apart from the `touched_ago` and quiet times, which depend on the clock.

