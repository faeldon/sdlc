---
id: 104
slug: landing-follows-main
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 104 — The landing follows main and reviews its own fixes · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

**This change builds after 097 lands** (`depends_on: [097]`). It uses these parts of 097 as they are and has no copy of any of them:

- `_amend_record()` and `_dirty()` (097 R1–R5). The amend lands only on a `HEAD` that carries `Sdlc-Landed:`, and it refuses any path outside the change's folder.
- `land` amending that record on a `stage: shipped` change before `sdlc.py base` (097 R3).
- `land_verdict(root, folder, cfg, n)` (097 R12).
- `resolution_signals()` and the `land-<n>` marker (097 R10, R11).
- The rule that a `sdlc.py resolve` resolution counts as reviewed only when its files match the newest complete round's snapshot (097 R13).
- `land --close` refusing `by=auto` over a resolution no review passed (097 R15).
- A resolved change in a batch that passed itself closing in the same landing once its review passes (097 R16).

Each test named below is in `tests/test_land.py` unless it says otherwise.

**Following main**

R1. Once 097's `_amend_record()` and 097's R15 check have passed, and before it hands off to `sdlc.py close`, `factory.py land <NNN> --close` checks whether the base branch has commits the change's branch lacks. It counts with `git rev-list --count HEAD..refs/heads/<base>` in the worktree, taking the base from `_base()`, never a literal. If the base has moved, it runs no `close` and returns `state: moved` with `moves: <k>`. `test_main_moving_before_close_sends_the_landing_back_to_its_rebase` fails if `close` is attempted or a `Close` commit appears.

R2. The `moved` path amends nothing of its own. The landing's record is already in the change's commit through 097's `_amend_record()` call in `cmd_land_close()`, made before this check, and `runs/land-moves` (R5) is written before that call so the same amend carries it. No second amend and no second stray-path check exist in the change (097 R5 still holds). The same test asserts the round-1 review and `runs/land-moves` are in the commit before the re-entry.

R3. Running `land <NNN> --by <who>` again on the `shipped` change goes through 097's R3 path (amend, then `sdlc.py base`). That opens round `land-<n+1>` and returns `rebased` or `conflict`. This change adds no code there; its test pins the whole chain. `test_main_moving_before_close_sends_the_landing_back_to_its_rebase` moves `main` between a passing landing review and `land --close`, and asserts, in order:
- `moved`;
- `rebased` in round 2;
- `next: gate`, then `review` with `missing: [behaviour]`, then `pass`;
- a `Close` commit on the base branch, with `Sdlc-Landed` still on the change's commit.

R4. If `sdlc.py close` itself refuses, `land --close` counts the base again. If the base has moved and close's `done` is empty, it returns `moved` too and does not pass the refusal through as a stop. It never matches close's refusal text. `test_a_move_racing_close_reads_as_moved` stubs `_sdlc` to refuse after the check and asserts `state: moved`.

R5. The loop is bounded by `[land] moves` in `.sdlc/factory.toml`, a whole number above 0 (default 3). `_land()` reads it from the base branch's copy, beside `auto` and `batch`, so a change can't raise its own bound. Anything else gives a warning and the default. Each `moved` adds one line to `runs/land-moves` (the base tip it saw). Once `moves` lines are recorded, a further move returns a refusal: "`<base>` moved `<moves>` times while `<NNN-slug>` landed: run /sdlc-factory:land again, or /sdlc:ship it by hand". Two tests cover it:
- `test_a_landing_stops_after_land_moves_moves` sets `moves = 1` on the base branch and fails if a second move is followed.
- `test_the_bound_on_following_main_is_the_base_branchs` sets `moves = 10` on the change's branch only and fails if the default isn't used.

R6. The land skill sends `moved` back to Step 3.1 for the same change with the same `--by`. Every rule of Step 3 then applies to the new round:
- the gate;
- behaviour alone after a clean rebase;
- the builder and every reviewer at the run's depth after a conflict;
- in a batch that passed itself, a resolved change closes once its review passes (097 R16), with 097's R15 as the script's guard.

