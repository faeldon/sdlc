---
id: 169
slug: decisions-and-stops-counted
kind: spec
created: 2026-11-19
updated: 2026-11-19
---

# 169 — The retrospective counts decisions and stops · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

**Factory records.** These requirements cover the reader in `scripts/factory_records.py`, with tests in `tests/test_retro.py` unless named otherwise.

1. **R1.** `factory_records.autonomy_counts(show, listing)` returns None for a change with no decision file (`DECISION_FILE`), which is a change built by hand. It returns one dict of counts for a factory run. `test_autonomy_counts_are_none_for_a_change_built_by_hand` fails if a hand change gives a dict, or zeros.
2. **R2.** `escalations` counts every `DECISION: ESCALATE` that `opening()` reads. It reads the current decision file and every archived `decision-<n>.md` (`ARCHIVE_RE`). A run with two archived escalations and a current READY gives 2. `test_autonomy_counts_every_escalation_current_and_archived` fails on 0, 1 or 3.
3. **R3.** Each ledger line (`LEDGER_RE`) is counted once, by its mark:
   - A **default** line counts as exactly one of:
     - `kept`: the answer is exactly `KEPT_ANSWER`.
     - `confirmed`: the answer is exactly `CONFIRMED`, the landing's blanket confirmation.
     - `changed`: any other answer the person gave.
     - `settled`: the line carries `SETTLED`.
     - `superseded`: the line carries `SUPERSEDED`.
     - `open`: the line is unticked.
   - A **blocking** line counts as `answered` or `open`.
   - A **look** line counts as `seen` (the answer is exactly `LOOK_SEEN`, `seen`), `checked` (any other answer) or `open`.

   `KEPT_ANSWER` is a prefix of `CONFIRMED`. `test_autonomy_counts_read_each_ledger_answer_by_its_mark` fails if a landing-confirmed default counts as kept, or if a settled or superseded line counts as the person's.
4. **R4.** `mends` counts the lines of `runs/mended` (`MENDED`):
   - `<role> <n>` is a build mend.
   - `<role> land-<n>` is a landing mend.
   - Any other line is skipped.

   `test_autonomy_counts_tell_a_landing_mend_from_a_build_mend` fails if a landing mend counts as a build mend, or if a garbled line counts at all.
5. **R5.** A decision file whose answer `opening()` can't read leaves that change out of `escalations`' `n` and adds a retro problem naming the change and the file. It is never counted as zero escalations. `test_retro_autonomy_says_a_decision_it_cannot_read` fails otherwise.

**`retro`'s `autonomy`.** These requirements cover what `retro()` adds to its JSON.

6. **R6.** `retro()`'s JSON gains `autonomy`. Every count in it is summed only over the window's factory changes (R1 not None). `factory` and `by_hand` say how many of each there were. Each figure carries its `n`, and a rate or per-change figure is null whenever its `n` is 0. With a window of hand-built changes only, `test_retro_autonomy_leaves_hand_built_changes_out` asserts `factory == 0`, every `n == 0` and every rate null, never 0.
7. **R7.** `autonomy.auto_landed` reads each factory change's `Sdlc-Landed` trailer on its own commit:
   - `auto` when `by=auto`.
   - `person` when `by=person`.
   - `shipped` when the trailer is absent, meaning the change was shipped by hand.

   `share` is `auto / n`. `test_retro_autonomy_counts_auto_landed_from_the_change_commit` fails if a `by=auto` on the `Close` commit, rather than on the change's own commit, is counted.
8. **R8.** `autonomy.kept_default.rate` is `kept / (kept + changed)`. `confirmed` and `settled` are reported beside it and never enter the rate. The test in R3, run through `retro()`, fails if a confirmed default moves the rate.
9. **R9.** `autonomy.overturned` is `{"count": null, "n": 0, "unmeasured": <why>}`. `UNMEASURED` gains two entries, each with its `needs`:
   - "an approver's settled call the person overturned"
   - "a factory stop that cleared with nothing changed"

   `test_retro_says_what_autonomy_cannot_count` fails if either is missing, or if `overturned.count` is a number.
10. **R10.** `retro.py` reads factory records only through `sdlc.factory_records`, and never spells a record's name.
    - Every new copied name (`MENDED`, `ARCHIVE_RE`, `KEPT_ANSWER`, `CONFIRMED`, `SUPERSEDED`) is factory.py's own name and value.
    - The new names go into `RECORD_NAMES`.
    - `test_the_board_and_close_read_records_through_sdlc` also covers `retro.py`.

    The existing `test_no_factory_record_is_named_outside_its_reader` and `test_every_shared_name_is_the_factorys` (`tests/test_modules.py`) fail on a drift. A new `test_look_seen_is_the_decide_skills_answer` fails if `LOOK_SEEN` stops matching the `→ decided: seen` that `plugins/factory/skills/decide/SKILL.md` writes.

