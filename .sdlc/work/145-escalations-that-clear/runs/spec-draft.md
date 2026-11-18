---
id: 145
slug: escalations-that-clear
kind: spec
created: 2026-11-18
updated: 2026-11-18
---

# 145 — An escalation the person has dealt with clears without a rebuild · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Four parts: escalations that clear (R1–R14), columns that name the state of the work (R15–R18), a landing's progress (R19–R24), and three seeds the person asked to fold in (R25–R27).

**Escalations that clear**

- **R1.** `agents/approver.md` tells the approver to give every reason it escalates for as a line of its own, with a kind. Open ledger lines keep today's form: an unticked blocking line by its id, and `- ESCALATED: D<n>: <why>` for a default. Every other reason is `- ESCALATED: gate: <why>`, for something a green `[commands] check` on the change would show is fixed (a red gate, or a failing test or lint the check runs), or `- ESCALATED: look: <why>`, for anything else the person must look at. A test in `tests/test_skills.py` (beside 137's `- SETTLED:` one) fails if approver.md names either form, or the rule that every reason has a line, no longer.
- **R2.** `factory.py`'s new `escalation_reasons(folder)` reads only the current `decision.md`, never a `decision-<n>.md`. It returns each `gate` and `look` line in order as `{"kind", "text"}`. A `- ESCALATED: <word>: …` line whose word is neither `D<n>`, `gate` nor `look` reads as a `look`, so it still needs the person. `ESCALATED_RE` (the `D<n>` form) never matches a `gate:` or `look:` line, so `approver_weighing()` reads what it reads today. A test with a decision holding all three forms, and an archived decision holding others, pins this.
- **R3.** `factory.py decisions` files each current `look` reason once in `decisions.md`, as `- [ ] D<n> (approver round <R>, look): <why>`, where `<R>` is `newest_round()` when it files it. A rerun writes nothing. After a restart, the new decision's reasons are filed as new lines, even when a reason's text matches an older line's. Tests: one for a rerun, one for a restart.
- **R4.** The ledger pattern accepts the new kind, `(blocking|default|look)`, in all three copies: `factory.py`'s `LEDGER_RE`, `board.py`'s `LEDGER_RE` and `sdlc.py`'s `FACTORY_LEDGER_RE`. The existing pinning tests (`test_sdlcs_copies_of_the_factorys_patterns_match_its_own`, and the board's copy test) still pass. A `look` line is never `pending` (blocking), never `assumed` (default), never `GARBLED_LEDGER`, and is counted in none of `_factory_files()`'s `blocking`, `defaults`, `defaults_open` or `defaults_settled`. A test with a ledger holding one line of each kind asserts every count.
- **R5.** Only the person ticks a `look` line. The changes needed:
  - `_settle_refusal()` refuses one (`D<n> is the person's to acknowledge`), so an approver's `- SETTLED:` naming it lands in `unsettled`.
  - A landing's yes never ticks one, where it confirms assumed defaults.
  - `upgrade_answer()` never reads one.

  A test makes each of the three attempts and finds the line still unticked.