The loop lives in the skill's prose, never in a bash loop. `tests/test_skills.py` still passes: one WAIT, every command with its rule, and every rule used.

R7. The WAIT's question names the bound, taken from `config`'s `land.moves`:

> `Land <n> changes in this order, <…>, each shipped with its approver's impact, committed, brought up to date with <base> as often as it moves while landing, up to <moves> times (a conflict resolved by its builder and reviewed again), and closed, pushed as git.push says? (yes / yes, with a fix / leave one out / no)`

`READS_CONFIG["sdlc-factory:land"]` in `tests/test_skills.py` gains `factory.land.moves`, so the skill fails the test if it stops naming `land.moves`.

**A fix asked for at landing**

R8. `yes, with a fix` approves the batch: it is a chosen `yes, …`. The skill takes the person's words for the fix, and the change they name, from what they typed in Other, or asks for them as plain text. That question is not a gate. After that change's Step 3.1 and its rebase round pass, the skill writes the words at the end of the change's `decisions.md` as a ticked `- [x] R<k> (person, fix): <words>` line, `<k>` one past the highest `R` there, and runs `factory.py land-fix <NNN> --ask R<k>`: the words never reach a command line, as a revision's and a restart's never do (the person's `R2`, after round 1). The command:
- refuses unless the change is `shipped`, `R<k>` is a ticked `(person, fix)` line in `decisions.md`, and `land_verdict()` for the current round is `pass` or no round is open;
- opens round `land-<n+1>`;
- copies the line's words to `build/land-<n+1>.ask.md`, never under `reviews/land-<n>/`.

`test_a_fix_asked_at_landing_is_built_gated_and_reviewed_at_depth` covers it, and `test_a_fix_is_asked_by_its_line_in_decisions_md_never_on_a_command_line` fails if words with a quote or `$(`, an unticked line or another kind's line open a round.

R9. `factory.py agent <NNN> --task land-fix` resumes the change's builder with the person's words. The task is added to `RESUMES`, `LAND_TASKS`, `TASKS` and `TASK_ROLE`. The prompt says: edit only what the fix needs, run no git command, end with `## Evidence`. The reply goes to `build/land-<n>.md`. The task refuses with no ask in the round. The same test asserts the prompt holds the words and the reply's target.

R10. `factory.py land-fix <NNN> --commit` commits the builder's edits through 097's `_amend_record()`. That function gains one keyword, `also: list[str] = ()`: paths outside the folder that it stages and admits. The default leaves 097's behaviour byte for byte. `also` is every path `_dirty()` lists outside the change folder, which the command returns as `fixed`. The command refuses when that list is empty or the round has no ask. The new `HEAD` has no current gate, so `land-verdicts` returns `next: gate`. Three tests cover it:
- The same test fails if the gate is skipped.
- `test_a_landings_record_never_takes_in_a_path_outside_its_folder` (097) still passes unedited.
- `test_a_fix_commit_needs_an_ask` fails if `--commit` amends in a round with no ask.

R11. A fix round is reviewed at the run's depth. `land_verdict()` wants the run's reviewers when the round has a `build/land-<n>.ask.md`, as it does when `runs/land-resolved` exists, and its output adds `fixed: true`. The `land-review` prompt says the round reviews a fix the person asked for, and quotes the fix. The same test asserts `missing` is the run's reviewers, not `[behaviour]`.

R12. A fix made at landing stays a risk signal. `land_signals()` adds "a fix was made while landing" whenever any `build/land-*.ask.md` exists, so a later landing that passed itself is refused on it, at `land` and at 097's `land --close` check. `test_a_fix_at_landing_is_never_landed_by_auto_later` fails otherwise.

**A fix made any other way is recorded**

