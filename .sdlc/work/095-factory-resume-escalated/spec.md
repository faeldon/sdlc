---
id: 095
slug: factory-resume-escalated
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 095 — An escalated factory run can be sent back for another build · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions, each checked in the code: an escalated change sits at `stage: test` with
`decision.md` opening `DECISION: ESCALATE` (`factory.py` `read_decision()`, `cmd_stage()`);
`factory.py start` writes nothing today (`cmd_start()` only reports); every reader of the
decision reads `decision.md` alone (`read_decision()`, `read_impact()`, `ready()`, `board.py`
`_factory()`, `sdlc.py` `_factory_files()` and `measure_change()`, ship's `factory.md` branch);
the gate's fix limit is per round already (`read_gate()` on `build/round-<N>.gate.md`). Tests
named below go in `tests/test_factory.py` unless another file is named.

1. **R1. `start` takes back an escalated change, read-only.** `factory.py start NNN --for build`
   on a Tier 1 or Tier 2 change at `stage: test` whose `decision.md` opens `DECISION: ESCALATE`
   returns no refusals and a `restart` object: `archive` (`decision-<n>.md`, `n` one past the
   highest `decision-<k>.md` in the folder, from 1), `round` (the round the new build will be:
   one past the higher of the newest review round and the newest builder report), `reconsider`
   (whether the decision has a `## Reconsider the approach` section) and `reasons` (the
   decision's text). `spec` is false. The worktree is byte-for-byte the same afterwards.
   `test_start_takes_back_an_escalated_change` fails if any of these is missing or if a file
   changes.
2. **R2. `start` refuses every other `test` change.** At `stage: test` it refuses: a `READY`
   decision (the refusal names `/sdlc:ship` and `/sdlc-factory:land`), a missing `decision.md`,
   and a `decision.md` that doesn't open with a decision line (the refusal gives
   `read_decision()`'s problem). `--for spec` at `test` is refused as before. The
   `(2, "test", "build", False)` row of `test_start_checks_the_tier_and_stage` stays (no
   decision), and `test_start_refuses_a_ready_or_unreadable_test_change` covers each case.
3. **R3. `factory.py restart NNN [--words R<n>]` does the writes, once the person says yes.** It
   runs the same checks as R1 and R2 (one shared function), then in this order: writes
   `build/round-<R>.restart.md`, renames `decision.md` to `decision-<n>.md`, and sets the
   intent's `stage: build` and `updated:` through `set_stage()`. The archive is byte-identical
   to the old `decision.md`. An existing `decision-<k>.md` is never overwritten: if the target
   exists, `restart` refuses. It writes nothing outside the change's folder and makes no commit.
   Tests: `test_restart_keeps_the_decision_as_history` (bytes equal, `decision.md` gone, stage
   `build`, `id: 008` still `008`), `test_restart_numbers_archives_from_one_and_never_overwrites`
   (a second restart writes `decision-2.md` and leaves `decision-1.md` alone), and
   `test_restart_moves_no_head` (`HEAD` unchanged, `git status` shows only the folder).
4. **R4. A restart that stopped part way finishes on a rerun.** A folder at `stage: test` with
   no `decision.md`, and a restart record for an unbuilt round whose archive exists, is a restart
   under way: `start` accepts it (the `restart` object names that record) and `restart` only
   sets the stage. `test_a_restart_cut_short_finishes_on_rerun` builds that state by hand and
   fails if either command refuses or a second archive appears.
5. **R5. After a restart, `verdicts` names a builder step, not `done`.** Start, then restart,
   then `verdicts`: `next` is `build`, `round` is R, `decision` is null. After the builder's
   report `build/round-<R>.md` and its snapshot, the next step is `gate` for round R, then
   `review` for R, as for any round. `test_restart_then_verdicts_builds_round_r` fails if
   `verdicts` says `done` or `approve`, or if `agent --task build` is refused.
6. **R6. The restart's builder is told the escalation's reasons.** `agent NNN --task build` at a
   restart round sends a prompt that names `<folder>/decision-<n>.md` and includes the decision's
   `## Reconsider the approach` section word for word when it has one (and no such heading when
   it doesn't). With `--words R<n>`, it also includes the person's words from that `decisions.md`
   line. The reply goes to `build/round-<R>.md` (not appended), in a fresh builder session
   (`--session-id`). Tests: `test_the_restart_prompt_carries_the_escalation` and
   `test_the_restart_prompt_carries_the_persons_words`, which read the fake `claude`'s argv.
7. **R7. The round limit counts from the restart.** The restart's round R is the run's first
   round again. `rework` is named while `last.round - R + 1 < rounds`. `exhausted` uses the same
   count, so a restarted run can run out and then escalate again only with a
   `## Reconsider the approach` section. `verdicts`' `limit` is the last round number this run
   may reach (`R - 1 + rounds`), so `runs/step.md` and the board show "round 5 of 6", not
   "5 of 3". `test_the_round_limit_counts_from_the_restart`: escalated at round 3 of 3, restarted,
   round 4 with a kept change → `rework`, not `approve`.
8. **R8. A restart never deepens a light run.** `depth()`'s "an earlier round ran at the full
   depth" counts each round's position within its own run, not its absolute number. A run that
   was light through rounds 1–2 (`light.rounds = 2`) and restarted at round 3 is still `light`.
   A run that was full stays full. Tests:
   `test_a_restarted_light_run_stays_light_and_a_full_one_stays_full`.
9. **R9. The gate's fixes count from the restart.** Round R's gate file is new, so its fix count
   starts at 0 whatever round N's was. `test_a_restart_round_gets_its_own_gate_fixes` gives round
   N two red attempts and checks round R's first red gives `fix`, not `stop`.
10. **R10. A restart record that won't read is a stop.** A `build/round-<R>.restart.md` that
    doesn't open with `RESTART: decision-<n>.md`, that names an archive that doesn't exist, or
    whose `WORDS:` names no `(person, restart)` line in `decisions.md`, gives `next: stop`,
    `way: rerun`, with the problem. `test_a_bad_restart_record_stops_the_run`.
11. **R11. Only the current `decision.md` counts as the run's decision.** After a restart:
    `factory.py ready` leaves the change out (stage `build`, no `decision.md`); `land-check`
    never reads an archive's ESCALATE. On the board, the card is in the Build column, `decision`
    is null and `decision-<n>.md` is among `files`, served by `/file`. After the new run's
    approver writes `decision.md`, `ready`, `land-check`, the board and ship's `factory.md`
    branch read that file alone. Tests: `test_a_restarted_change_is_not_ready` (here) and
    `test_a_restarted_factory_card_is_in_build_with_its_old_decision_as_a_file`
    (`tests/test_board.py`).
12. **R12. The build skill sends an escalated change back behind its one WAIT.**
    `plugins/factory/skills/build/SKILL.md`:
    - Step 0 says `start` accepts an escalated change at `stage: test`.
    - Step 1 shows the decision's reasons, its Reconsider section and the assumed decisions still
      in the ledger.
    - Step 2 asks a third wording of its question, for a restart.
    - Step 3 runs `factory.py restart <NNN>` in place of `stage`, with `--words R<n>` when the
      person answered `yes, <words>`. Before that it writes the line
      `- [x] R<n> (person, restart): <their words>` to `decisions.md`, after the yes.
    - `allowed-tools` gains exactly that command's rule.
    - The `build` step's bullet says it is also the restart's round.
    - It still has one WAIT heading.

    `tests/test_skills.py` (rules match commands, one WAIT, the dialog) fails otherwise.
13. **R13. The docs say it.** AGENTS.md's factory paragraph, `plugins/factory/README.md`'s
    "What it leaves in the change's folder" (`decision-<n>.md`, `build/round-<N>.restart.md`) and
    any `docs/REFERENCE.md` line that says an ESCALATE ends a run. `sdlc.py context` lists nothing
    left unedited at ship.
14. **R14. `./check.sh` passes.**

## Design

**Two commands, split at the WAIT.** `start` stays read-only. It runs in Step 0, before the
person's yes, and it only reports (R1, R2). The writes move to a new `restart` command that
Step 3 runs after the yes (R3). Both call one function, `restart_state(folder, meta)`, which
returns the restart object or a refusal. That way `start`'s answer and `restart`'s check can't
drift apart. `STARTS` itself is unchanged: the escalated case is its own branch in `cmd_start()`,
taken when `purpose == "build"` and `stage == "test"`. A READY change, or any other stage,
falls through to the existing refusal. No other stage is opened.

**The restart record: `build/round-<R>.restart.md`.** `verdicts` decides from the run's files
alone, so it needs a file that marks where the new run starts. The archived decision alone can't
mark it. Once a restarted run is reviewed, "round R reviewed, nothing built since" looks exactly
like "escalated, restart pending". Counting archives doesn't settle which round each one closed.
So `restart` writes, beside the gate files and in the same place they live:

```
RESTART: decision-<n>.md
WORDS: R<k>            (only with --words)
```

It is a run file in `build/`, written by the script like `round-<N>.gate.md`. It is not state
in `runs/`, and `verdicts` never writes it. Every existing glob of `build/round-*.md` already
skips it: `build_round()`, `raised_decisions()`, `board.py`'s `built` and `typical_times()`, and
`sdlc.py`'s `_factory_files()` (which reads `.gate.md` only) each require a numeric stem or the
`.gate.md` suffix, and `round-4.restart` is neither. New constants: `RESTART_RE =
^RESTART: (decision-\d+\.md)\s*$`, `WORDS_RE = ^WORDS: (R\d+)\s*$`, and
`RESTART_WORDS_RE = ^- \[x\] (R\d+) \(person, restart\): (.+?)\s*$`, which shares the `R`
numbering of build's `revise` lines and matches neither `LEDGER_RE` nor `REVISION_RE`, so the
ledger, the board and `sdlc.py` read past it.

**`loop_state()` with a restart.** A new reader, `read_restarts(folder)`, returns each record
as `{round, archive, words}`, oldest first, plus problems (R10). The newest one is `restart`,
and its round, R (1 when there is none), is the run's first round:

- **Decision.** `read_decision()` still reads only `decision.md`, which `restart` moved away, so
  `decision` is null.
- **New branch.** `elif restart and restart["round"] > built: next, round = "build", R` goes
  after `decision` and before `built == 0`. Problems and pending decisions still come first.
- **Limits.** `exhausted` and the `rework` test use `last.round - R + 1` in place of
  `last.round` (R7). `limit` is `R - 1 + run["rounds"]`.
- **State.** `state["restart"]` carries the newest record for `_task()`.
- **Unchanged.** Round R's report is newer than any review round, so `unreviewed` gates it and
  then reviews it with no other change. `reworked()` compares round R's snapshot with round N's,
  so the reviewers are told what the restart changed. `settled()` carries what earlier rounds
  answered across the restart.

**`depth()`** takes the restart rounds (R8). A round's position in its run is `round - start + 1`,
where `start` is the newest restart round at or before it (1 when there is none). "Beyond light"
compares that position with `light.rounds`. The reviewer test stays as it is, so a full run never
lightens.

**`_task("build")`** checks `state["round"] == state["restart"]["round"]` and composes:

> `Change folder: <rel>. Worktree: <root>. The approver escalated this change after round
> <R-1>, and the person sent it back for another build: read <rel>/decision-<n>.md and build
> round <R> to answer it, plan.md first where the approach changes, then the code, test first.`

That is followed, when present, by `The approver's ## Reconsider the approach:` and the section's
lines up to the next `## ` heading, then `The person adds: <words>` from the `R<k>` line. The
target is `build/round-<R>.md`, not appended. `build` is not in `RESUMES`, so the session is fresh.
The plain round-1 prompt is unchanged. The prompt goes to `claude` as one argv item, never through
a shell. In the skill, the person's words never go on a command line: only their id `R<k>` does.

**`restart`'s order and rerun (R3, R4).** The order is record, then rename, then stage. A run cut
short leaves one of three states:

- The record written, `decision.md` still there: a rerun writes the same record again, since R is
  computed the same.
- The rename done, stage still `test`: `restart_state()` sees no `decision.md`, a newest record
  for an unbuilt round and its archive present, and calls it a restart under way. `start` accepts
  it, and `restart` sets only the stage.
- The stage set: `start` takes it like any `stage: build` run.

`n` is one past the highest existing archive. The rename refuses if the target exists, so on
Windows `Path.rename` never meets an existing file, and no archive is replaced. Each write is
`newline="\n"`, UTF-8.

**What doesn't change, and why that's enough:**

- **`ready()`, `land_signals()`, `read_impact()`, `cmd_land()`.** They read `decision.md` only.
  A restarted run has none until its own approver writes one, at `stage: test` again.
- **The board.** It reads `decision.md` only (`_factory()`), so a restarted card has no decision.
  Its stage is `build`, so it goes to the Build column even before 086. 086's stage-gating makes
  that hold even if a stale `decision.md` were left by hand. `decision-<n>.md` shows in the card's
  files, which is the history. No pinned copy changes.
- **`sdlc.py` `_factory_files()`.** Its round count spans the whole folder, restart rounds
  included, which is honest rework. `escalate` reads the final decision (see the open question).
  `measure_change()`'s `way` keys on `decision.md`, which a finished restart has again.
- **Ship's `factory.md` branch.** It still keys on `decision.md`.
- **`carry`.** Lines it added before the escalation stay in `notes.md` as unticked items, and the
  next `carry` adds only new ones. So a restarted change whose first run was exhausted usually
  has undone notes, and `land` leaves it to `/sdlc:ship`, which is the existing rule working.
- **Gate fixes.** They are per round, so round R starts at 0 (R9). `max_runs` is per run, shown
  again at the restart's WAIT.

**The skill.** Step 0: on `start`'s `restart` object, this is a restart. Step 1 shows:

- the decision's first reason, its Reconsider section (or that it has none) and the assumed
  ledger lines, since an unconfirmed default is a common reason to escalate and the person may
  want to answer it first;
- `decision-<n>.md`, the archive name;
- round R;
- the run's shape as today.

Step 2 asks:

> `Send NNN-<slug> back to the factory: decision.md kept as decision-<n>.md, the builder
> rebuilds from round <R> with the approver's reasons, the base branch's gate <command> runs on
> each build before any reviewer (up to 2 fixes a round), <reviewers> review it in up to <rounds>
> more rounds (…light clause…), …ui clause…, a verifier checks each round's changes, the approver
> decides again, at most <max_runs> agent runs, agents in <mode>, all left uncommitted at stage:
> test? (yes / change the reviewers or rounds / no)`

A typed `yes, <words>` is a yes with direction. Step 3 `Write`s or `Edit`s the `R<k>` line, then
runs `factory.py restart <NNN> [--words R<k>]`, then the loop's step 2 as usual. The supervisor
keeps `head` from `start` as for any run.

### Boundaries

- **Always:** keep the old decision byte for byte under a new number; write only the change's own
  uncommitted folder; have a person's yes before any write; give the restarted build to the gate
  and the reviewers like any round.
- **Asks first:** every restart, through build's one WAIT, with the run's cost shown again. A
  second escalation is a second question.
- **Never:** restart a READY change; restart at the spec; delete, edit or overwrite a
  `decision-<k>.md`, a round or a gate file; commit; read an archived decision as the run's
  decision anywhere.

## Contracts touched

- **No agent commits, and `HEAD` stops a run** (AGENTS.md, the factory). `restart` writes only
  the change's own folder and runs no git command that writes. The supervisor keeps `start`'s
  `head`, and `verdicts --head` still stops on a move (R3's test).
- **`verdicts` decides from the rounds alone and never reads a state file.** The restart record
  sits in `build/` with the gate files, which `verdicts` already reads, and only `restart` writes
  it. `runs/stopped.md` and `runs/step.md` are still never read back.
- **A writing skill has exactly one `WAIT` heading, asked in an `AskUserQuestion` dialog; nothing
  is written before it.** The restart reuses build's WAIT with a third wording. `start` stays
  read-only. The `decisions.md` words line and `restart` both come after the yes, so this adds no
  named exception (build's `revise` exception is unchanged).
- **Narrow `allowed-tools`, plain commands, the literal `uv run --quiet --script
  "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py` call.** One new rule, `factory.py restart *`, used
  by one bash block with no branching. The choice between restart and a fresh run is the
  script's `restart` object, not a shell `if`.
- **Frontmatter is edited in place, never round-tripped.** `restart` calls the existing
  `set_stage()`.
- **The scripts run on Windows.** `encoding="utf-8"` and `newline="\n"` on every write. No
  rename onto an existing file. Paths shown with `as_posix()`. No top-level platform import.
- **The board writes nothing, and its and `sdlc.py`'s copies of the factory's parsing stay pinned
  by tests.** No copy changes: neither reads the restart record or the archives as a decision,
  and the existing pin tests still hold.
- **The metrics trailer is extend-only.** Nothing is redefined. The `escalate` question below is
  left as an extension or nothing.
- **Nothing local.** Test data uses the existing neutral `008-reopen-drafts` fixture.
- **Context docs are checked at ship.** AGENTS.md, `plugins/factory/README.md` and
  `docs/REFERENCE.md` are edited in the change (R13).

No invariant needs to change.

## Alternatives rejected

- **Do the archive in `start`.** `start` runs in Step 0, before the WAIT, so a write there is a
  write before the person's yes. `start` would also stop being safe to run just to look.
- **Overload `stage <NNN> build` to archive the decision when moving from `test`.** A stage move
  that silently renames files hides a write, and `stage` is also the hand-back's command.
- **Find where the new run starts from the archives alone, with no record.** After the restarted
  round is reviewed, "reviewed, nothing built since" can't be told apart from "restart pending".
  The archive count doesn't say which round each archive closed. Putting the round in the
  archive's name, or a header in it, would break the intent's `decision-<n>.md` from 1 and its
  "never rewritten".
- **A `runs/attempt-2/` subfolder, or `decision.md` moved into the round's folder.** Every
  reader, `sdlc.py`'s pinned copies, the board and measure, globs `reviews/round-<N>/` and
  `build/round-<N>.md` at a fixed depth. A subfolder would hide the first run's rounds from them
  or need every copy changed. A `decision.md` under `reviews/round-<N>/` would be read as a
  review by the board and by `raised_decisions()`. Round numbers carrying on (4, 5, …) keep every
  reader right with no change.
- **Delete or reset the old rounds.** This loses the history the intent keeps, and the counts
  measure takes from it.
- **Give the reasons as fake `KEPT:` lines in a `verified.md`.** `read_verified()` requires each
  answer to name a reviewer's `CHANGE:` exactly once. A forged one is a stop, and it would put
  the approver's words in the verifier's mouth.
- **Resume the old builder session.** It may be long, after several rounds and fixes, and is
  anchored on the approach the approver asked to reconsider. A fresh session reads `plan.md`,
  the diff and the decision. The cost is re-reading the code once.
- **Count the round limit across the whole folder.** A run escalated at round 3 of 3 would be
  `exhausted` at its first review after the restart and go straight back to the approver. That
  is one rebuild with no rework, which isn't "another build".
- **Restart a Tier 2 at its spec.** The spec-writer would redraft over the approved `spec.md`
  and need the `plan`→`design` route, which this change doesn't touch. A person who wants a new
  spec edits `spec.md` before saying yes, or drops the change.

## Verification

```bash
uv run --group dev pytest -q tests/test_factory.py -k "restart or start_" -n auto
uv run --group dev pytest -q tests/test_board.py -k restarted
uv run --group dev pytest -q tests/test_skills.py -n auto
./check.sh
```

Healthy output:

- Every R-named test above passes, along with the existing `test_start_checks_the_tier_and_stage`,
  `test_stage_edits_only_the_two_lines`, the board's pin tests (`DECISION_RE` and the rest, in
  `tests/test_board.py` and `tests/test_metrics.py`) and `tests/test_windows.py`.
- `./check.sh` ends with ruff clean, the formatter clean, pytest all passed and
  `claude plugin validate --strict` passing for both plugins.

By hand, in a scratch change: `factory.py start NNN --for build` on an escalated change prints a
`restart` object and leaves `git status` unchanged. `factory.py restart NNN` then leaves
`decision-1.md`, `build/round-<R>.restart.md` and `stage: build`. `factory.py verdicts NNN` then
says `"next": "build", "round": R`.