- **R6.** A `look` line is *current* only when its source round is the change's newest round and the current `decision.md` holds a `look` reason with its exact text. A line that isn't current is history: it isn't in `ask`'s items, isn't one of `needs_of()`'s needs, and isn't in `land-check`'s signals. A test restarts a change holding an open `look` line and finds it in none of the three.
- **R7.** `sdlc.py gate NNN` gates a factory run at `stage: test`, and only there: at `design` or `build` it still refuses, naming `factory.py gate`. It writes the same `build/gate.md` record as for a hand change. That file is never counted in `_factory_files()`'s `gate_fail`, nor in the board's `history_samples()` gate times. Tests: a factory run at `test` gates; one at `build` is refused; a closed change carrying `build/gate.md` keeps its `gate_fail` and `land-gate` samples unchanged.
- **R8.** A `gate` reason is cleared only while the hand gate's last attempt is `PASS` and `current` (`hand_gate()`'s rule: `hand_build()` matches). A later edit to a path the change touches makes it stale. This is the intent's own test: escalate a change for a red gate, fix its tree, record a green `sdlc.py gate`, and find the change in Ready and gone from `■ What needs me`. Then edit a touched path and find it back in Needs you.
- **R9.** For an ESCALATE at `test`, `needs_of()` gives:
  - `decide D<n>` for each pending blocking line, and `confirm N defaults`, as today;
  - `reconsider the approach`, as today;
  - `acknowledge D<n>` for each current, unticked `look` line;
  - `gate it green` once, while any `gate` reason isn't cleared;
  - `read the escalation`, only when the decision holds no `gate` or `look` reason and the ledger holds no blocking or default line (today's rule, so an old decision reads as before).

  An escalation that needs nothing is `answered()`. On the board it goes to Ready, badged `escalated: answered`, and in `status` it leaves `■ What needs me`. A table-driven test in `tests/test_sdlc.py` covers each case. Its fields come from `factory_reading()`, which now also gives `reasons` (each with its kind, text and whether it is cleared), and from the record's `gate`.
- **R10.** `decision.md` is never written. A test runs `ask`, `decisions`, `sdlc.py gate`, `land-check` and the board's state on an escalated change and finds the file's bytes unchanged.
- **R11.** `factory.py ask` lists each current open `look` line among its `items` (`kind: look`, `reply: decision.md`, the reason as its `question`, no options). It also prints `gate`: each `gate` reason, whether it is cleared, and the record's path. With `--answered`:
  - a `look` answer never makes `next` `rebuild`;
  - once nothing is open but an uncleared `gate` reason, `next` is `gate`, and `then` is `sdlc.py gate NNN`;
  - otherwise `next` follows today's rules.

  A test in `tests/test_factory.py` covers each.
- **R12.** `/sdlc-factory:decide` asks each `look` item in a dialog of its own. Its answers are `seen` and `checked something`, which asks for the person's words as text. Step 3 records `→ decided: seen`, or the words they gave. The skill tells the person about each uncleared `gate` reason and runs nothing for it. Its `allowed-tools` and its one WAIT are unchanged, so `tests/test_skills.py`'s invariants still hold.
- **R13.** `land-check` keeps the signal `the approver escalated` for every ESCALATE, cleared or not, so `clear` is false and no gate passes itself on a cleared escalation. Its `shown` text adds an `Escalated` block for each such change, one line per reason:
  - `D2: decided: <answer>`;
  - `D7: acknowledged: <words>`;
  - `gate: green on the build as it stands (attempt 3)`;
  - `not cleared`, when it isn't.

  A test reads `land-check` on a cleared escalation and finds `clear: false` and each line.
- **R14.** Measuring still reads the approver's call. A cleared escalation's `Close` commit carries the decision `ESCALATE` exactly as an uncleared one's does, because `_factory_files()` reads `decision.md`, which no one rewrote. A test pins this.

**Columns that name the state of the work**

- **R15.** `board.py`'s `column()` returns one of `planned`, `designing`, `building`, `ready`, `landing` or `needs-you`, checked in this order:
  1. `needs-you` for a problem or a need, as today.
  2. `landing` for a shipped or dropped change still waiting on close, or a factory landing in flight (a `runs/land-step.md` that isn't a stop) at `test` or `shipped`.
  3. `ready` for a factory change at `test` whose decision is READY or `answered()`, or a change built by hand that R16 calls ready.
  4. Otherwise by `seen` or `stage`: `plan` is `planned`, `design` is `designing`, and `build` is `building`. A factory change at `test` with no decision (a restart cut short) is also `building`.

  A parametrized test in `tests/test_board.py` places a hand change and a factory change at each of planned, designing, building, ready and landing, and finds each pair in the same column.
- **R16.** A change built by hand is Ready once ship's review has written `findings.md`, or its hand gate is current and green, and never while its hand gate is current and red. This is today's Test rule, now under a new name, plus the red-gate exclusion. A test covers all three cases.
- **R17.** `board.html`'s `COLUMNS` reads Planned, Designing, Building, Ready, Landing and Needs you, keyed as R15. Every card's `next:` line still names its own tool's command (`next_action()` is unchanged but for R9's new needs and R25). `PRECEDENCE` and `BOTH` in `tests/test_board.py` gain the pairs for `acknowledge`, `gate it green` and R25's landing conflict.
- **R18.** `docs/REFERENCE.md`'s three places that name the columns (status's `■ What needs me`, *The board*, and the hand gate's paragraph) name the new columns and the new needs. The hand gate's paragraph says it now gates a factory run at `test`.

**A landing's progress**

- **R19.** `_record_land()` adds a line to `runs/land-times.jsonl` for the step it replaces, `{"step", "round", "seconds"}`, when the step changes. The time runs from that step's `SINCE:` to now. It writes nothing when the step and round hold. A landing's record files are amended into the change's commit, and this one goes in with them. Its writes are UTF-8, with `newline="\n"`. A test runs three steps and reads two lines.
- **R20.** `history_samples()` reads `runs/land-times.jsonl` from each closed factory change's folder at the `Close` commit's parent. Those are `land-<step>` samples for `ship`, `rebase`, `stack`, `checks`, `recheck` (R26) and `close`. The existing `land-gate`, `land-review` and `land-verify` keep their sources. A step's typical time needs `MIN_CHANGES` changes, as a build step's does. A test builds three closed changes with the file and finds `land-ship/2` in `typical_times()`.
- **R21.** The open-ended steps are `resolve`, `fix`, `mend`, `cases` and `wait`. On a card, an open-ended step, or a step history has no time for, shows its elapsed time and `running`. It never shows a `fraction` or `typical`. A test gives the board history for every step and finds no fraction on any open-ended step.
- **R22.** A change in a train that is waiting for another change gets the step `wait` in its record, with `WAITS: stack on <change>` or `WAITS: close after <change>`, naming the live change before it (`train_live()`). The record is rewritten each time the train turns to another change. On the card it reads `waiting to stack on 140`, never the last step it finished. `wait` joins `LAND_STEPS` and `board.py`'s `LAND_AT` (at the rebase position, labelled `waiting`), so the existing pin tests hold.
- **R23.** The intent's test: the board gets a train of three, one stacking and two waiting. It finds each card's step (`stacking`, `waiting`, `waiting`), place (`1 of 3`, `2 of 3`, `3 of 3`) and wait (`waiting to stack on <first>`, `waiting to stack on <second>`).
- **R24.** `factory.py`'s and `board.py`'s readers of the new record lines (`WAITS:`, and the land-times row) are copies, pinned by a test over a shared table of cases, as `read_land_step()`'s are.

**Seeds folded in**

- **R25.** Seed 2026-11-18-49 (*Board says "builder is resolving a conflict" on a factory landing mid-rebase*).
  - **Today:** a card whose worktree is stopped mid-rebase while a factory landing's record names `resolve` (not a stop) gets the hand-run `sdlc.py resolve … --continue / --abort` line as its next step, because `next_action()` checks `rebasing` first.
  - **Change:** such a card's next step reads `its builder is resolving a conflict: wait for it, or /sdlc-factory:land NNN if its session ended`. The card sits in Landing (R15) with its `rebasing` badge. A rebase stopped with no landing record, or with a landing record that is a `stop` or `eject`, keeps today's `sdlc.py resolve` line.
  - **Tests:** `PRECEDENCE` and `BOTH` in `tests/test_board.py` gain the `rebasing` + landing-`resolve` pair. A test finds the new line on one card and the old line on a hand-run rebase.
- **R26.** Seed 2026-11-18-50 (*Landing track shows post-rebase `accept` as its own step after the gate*).
  - **Today:** `factory.py accept`, run after the landing's commit (inside a landing round, after a rebase), records no step, so the track stays at `gate`.
  - **Change:** after the commit, `accept` records the new landing step `recheck`. It joins `LAND_STEPS`. `LAND_TRACK` gains a position `checks` between `gate` and `review`, where `recheck` sits, labelled `checks`. Before the commit, `accept` still records `checks` at the ship position, as today.
  - **Tests:** a test runs `accept` after a landing's commit and finds `STEP: recheck` in `runs/land-step.md` and the card's track `ship, rebase, gate, checks (current), review, verify, close`. `test_land.py`'s assertion that a post-commit accept leaves the record unchanged (`the gate's step`) is rewritten to assert `recheck`. The `LAND_AT` and `LAND_STEPS` pins hold.
- **R27.** Seed 2026-11-18-47 (*Reword `_no_verdict()` and `NO_DECISION` now that an answer after prose is read*).
  - **Today:** `opening()` reads an answer after prose (140), but four messages still say a reply "doesn't open with" its answer.
  - **Change:** each says what it now means, that the reply holds no answer the script reads:
    - `_no_verdict()`: `reviews/<kind>-<n>/<role>.md holds no VERDICT: PASS or VERDICT: CHANGES the script reads (first, or the only answer it gives)`;
    - `NO_DECISION`: `decision.md holds no DECISION: READY or DECISION: ESCALATE the script reads (first, or the only answer it gives)`;
    - the landing review's problem at `factory.py` line 6292 says it in the same words;
    - `board.py`'s copies in `_factory()` (lines 370 and 396) are its plain card text for the same two facts.
  - **Tests:** a test pins each board copy's text to the factory's constant or function. The tests that assert the old words (`test_factory.py` around lines 3049 and 4138, `test_train.py` line 881, `test_board.py` line 525) assert the new ones. `sdlc.py` and `status` have no copy of this text, so nothing else moves.

## Design

**Assumptions checked in the code.**

- Nothing in the code today tells one kind of escalation reason from another. The approver's only machine-read lines are `DECISION:`, `- SETTLED:`, `- ESCALATED: D<n>:`, `- IMPACT:`, `- UNDONE:` and `- RECOVER:`. Its other reasons are prose (`approver.md`, *What you return*).
- `needs_of()` stands in for "dealt with" by looking at the ledger: an ESCALATE whose every ledger line is ticked is `answered()`, whatever its prose said, and one with no ledger line reads `read the escalation`. That second rule is why 140 stayed in Needs you (`sdlc.py` `needs_of()`).
- `cmd_gate()` refuses a folder holding `runs/`. Its `Build:` hash (`hand_build()`) leaves out the change folders, so writing the record, or the factory's own `runs/` files, never makes it stale.
- `_amend_record()` adds everything under the change folder to the landing's commit. That is why the `Close` commit's parent holds `build/land-*.gate.md` and `runs/costs.jsonl`, which `history_samples()` already reads.
- `runs/land-step.md` holds only the current step. Past landing steps leave no times, which is why `typical` is empty.
- `cmd_accept()` records `checks` only `_before_commit()`.
- `next_action()` returns the `rebasing` line before it reads `progress`.
- `opening()` takes a reply's first line, or the one answer all its answer lines agree on.
- `land_signals()` adds `the approver escalated` for any ESCALATE.
- `ready()` takes an ESCALATE as readily as a READY.
- `_factory_files()` reads the decision from `decision.md`.

**Reasons and how each clears.** There are three kinds. Each is read from a file that already exists, and each is cleared by a record beside the decision, never in it:

| Kind | Where the reason is | What clears it | Where that is recorded |
|---|---|---|---|
| decision / default | ledger line (today) | the person's answer in `decide` | `decisions.md`, `→ decided:` |
| `look` | `- ESCALATED: look:` in `decision.md`, filed as a ledger line of kind `look` | the person's acknowledgement in `decide` | `decisions.md`, `→ decided: seen` or their words |
| `gate` | `- ESCALATED: gate:` in `decision.md` | a current green hand gate | `build/gate.md`, `sdlc.py gate`'s record |

`Reconsider the approach` is not a fourth clearable kind. It still needs a rebuild, or a hand ship. The intent asks for no change there.

**Where each piece lives.**

- **`factory.py`:**
  - `escalation_reasons()` (R2), and the filing in `cmd_decisions()` (R3), matched on (source round, text).
  - `read_ledger()` gives a `look` line `open` only while it is current (R6), reading the current `decision.md`'s reasons and `newest_round()`.
  - `cmd_ask()` (R11).
  - `land_parts()` gains `escalations`, which `land_shown()` prints (R13).
  - Whether a `gate` reason is cleared comes from a copy of `sdlc.py`'s `hand_gate()` currency rule (`_hand_paths()`, `_hand_digests()`, `_hand_hash()`) and `read_gate_file()`. The copy is pinned by a test that runs both on one tree, the way `tests/test_hand_gate.py` pins the record's shape.
  - `_record_land()` writes the times row (R19).
  - The train writes `wait` records (R22). They come from `train_live()` and the change the train is acting on, in `_train_reading()` and the close loop.
  - `cmd_accept()` records `recheck` after the commit (R26).
  - `_no_verdict()`, `NO_DECISION` and the landing review's problem are reworded (R27).
- **`sdlc.py`:**
  - `factory_reading()` gains `reasons` and `looks`. The look lines are split out of `pending` and `assumed`, and only current ones count. It needs `FACTORY_` copies of the new regexes and of `newest_round()`, all pinned.
  - `needs_of()` (R9) clears a `gate` reason from `rec["gate"]`.
  - `cmd_status` now reads `hand_gate()` for a factory run at `test` too, so `needs_of()` has the gate record.
  - `cmd_gate()` allows `stage: test` (R7).
  - `decide_step()` also names `/sdlc-factory:decide` for `acknowledge` needs.
- **`board.py`:**
  - `_entry()` reads `hand_gate()` for a factory run at `test`.
  - `_factory()` splits out look lines and words its problems as R27 says.
  - `column()` (R15–R16).
  - `next_action()` names `sdlc.py gate NNN` for `gate it green`, `/sdlc-factory:decide NNN for D7` for `acknowledge`, and R25's landing line before the `rebasing` one when the landing's step is `resolve`.
  - `LAND_TRACK` and `LAND_AT` gain the `checks` position and `recheck` (R26), and `wait` (R22).
  - `_land_progress()` handles `wait` and the open-ended steps (R21–R22).
  - `history_samples()` and `step_samples()` read the times file (R20).
- **`board.html`:** `COLUMNS`, the seventh track position, and the `waiting to …` label.
- **The approver and decide:** `agents/approver.md` (R1), and `skills/decide/SKILL.md` (R12).

**Edge cases.**

- A `look` reason with no ledger line yet. This happens only if `decisions` never ran after the approver; the build loop runs it after every step. The reason is not cleared, and it reads `read the escalation`.
- Several `gate` reasons are all cleared by the same green gate.
- A gate record that won't read clears nothing: `hand_gate()` gives `current: false` with a problem.
- A hand fix after the approver also raises `land-check`'s existing `changed since its last review` signal. That is right: the person sees both.
- A landing whose record says `resolve` while no rebase is stopped (the builder finished, and the next step hasn't recorded yet) shows the landing line it shows today.
- A `recheck` with no history shows elapsed time and `running` (R21's rule for any untimed step).

### Boundaries

- **Always:** the approver's decision stays exactly as written; clearing never lands anything; the landing question shows how each reason was cleared.
- **Asks first:** nothing new. `decide` keeps its one WAIT, and `sdlc.py gate` stays the person's own command, never pre-approved.
- **Never:**
  - an agent ticks a `look` line;
  - a gate clears a `look` reason, or an acknowledgement clears a `gate` reason;
  - `decision.md` is rewritten or stamped;
  - a `fraction` is made up for a step without history;
  - `status` is regrouped (left to the person, below).

## Contracts touched

- **The board writes nothing** (AGENTS.md, *The board*). It only reads the new `runs/land-times.jsonl`, `WAITS:` lines, `recheck` records and `build/gate.md`. Every node is still built with `textContent`.
- **The hand gate is for a change built by hand.** AGENTS.md's *The board* paragraph says this, as do REFERENCE.md's *The gate, run by hand* and `cmd_gate()`'s docstring. **This changes**: the hand gate now also gates a factory run at `stage: test`, and only there, where the factory's own gate has stopped. That is the intent's own mechanism (`a green sdlc.py gate NNN`). The design stays narrow:
  - a factory run at `build` or `design` is still refused;
  - the record is a file the factory never writes (`build/gate.md`, not `round-<N>.gate.md`), so neither `verdicts` nor `gate_fail` nor the gate history reads it.

  The AGENTS.md map and REFERENCE.md are edited in this change to say so. This is a policy edit for the person to approve with the spec.
- **`factory.py` never imports `sdlc.py`; `sdlc` never runs `factory.py`; each reads the other's files with pinned copies.** Kept. The factory reads `build/gate.md` with a copy of its parsing and of `hand_build()`. `sdlc.py` and the board read `look` lines, `- ESCALATED: gate|look:` lines, `newest_round()`, the new landing steps and R27's problem texts with copies. Each copy is pinned by a test.
- **Only the current `decision.md` is ever a run's decision.** Reasons are read from it alone, and R6 makes a filed `look` line history once a restart archives its decision.
- **`verdicts` decides from the rounds alone.** Untouched: it reads none of the new files. R27 changes only the words of the problems it already reports, not when it reports them, so the one mend a run makes for an unreadable reply is triggered exactly as before.
- **Agents that judge have no Write.** The approver's tools stay `Read, Grep, Glob`. It still only returns text, which `factory.py` files.
- **Writing skills: one WAIT, asked in a dialog, narrow `allowed-tools`.** `decide` gains no command and no write before its WAIT. Its new `look` dialogs collect answers only.
- **Metrics: extend, never redefine.** No trailer is added or changed. A `look` line is in no existing count (R4), and the decision trailer still reads the approver's call (R14).
- **The scripts run on Windows.** The times file is appended with `encoding="utf-8", newline="\n"`. No new subprocess.
- **The ledger is the one place a person answers** (`cmd_decisions()`'s docstring). Kept: an acknowledgement is a ledger answer.

## Alternatives rejected

- **Rewriting or stamping `decision.md` as cleared.** The Constraints forbid it, and measuring and the landing must still tell the approver's call from the person's.
- **Filing `look` items as `blocking` ledger lines.** Simpler regexes, but wrong in three ways:
  - they would count in `Sdlc-*` blocking figures, redefining a metric;
  - an answer that isn't `KEPT_ANSWER` would send `ask` to `rebuild`;
  - `upgrade_answer()` and the supervisor's in-run asking would read them.
- **A separate acknowledgements file.** The intent asks for the ledger, and a second place the person answers would need a second reader in all three copies.
- **Clearing a red gate with `factory.py gate`.** Its record belongs to a round. It would count in `gate_fail` and the gate-time history as a round the factory ran, and the factory, not the person, would have run it.
- **Asking `sdlc.py preflight` for the hand gate's state from `ask` and `land-check`.** That avoids a copy, but costs a subprocess on every `ask`. A pinned copy is how the two plugins already share every other reading.
- **Counting the change folder in the hand gate's `Build:` hash**, so an edit to a behaviour record makes the gate stale. A factory folder changes on every step (`runs/`), so no record would ever be current. The known gap: a later edit inside the folder that breaks a repo-wide test (as 140's record did) doesn't make the record stale. The landing's own gate still runs the check.
- **Matching a `look` line to its reason by text alone.** After a rebuild, an identically worded reason would read as already acknowledged against a different build. That is why the source carries the round (R3, R6).
- **Taking landing step times from `runs/land-step.md` in history.** It holds only the last step, so every earlier step's time is gone.
- **A percentage for an open-ended step.** A conflict resolution or a paid case run has no typical length, and a bar would be a guess dressed as a measure.
- **Recording a post-commit `accept` as `checks` with an `AFTER: gate` line** (R26). `LAND_AT` places a step by its name alone, and the same name in two positions would need every reader (board, pins, the times history) to look at a second field. A step of its own keeps one name, one position.
- **Leaving R27's old wording on the board while the factory changes.** The card and the factory's refusal would then say two things about one file.

## Verification

```bash
uv run --group dev pytest -q -n auto tests/test_factory.py tests/test_land.py tests/test_train.py
uv run --group dev pytest -q -n auto tests/test_board.py tests/test_sdlc.py tests/test_hand_gate.py tests/test_metrics.py tests/test_skills.py tests/test_evals.py
./check.sh
```

What healthy output looks like:

- Every test passes, the new ones included: the R8 green-gate test, the R9 needs table, the R10 unchanged-bytes test, the R15 hand-and-factory column pairs, the R20 history test, the R23 train-of-three test, R25's landing-conflict pair, R26's `recheck` track and R27's pinned wording.
- `./check.sh` ends with ruff, ruff format, pytest and `claude plugin validate --strict` all green.
- The pattern-copy tests (`test_sdlcs_copies_of_the_factorys_patterns_match_its_own`, the board's copy and `LAND_STEPS` pins, the new `hand_build` and `newest_round` pins) all pass.

By hand, on a scratch factory change at `test` with `- ESCALATED: gate: …` and `- ESCALATED: look: …`:

1. `sdlc.py status` lists it under `■ What needs me` with `acknowledge D<n>` and `gate it green`.
2. After `/sdlc-factory:decide` and a green `sdlc.py gate NNN`, it is gone from that list and on the board under Ready.
3. `factory.py land-check NNN` shows `clear: false` and the `Escalated` block.
4. `git diff` shows `decision.md` untouched.