R13. At `stage: test`, before ship, `land` compares `_tree_hashes()` with the snapshot of the newest complete build round. This is the round 097's R13 reads, taken from `_rounds_at_depth()`, by the same rule: a path absent from both counts as unchanged. The paths that differ are the change's unreviewed paths. When there are any, `land_signals()` adds "changed since its last review: `<paths>`". When there is no complete round or no snapshot, it adds "no snapshot of its last review". Either one refuses `--by auto`, and `land-check` shows it at the WAIT. A `sdlc.py resolve` resolution after the last round shows up here as well as in 097's signal; both say the same thing, and neither replaces the other. `test_a_hand_edit_after_the_approver_is_a_signal_and_recorded` edits a file after the snapshot, then asserts the signal and the refusal of `auto`.

R14. That landing's commit says so. `land_message()` gains `unreviewed: list[str] | None`, beside 097's `nits`. It writes `Sdlc-Landed: by=person unreviewed=<n>`, or `unreviewed=unknown` with no snapshot, plus a body line before the trailers: `Changed since its last review: a, b`. A change with nothing unreviewed keeps the bare `Sdlc-Landed: by=<who>`. `test_a_landed_commit_says_who_passed_its_gate_and_carries_no_review_count` passes unedited. The new test asserts `metrics.parse_trailers(body)["landed"] == {"by": "person", "unreviewed": 2}`.

R15. Close's measure carries the field forward. Where `sdlc.py` reads `landed` from the branch tip, it also reads `unreviewed`. It writes `unreviewed=<n|unknown>` on `Sdlc-Totals` beside `auto=`, only for a landed change whose tip has the field. This extends the trailer format; nothing is redefined. A case in `tests/test_metrics.py`, built on the existing `LANDED` events, fails if the field is missing, or if it appears on an unlanded change. The retrospective report's line for it is a later seed, not this change.

**Docs**

R16. Two docs are updated; both are context docs, checked at ship:
- `plugins/factory/README.md`: `moves = 3` in its `[land]` example ("the most times a landing follows the base branch"), the follow loop, and the fix at landing.
- `docs/REFERENCE.md`, *Metrics*, the `Sdlc-Landed` paragraph: what `unreviewed=` means on `Sdlc-Landed` and on `Sdlc-Totals`.

## Design

**What exists after 097, checked in 097's spec and round-1 report.**
- `cmd_land_close()` runs `_amend_record()` and then hands off to `sdlc.py close`.
- `cmd_land()` amends on `stage: shipped` before `sdlc.py base`.
- `_amend_record()` refuses anything outside the folder, and amends only a `HEAD` that carries `Sdlc-Landed:`.
- `land_verdict()` decides `pass` for a round.
- `land_round()`, `_land_gate_state()` and `cmd_gate --land` work per round, keyed by `HEAD` (`landed_build()`).

A move is therefore "go back to the step that already handles a moved base"; a fix is "one more round, opened by the person instead of by a rebase". Both reuse every per-round piece.

**The move loop.**

```
land --by X ──► current ───────────────────────────────────► land --close ──► (closed)
     ▲    └──► rebased/conflict ─► gate, review, land_verdict=pass ─┘   │
     │                                                                  └─► moved (k < moves)
     └──────────────────────────────────────────────────────────────────────┘
```

`cmd_land_close()` gets these additions, in this order, with nothing else changed:
1. `_behind(root)`: the factory's own `rev-list` count. It never imports `sdlc.py`.
2. If the base has moved: check `runs/land-moves` against `cfg["land"]["moves"]` and refuse at the bound. Otherwise append a line, with `newline="\n"`.
3. 097's `_amend_record()`, which carries the new line in (R2).
4. 097's auto check.
5. If the base had moved, return `moved`. Otherwise hand off to `sdlc.py close`.
6. If close refuses, `_behind()` is above 0 and `done` is empty, append a line and amend through `_amend_record()`, as in steps 2–3, then return `moved`.

Because step 2 writes before the amend, a move is always recorded in the commit it was found on. `_land()` gains `moves`, validated as `batch` is, with its warning reworded to "auto = true|false, batch or moves = a whole number". `DEFAULTS["land"]` gains `"moves": 3`. `factory.py config` shows it with no change, since it prints the whole `land` table.

