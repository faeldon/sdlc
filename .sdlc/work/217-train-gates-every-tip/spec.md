---
id: 217
slug: train-gates-every-tip
kind: spec
created: 2026-11-21
updated: 2026-11-21
---

# 217 — Gate every landing train's tip, a train of one included · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions checked in the code. `_train_gate()` (`plugins/factory/scripts/landing.py`) is the only place that skips the tip's gate: its `m == 1 and stacked == pre` early return. `cmd_gate(..., land=True)` already gates a train's change that opened no landing round, and writes its record where round 1's would go (`build/land-1.gate.md`, the `n == 0 and landing.train_names(...)` branch in `factory.py`). `_read_gates()` reads `land_round(folder) or 1` the same way. `train --run` already takes a `gate` step for any change. `_put_back()` already handles ejecting a change whose head is still its pre-train commit: no undo, and its records are amended in by `_train_eject()`. So the fix changes the decision, not the machinery.

1. **R1. A train of one is gated at its tip.** When the base branch's `.sdlc/config.toml` names a `[commands] check`, a one-change train whose stacked commit equals its pre-train commit reads `next: gate` for that change (`prefix: 1, of: 1`) before it ever reads `close`. Two cases: the change was never touched since its build, or it was rebased onto a base that moved before `--begin` (as `factory.py fresh` does). `test_a_train_of_one_is_gated_at_its_tip`, parametrized over both cases, fails today because the reading is `close`.
2. **R2. The escape is reproduced, and a red tip ejects.** The base's check is `! git ls-files | grep -qx forbidden.txt`. A ready change adds an untracked `forbidden.txt`, and its build round's gate passes on the uncommitted tree. `train --run` then:
   - ejects the change with `cause: gate`, its reason naming `build/land-1.gate.md` and `exit 1`;
   - leaves the base branch's tip where it was, with no `Close` commit;
   - leaves the change's branch at its landing commit, with `build/land-1.gate.md` (`GATE: FAIL`) and a `runs/ejections.jsonl` row `cause: gate` amended in, its worktree clean and `undo` null.
   
   `test_a_train_of_one_whose_commit_fails_the_check_is_ejected` fails today: the train closes the change and the base goes red.
3. **R3. A green train of one lands with its gate on record.** On a base whose check passes, a one-change `train --run` ends `done: true` with `gates: 1`. The change's own commit on the base branch holds `build/land-1.gate.md`, starting `GATE: PASS`, and `runs/land-train.md` with a `TIP GATE: PASS` line. `test_a_green_train_of_one_records_its_tip_gate` fails today because there is no gate file and `gates` is 0.
4. **R4. The records ledger covers a train of one.** A `build/land-1.gate.md` written by hand on a one-change train's commit stops `train --run`, naming the file, and closes nothing. Today `_train_gate()` returns before `_read_gates()` ever looks. A one-change case is added to `test_train_run_stops_on_a_hand_written_record`, and it fails today.
5. **R5. Longer trains are unchanged.** One gate at the tip, a red tip bisected by prefix, the change at fault ejected, and the "first change at fault twice in a row" stop all behave as before. The existing multi-change tests in `tests/test_train.py` and `tests/test_land.py` pass with their assertions unchanged. Only tests that relied on a one-change train skipping its gate (a reading of `close` straight after `land`, or `gates: 0` on a base with a check) are updated to expect the gate.
6. **R6. A landing with no gate says so, and why.**
   - `train`'s reading and `train --run`'s exit JSON carry `ungated`. It is null when the base branch names a `[commands] check`. Otherwise it is the string `<base>'s .sdlc/config.toml names no [commands] check`.
   - So `done: true` beside `gates: 0` and a non-empty `landed` happens only with `ungated` set.
   - `test_a_landing_with_no_check_says_it_ran_no_gate` covers a one-change train on a base with no check: `done: true`, `gates: 0`, and `ungated` naming the reason.
   - R3's test asserts `ungated` is null.
7. **R7. The question tells the truth on a base with no check.**
   - `land_question()` takes `gated: bool = True`. With `gated=False`, the clause `gated once at the tip (a red tip bisected, the change at fault left out with why and the rest landed; a conflict resolved by one landing agent and reviewed again)` becomes `not gated, since <base> names no [commands] check (a conflict resolved by one landing agent and reviewed again)`.
   - `cmd_land_check()` passes `gated=factory._base_check(root, base) is not None`. That reads the base branch's config, never the checkout's, and is False when no base resolves.
   - With a check, the wording is byte for byte what it is today, so the strings pinned in `tests/test_land.py` and `tests/test_train.py` stand. A new case in `tests/test_land.py`'s question test asserts the ungated wording, and that `land-check` on a base with no check returns it.