**After-gate stops (idea 2026-11-18-92).**

11. **R11.** `metrics.summarize()` keeps, for each `after_gate` stop, the gated skill whose span it fell in. `trailers()` then writes one `Sdlc-AfterGate: <skill> stops=<n>` line for each skill with at least one. `parse_trailers()` reads the lines back as `after_gate: {skill: {"stops": n}}`. The `Sdlc-Extra` and `Sdlc-Totals` lines are unchanged. `test_an_after_gate_stop_names_the_skill_whose_gate_it_followed` (`tests/test_metrics.py`) fails if two stops after `sdlc:ship`'s WAIT and one after `sdlc:spec`'s don't round-trip as `{sdlc:ship: 2, sdlc:spec: 1}`.
12. **R12.** `retro`'s `metrics.extra` gains `after_gate_by`, each skill's `count` and `changes`, and `after_gate_unnamed`. `after_gate_unnamed` counts the `after_gate` stops on recorded commits that carry no `Sdlc-AfterGate` line, which were closed before this change. `test_retro_names_the_skill_an_after_gate_stop_followed` fails if an older commit's stops are dropped, or are counted under a skill.

**Status nits.**

13. **R13 (nit 2026-11-18-86).** `held_by_rebase()` calls `_change_trees()` once. `rebasing_branches()` takes the list as an optional argument, and the board's caller is unchanged. `test_held_by_rebase_walks_the_change_trees_once` (`tests/test_sdlc.py`) counts the calls and fails on 2. The existing rebase tests in `tests/test_board.py` must still pass.
14. **R14 (nit 2026-11-18-87).** `_by_state()` places a record that has no `column` by calling `column()` on it, so there is one rule. It no longer uses its own `BY_STAGE` lookup. `test_by_state_places_a_record_without_a_column_as_column_does` is parametrized over every stage in `STAGES`, and over factory and manual modes. It fails if `_by_state` and `column()` disagree on any of them.

**Docs and boundaries.**

15. **R15.** These docs change in the same change, checked at review:
    - `docs/REFERENCE.md` *Retrospectives* names `autonomy` and each key's meaning.
    - REFERENCE *Metrics* names `Sdlc-AfterGate`.
    - `metrics.py`'s docstring contract gains the line.
    - `factory_records.py`'s docstring names retro as a reader.
    - AGENTS.md's map sentence "the board and close reach `factory_records.py` through their binding" names retro too.
16. **R16.** `retro` stays read-only. The existing tests that compare `git status` and `HEAD` before and after `retro` (`_state()` in `tests/test_retro.py`) still pass with factory fixtures in the window.

## Design

**What I took as given, each checked in the code:**

- A factory run's folder is committed with the change, so its files are readable at the change's own commit. That commit is `rec["sha"]` from `closed_changes()`, the `Close` commit's parent. Close's measure step already reads the same files through `run_counts(show, listing)`.
- `runs/stopped.md` is removed by the next `verdicts --record` that finds the cause gone (`cmd_verdicts`). `runs/step.md` is overwritten. So no committed record holds a stop that cleared by itself.
- A mend is the one stop a run clears without the person. The build skill runs `agent --task mend` itself (`skills/build/SKILL.md`, step 2). `agent` appends `<role> <round>` or `<role> land-<n>` to `runs/mended`.
- A restart archives the current decision, always an ESCALATE, as `decision-<n>.md` (`restart_state()`), so archives are past escalations.
- The person's answers in `decisions.md`:
  - `/sdlc-factory:decide` writes `→ decided: the assumed default, confirmed` (`KEPT_ANSWER`) when the person keeps a default, and `→ decided: seen` for a look.
  - The landing writes `→ decided: the assumed default, confirmed when landing` (`CONFIRMED`, `landing.py`) on every default still open at its yes.
  - The approver's own mark is `→ settled by the approver:`.
- No writer records a person overturning a settled call. The decide skill never asks one, and says a person "can still change the ledger by hand" in no defined shape.
- Factory stops already name the skill that follows: `WAYS` in `factory.py` reads "rerun /sdlc-factory:build {id}, or /sdlc:ship {id}". So idea 2026-11-18-92 means its own text: `metrics`' `after_gate` stops, the messages typed after a WAIT was answered, which record no skill.

**The reader (`factory_records.autonomy_counts(show, listing)`).** This is a pure function beside `run_counts()`, with the same callables and no git of its own. It reads the following:

- **Decisions.** The current decision through `show(DECISION_FILE)`; None means a hand-built change, so it returns None. Then `listing("")`, filtered by `ARCHIVE_RE` on the base name, gives the archives, each read through `show()`. Each answer is read with `opening(lines, DECISION_RE)`. A file it can't read goes into `unread`, a list of relative paths. The function never raises.
- **Ledger.** `show(LEDGER_FILE)`, split into lines and matched with `LEDGER_RE`. The marks are checked in this order:
  1. `SUPERSEDED`
  2. `SETTLED`
  3. unticked
  4. then the answer after `DECIDED`, compared for exact equality with `CONFIRMED`, `KEPT_ANSWER` and `LOOK_SEEN`.

  Equality, not `startswith`, because `KEPT_ANSWER` is a prefix of `CONFIRMED`.
- **Mends.** `show(MENDED.as_posix())`, matched as `^(\S+) (\d+)$` for build mends and `^(\S+) land-(\d+)$` for landing mends.

It returns:

```
{"escalations": int, "unread": [str],
 "blocking": {"answered": int, "open": int},
 "defaults": {"kept", "changed", "confirmed", "settled", "superseded", "open"},
 "looks": {"seen", "checked", "open"},
 "mends": {"build": int, "landing": int}}
```

New copies go in under `factory.py`'s names, so `test_every_shared_name_is_the_factorys` pins them with no new test: `MENDED`, `ARCHIVE_RE`, `KEPT_ANSWER`, `CONFIRMED` and `SUPERSEDED`. `LOOK_SEEN = "seen"` is core's own name for the decide skill's wording, pinned by R10's test against that `SKILL.md`.

**Retro's side (`scripts/retro.py`).**

- **Reading each change.** A small `_records_at(home, rec)` returns `(show, listing)` over `f"{rec['sha']}:{work_rel(home)}/{rec['name']}/…"`, built the way `closing._branch_files()` builds them, through `sdlc._git`. `_autonomy(home, changes)` calls `sdlc.factory_records.autonomy_counts()` once per change. It sums the results and adds one problem per `unread` path (R5).
- **Auto-landed.** `closed_changes()` already parses the change commit's trailers (`own`) for `findings`. It now also keeps `rec["landed"] = own.get("landed")`, so R7 costs no extra git call.
- **The JSON.** `retro()` adds `"autonomy"`:
  - `factory`, `by_hand`
  - `escalations` {`total`, `changes` (those with any), `per_change`, `n`}
  - `asked` {`blocking`, `default` (kept+changed), `look` (seen+checked), `per_change`, `n`}
  - `kept_default` {`kept`, `changed`, `rate`, `n`, `confirmed`, `settled`}
  - `overturned` {`count`: null, `n`: 0, `unmeasured`}
  - `auto_landed` {`auto`, `person`, `shipped`, `share`, `n`}
  - `spurious_stops` {`build`, `landing`, `changes`, `per_change`, `n`}, the mends
  - `looks` {`seen`, `checked`, `open`, `seen_share`, `n`}

  Shares are rounded to 2 places, like `_in_change_summary`. `n` is the count the figure divides by, and the figure is null at 0.
- **Not in the report.** `retro --report` and `templates/retro.md` are unchanged. Showing these figures is the scorecard's S14.

**`after_gate` by skill (`scripts/metrics.py`).**

- In `summarize()`'s `close_span()`, the stop marked `why = "after_gate"` also gets `stop["skill"] = span["skill"]`. The summary gains `after_gate: {skill: n}`, summed in the same loop that fills `stage["kinds"]`.
- `trailers()` appends `Sdlc-AfterGate: <_word(skill)> stops=<n>` after the `Sdlc-Extra` lines. `parse_trailers()` gets a named branch for `aftergate`, so several lines don't overwrite each other.
- `history_summary()` writes none. A commit without the line is unrecorded, never zero.
- `retro._extra_report()` gains `after_gate_by` and `after_gate_unnamed` (R12).

This extends the trailer contract; it doesn't redefine it. Every existing line keeps its exact shape.

**Status (`scripts/sdlc.py`).**

- **R13.** `rebasing_branches(root, trees=None)` uses `trees` when it is given, else it calls `_change_trees(root)` as now. `held_by_rebase()` gets the trees once and passes them on. The board's `_on_board()` call is unchanged.
- **R14.** `_by_state()`'s fallback becomes `column({"stage": rec["stage"], "problems": rec.get("errors") or [], "mode": rec.get("mode") or "manual"} | rec)`. `cli_status` sets `column` on every record, so its output is unchanged. Only callers that print `analyze()` alone (the tests) reach the fallback.

**Edge cases.**

- A window with no factory change gives `factory: 0` and every count's `n` 0. This is the scorecard's "no factory changes", never zeros.
- A factory change shipped by hand counts in every figure, and as `shipped` under `auto_landed`.
- A dropped change is never in `closed_changes()`, so it isn't counted.
- A ledger line that won't match `LEDGER_RE` is skipped, as `run_counts()` skips it.