The count is per change and travels with it. A change at its bound has to be landed by a person, or by a later `/sdlc-factory:land`, which refuses on that change's next move.

**A fix at landing.** The fix is built after the change's commit, so its gate and review use the machinery keyed on `HEAD`, and nothing is written before the yes.
- `cmd_land_fix(root, ident, ask, commit)`:
  - `--ask R<k>` checks the stage, the `(person, fix)` line and `land_verdict()`, opens the next round, and copies the words to `build/land-<n>.ask.md`.
  - `--commit` checks for the ask, lists `_dirty()` outside the folder, and calls `_amend_record(root, folder, also=those)`.
- `_land_task()` gets a `land-fix` branch.
- `land_verdict()` widens `wanted` on an ask.
- `land_signals()` gets R12 and R13.
- The skill gets:
  - the fourth answer;
  - a Step 3 substep, "a fix the person asked for", after the change's rebase round passes and before Step 4;
  - the rule `Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py land-fix *)`.

**The unreviewed record.**
- `land_unreviewed(root, folder, cfg) -> list[str] | None` is computed once by `cmd_land()` at `stage: test`, and by `land-check`. It is passed to `land_signals()` and `land_message()`.
- `metrics.parse_trailers` needs no change: `unreviewed=2` reads as an int and `unknown` as text.
- Measure in `sdlc.py` reads `tip["landed"].get("unreviewed")` next to `by`, and sets it on the summary's totals, which `metrics.trailers()` writes.

**Edge cases.**
- *A move during a fix round.* `land --close` comes only after the fix round passes, so the move is caught there. The rebase round that follows reviews the change with the fix in it.
- *A second conflict after a move.* `resolve --continue` aborts, which is a stop, as today.
- *No check on the base branch.* `land_verdict()` never asks for a gate, as today.
- *A hand edit after the landing's commit.* If it sits outside the folder and is uncommitted, `_amend_record()` refuses it. A hand commit on the branch is out of scope, because the landing never pushes a branch.
- *A clean rebase that changes a file.* The R13 comparison runs only at `stage: test`, before any landing rebase, so a rebase never reads as a hand edit.

## Contracts touched