8. **R8. The land skill reports it.** In `plugins/factory/skills/land/SKILL.md`:
   - Step 3's list of the loop's JSON keys names `ungated`.
   - Step 4 says to report `ungated`, in the script's words, whenever it is set, beside how many times the tip was gated.
   
   A test in `tests/test_skills.py` fails if Step 4's text doesn't name `ungated`.
9. **R9. No claim is left that the change made false.**
   - The comment in `cmd_land()` ("a train of one that never moved lands on its round's gate alone") is updated.
   - So is the comment in `factory.py`'s `cmd_gate()` about a change that "opened no round". It now covers the tip of a train of one too, not only a bisected prefix.
   - `docs/REFERENCE.md`'s `gate_fail` sentence ("on a change a landing rebased") becomes one that covers every change a landing gates.
   
   Checked by the grep in Verification and by the review's doc pass. No test, since a comment's wording can't be checked by one.

## Design

**The decision.** Delete the two lines in `_train_gate()` that return None for `m == 1 and tip.stacked == tip.pre`. Nothing else in the function changes. With one live change, the first reading finds no recorded gate on its stacked commit and returns `{"next": "gate", "change": live[0], "prefix": 1, "of": 1}`. A PASS on that commit makes `green == m` and returns None, and the train goes on to `_train_build()`, the review step and `close` as today. A FAIL gives `red == 1 == green + 1`, which ejects the change with the gate's exit and file. The "twice in a row" stop can't fire for a train of one: after the ejection no change is live, and the next reading is `done`.

**Where the gate runs and what it records.** These are the existing paths, unchanged:
- `train --run` takes `gate` through `factory.py gate <NNN> --land`. That is `_run_check()` with the base branch's `[commands] check` (`_base_check(root, base)`), in a `gate_jobs` slot, vouched in the records ledger before it writes.
- A change that never moved opened no landing round when `rounds_before` is 0, so `cmd_gate` writes `build/land-1.gate.md`.
- If an earlier train left rounds, `_fresh_round()` has already opened `land-<k+1>`, and the gate goes there. `_read_gates()` reads the same path by the same `land_round(folder) or 1` rule, so the train's state holds the attempt under the change's stacked commit.
- `close` amends the record in, as it does for every train, and `train_record()` writes its `TIP GATE:` line from `_train_took_part()`.

**Ejecting a change that never moved.** `_put_back()` sees `head == pre` and returns `(None, None)`: nothing to reset, so `undo` is null. `_train_eject()` then records the `eject` step, the `runs/ejections.jsonl` row (`cause: gate`) and `runs/land-train.md`, and amends them into the landing commit. That is what a longer train does for a first change that never moved. The change is left committed, shipped and unclosed, for the person to fix and land again.

**Both escapes in the intent are closed by the same rule.** The landing no longer trusts any gate that wasn't run on the commit it is about to close:
- The untracked file is tracked by `land`'s commit before the gate runs.
- A base that moved under `fresh` is in the stacked commit the gate runs on.

**`ungated`.** `_train_reading()` puts `"ungated": None if factory._base_check(main, base) else f"{base}'s .sdlc/config.toml names no [commands] check"` into `out`, beside `gates`. `_run_end()` adds `ungated` to its summary keys in both branches: the live-state branch computes it the same way, and the cleared-state branch copies it from the final reading, which is the one that wrote the state as None. `ungated` is a reading of the base branch's config, never stored in the train's state. A base that gains a check mid-train is gated from the next reading on.

**The question.** `land_question(batch, base, moves, gated=True)` changes only the gate clause, as R7 words it. Every other clause, and the answers, stay. The skill quotes the question's fullest form in its Step 2 and keeps quoting the gated form, since the skill never words its own question and asks the script's text literally.

**Cost.** A one-change landing runs the base's check once more, which takes minutes on a large suite. No second approval comes with it: `gated once at the tip` is what the person's yes already says, and `gate` is already one of `RUN_STEPS`. The retrospective's land-gate count (`retro.py`'s `land_gates`) rises by one per one-change landing from this change on. That is a real figure, not a change to how it is read.