## Contracts touched

- **Core reads factory records only through `factory_records.py` (163).** Every file name and parsing rule is copied there under factory.py's names. Retro reaches the module as `sdlc.factory_records`, through its binding. `tests/test_modules.py` R2, R3, R5 and R6 enforce all of this, and R10 extends R2 to `retro.py`.
- **`factory_records.py` is pure.** Git reads come in as the caller's `show` and `listing`. The module runs no subprocess and names no `sdlc`.
- **The factory is never imported.** Nothing in core loads `factory.py`, and the new constants are copies.
- **Metrics' trailer format: extend, never redefine.** One new line, `Sdlc-AfterGate`; no existing line changes. Measuring still never refuses: a failure inside `summarize` is caught where it is caught today.
- **Retrospectives: read-only but for its report.** `_autonomy` only reads `git show` and `ls-tree` at commits in the window (R16).
- **Release, publish and measuring never read the register.** Nothing here reads `.sdlc/work/inbox.md`.
- **The scripts run on Windows.** There's no new subprocess (`sdlc._git` only), no new file write, and repo paths are joined with `/` for git.
- **Nothing about a project.** Fixtures use neutral change names (`001-keep-one-draft`), and the tests cite no change number from this repo's history.
- **Sensitive paths.** The design doesn't touch `scripts/closing.py` or `landing.py`: retro builds its own `show` and `listing` (see Alternatives).

No invariant needs to change.

## Alternatives rejected

- **Write the counts as new `Sdlc-*` trailers at close and have retro read them.** That covers only changes closed after this one lands. The records are already in every closed change's commit, so reading them at retro counts the whole window now, including every factory change already landed. The cost is a few `git show` calls per factory change per retrospective.
- **Count spurious stops from `runs/stopped.md`.** It is removed when its cause clears, so it never reaches history. Counting "a stop that cleared on rerun with no change" needs the factory to keep a committed log of each stop it records. That is new factory behaviour the intent didn't ask for, and a candidate seed. Until then it is listed under `unmeasured`.
- **Reword the factory's stop to name the skill that follows (the intent's paraphrase of -92).** `WAYS` and `WAYS_WHY` already name `/sdlc-factory:build` and `/sdlc:ship`. The idea's own text asks for `after_gate` stops to record their skill, which nothing does today.
- **Count landing-confirmed defaults as kept.** `CONFIRMED` is one yes covering every open default at the landing, not an answer to each one. Counting it would push the kept-default rate up and make the factory look over-asking. It is reported beside the rate as `confirmed`.
- **Read an overturned settled call from a hand-edited ledger line.** No writer defines that shape, so any rule would be guessing at free-form edits. It is reported as unmeasured, saying what would record it.
- **Extend `run_counts()` instead of adding a reader.** `run_counts()` feeds close's `Sdlc-Rework` line. Changing its shape risks changing that trailer. A second function keeps close's output exactly as it is.
- **Reuse `closing._branch_files()` from retro, or move it into `sdlc.py`.** Calling it from retro would break the rule that a function lives in `closing.py` only when only close calls it. Moving it would edit a sensitive path for no change in behaviour. Retro's own six-line helper reads at a commit rather than a branch, which is a different use anyway.
- **Keep `_by_state`'s own `BY_STAGE` fallback and just add `test`.** That keeps two rules for one decision. Calling `column()` makes drift impossible.

## Verification

```bash
./check.sh
```

Healthy: ruff, ruff format, pytest and `claude plugin validate --strict` all pass.

```bash
uv run --group dev pytest -q -n auto tests/test_retro.py tests/test_metrics.py tests/test_modules.py tests/test_sdlc.py tests/test_board.py
```

Healthy: every test named in R1–R14 is collected and passes, and the existing rebase, extra-stop and record-name tests still pass.

```bash
uv run --group dev pytest -q -m portable
```

Healthy: it passes. Nothing new is platform-bound.

```bash
uv run --quiet --script scripts/sdlc.py retro
```

This is read-only, run from this repo's main checkout. Healthy:

- `autonomy.factory` is above 0, since this repo has closed factory changes since the last retrospective.
- Every rate sits beside its `n`.
- `overturned.unmeasured` is set.
- `metrics.extra.after_gate_unnamed` holds every existing `after_gate` stop, because no older commit has the new line.
- `git status` is clean afterwards.

```bash
uv run --quiet --script scripts/sdlc.py status
```

Healthy: same sections and same placement as before the change.

**Boundaries.**

- **Always:** count only committed records, only factory changes, and put an `n` on every figure.
- **Ask first:** any change to factory behaviour, such as a stop log or a record for an overturned call. Each is a seed, not part of this change.
- **Never:** write from `retro`, change an existing trailer's shape, read the register, or put a figure in the retro report.