- **A writing skill has exactly one WAIT, asked in a dialog with 2–4 answers, and only a chosen yes approves.** The land skill keeps its one `## Step 2 — WAIT`, now with 4 answers. `yes, with a fix` is a `yes, …`. It approves the batch with that fix, and the fix's reviewers decide whether it lands: a kept change or a red gate is a stop. The words come after the yes and are not a second gate. Nothing is written before the yes.
- **What a yes covers (`.sdlc/SDLC.md`: a WAIT's "what it approves" is Tier 2).** The yes now covers following `main` up to `[land] moves` times. Each follow is gated and reviewed at the depth the rebase calls for, and the question says so. In a batch that passed itself, a moved change lands without asking after a clean rebase, as a rebase at Step 3.1 does today. After a conflict, it lands under 097's rule (R16, R15).
- **`[land]` is read from the base branch** (README; `_land()`). `moves` joins `auto` and `batch` there, so a change can't widen its own loop.
- **Narrow `allowed-tools`, plain commands only.** There is one new rule, used verbatim. The loop is prose; the bound is the script's.
- **Never a merge of `main` into the branch, never `--force`.** Every move goes through `sdlc.py base` (a rebase) or `factory.py resolve`. Close stays `--ff-only`.
- **Landing commits only through `sdlc`'s own steps; one amend (097 R5).** The fix commit is the same amend, `_amend_record()` with its new `also` keyword. No new commit path and no second copy exist. The guard that `HEAD` carries `Sdlc-Landed:` applies to the fix too.
- **Only the builder edits; no agent commits.** The fix is the resumed builder's work, the commit is the script's, and the reviewers keep `Read`, `Grep` and `Glob`.
- **The trailer format is a contract: extend, never redefine.** `Sdlc-Landed` gains an optional `unreviewed=`, and `by=` stays its first word. `Sdlc-Totals` gains `unreviewed=` beside `auto=`. File paths go in the commit body, never in a trailer.
- **`factory.py` never imports `sdlc.py`.** `_behind()` is the factory's own code, and close's refusal is never parsed as text.
- **Never `main` in a git call; the scripts run on Windows.** The base comes from `_base()`. Every new `write_text` passes `newline="\n"`. Paths are compared on both sides as git prints them, through 097's `_dirty()`.
- **Measuring never refuses.** A missing or unreadable `unreviewed` leaves the field out.

No invariant in AGENTS.md needs to change.

## Alternatives rejected

- **A second amend for the `moved` path or the fix.** 097 R5 already decided that a landing has one amend. A second copy would bring back 097's bug 31 (the porcelain parse) wherever someone forgot to fix it.
- **A `LAND_MOVES` constant.** The bound decides how long a yes stays good, so a host should set it. Like `auto` and `batch`, it comes from the base branch.
- **Letting `sdlc.py close` rebase.** Close is `--ff-only` by contract, and it would land a change nothing gated as it stands.
- **Rebasing and re-gating inside `land --close`.** The review needs agent sessions that the skill starts.
- **Merging `main` into the branch.** This is forbidden: close would put the merge on `main`'s first-parent line.
- **Asking the person again on every move.** A clean rebase after the yes is already covered today. Asking at every move works against O3.
- **Building the fix at `stage: test`, before the commit.** The land gate keys a build by `HEAD`, and the fix would be written before the yes.
- **Refusing any fix made outside the builder.** Sometimes the person needs a hand fix, so it is recorded (R13, R14) and treated as a signal instead.
- **A trailer of its own, `Sdlc-Unreviewed: paths=…`.** `parse_trailers` splits on whitespace, and trailers hold numbers and names. The fact belongs to the landing that let it through.
- **Clearing the fix signal once its round passes, as 097 R11 does for a resolution.** You chose to keep R12. A fix is new behaviour the person asked for, not a merge of two sides that were each already reviewed. Its signal lasts for the change.

## Verification

```bash
uv run --group dev pytest -q tests/test_land.py                       # the landing, new tests included
uv run --group dev pytest -q tests/test_metrics.py tests/test_skills.py
uv run --group dev pytest -q -m portable                              # what CI's Windows job runs
./check.sh                                                            # ruff, format, the suite, plugin validate
uv run --quiet --script scripts/sdlc.py preflight 104                 # `cases.scope`: the land skill's text changed
```

Healthy output:
- `test_land.py` passes, including every 097 test, unedited. The new tests are:
  - `test_main_moving_before_close_sends_the_landing_back_to_its_rebase`
  - `test_a_move_racing_close_reads_as_moved`
  - `test_a_landing_stops_after_land_moves_moves`
  - `test_the_bound_on_following_main_is_the_base_branchs`
  - `test_a_fix_asked_at_landing_is_built_gated_and_reviewed_at_depth`
  - `test_a_fix_commit_needs_an_ask`
  - `test_a_fix_at_landing_is_never_landed_by_auto_later`
  - `test_a_hand_edit_after_the_approver_is_a_signal_and_recorded`

  Each was seen failing before its code, with the evidence in `build/round-<R>.md`.
- `test_skills.py` passes, with `factory.land.moves` read, the new rule used, and one WAIT with 4 answers.
- `check.sh` ends with `All checks passed!`, a passing pytest count, and `✔ Validation passed` twice.
- `sdlc.py drift` reports nothing, because neither `defaults/` nor `guide/` is touched.
- If `preflight` puts the factory's skill cases in scope, you decide whether to pay for a run.

**Boundaries.**
- *Always:* follow a moved `main` through `base`, gate and review, up to the base branch's `[land] moves`. Review a fix the person asked for at the run's depth. Record what no review read.
- *Asks first:* a change with unreviewed paths, a change fixed at landing, or any other signal, as today.
- *Never:* a merge, a force, a second amend, an agent's commit, paths in a trailer, or a follow past the bound.