**Boundaries.**
- Always: gate the tip, a train of one included, on its committed, stacked commit, with the base branch's check.
- Ask first: nothing new. The existing yes covers the gate.
- Never:
  - push or close a change whose stacked commit has no green gate, when the base names a check;
  - run the change's own copy of `[commands] check`;
  - bisect or stop differently for longer trains;
  - change the build round's gate (see the second open question);
  - add a landing review for `unreviewed=N`.

## Contracts touched

- **The factory runs a host's command only through `factory.py gate` and `check` (`_run_check()`), the base branch's `[commands] check`.** The new gate is `gate --land` itself, reached through the loop's existing `RUN_STEPS`. No new call site, and the command is read from the base branch (`_base_check(main, base)`, `_base_command()`), never the checkout.
- **A gate, build or accept record is a verdict only while the records ledger vouches for it (`vouched()`, `RECORDS_LEDGER`).** The design widens where the ledger is enforced: `_read_gates()`'s forged check now runs for a train of one too (R4). The ledger itself is unchanged.
- **The land skill's one WAIT asks the script's question literally (`land_question()`), its yes options carrying `land-check`'s `shown` as preview.** The wording changes only on a base with no check (R7), still worded by the script. No new WAIT and no new answer: `test_every_wait_asks_in_a_dialog` and `test_every_wait_names_its_preview` are untouched.
- **`train --run` takes only `RUN_STEPS` and ejects only a gate's fault on its own.** A red one-change tip is exactly a gate's fault, `cause: gate`, so the loop ejects it with no stop. Every other stop is unchanged.
- **A change ejected goes back to its pre-train commit (`--eject`, `reset --keep`). Never a force, a stash or a merge of the base into the branch.** For a change that never moved there is nothing to reset, and the only write is the existing amend of its records.
- **The base branch: `git.base`, passed as `trunk`. Never `main` in a git call.** No new git call. The test hosts use their `main` as the base.
- **Scripts run on Windows.** No new subprocess or file write in the scripts. The new tests lean on `sh` and git through `uv run`, so they are `needs_uv` and not `portable`, like the train tests beside them.
- **Nothing about a project.** The test data is neutral (`forbidden.txt`, slugs like `aa`). The spec and the tests never name the host where the escape happened.

No invariant needs to change.

## Alternatives rejected

- **Keep the shortcut when the recorded gate's tree provably equals the committed tree on the same base commit.** It saves one gate per one-change landing, but it is exactly the comparison that failed. `build_hash()` hashes the worktree's files, while a check can read git's index, `git ls-files`, or anything else the commit changes, and both escapes in the intent passed a gate of the "same" change. Proving equality well enough to stand in for a gate means re-deriving what the gate observes. It is easy to get wrong, and wrong pushes a red base.
- **Gate inside `land` (`cmd_land()`), right after its commit.** That would be a second gate path outside the train, with its own record and its own ejection. The train is already the one place that gates, bisects and ejects, and a train of one is just a train.
- **Fix only the build round's gate (`git add -N` before `[commands] check`).** It would close the untracked-file escape but not the moved-base one, and it changes the index of a change's worktree during a judging step whose rule is "the tree as it found it" (`_tree_hashes()`). It is a separate change, if wanted (see the second open question), and not a substitute for gating what lands.
- **Refuse to land on a base with no `[commands] check`.** That is a policy change no one asked for. The intent asks only that such a landing say so (R6, R7).
- **Store `ungated` in the train's state.** The state is cleared on `done`, and a base's config can change between readings. Reading it each time is simpler and always current.

## Verification

```bash
uv run --group dev pytest -q -n auto tests/test_train.py tests/test_land.py tests/test_skills.py
./check.sh
grep -rn "gated as its build was\|lands on its round's gate alone" plugins/ docs/ AGENTS.md
```

What healthy output looks like:
- **The pytest run** passes, the new R1–R4, R6, R7 and R8 tests included.
- **Against the unfixed `_train_gate()`**, run during the build to show the tests reproduce the bug:
  - R1 fails with a `close` reading;
  - R2 fails with the change closed and the base advanced;
  - R3 fails with no `land-1.gate.md`;
  - R4 fails with nothing stopped.
- **`./check.sh`** ends green: ruff, the format check, pytest and `claude plugin validate --strict`.
- **The grep** prints nothing.

