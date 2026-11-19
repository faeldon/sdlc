---
id: 185
slug: landing-gates
kind: spec
created: 2026-11-19
updated: 2026-11-19
---

# 185 — The landing runs every gate a hand-built change gets, and stops only for what wasn't approved · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Nits taken in: 2026-11-19-47, 2026-11-19-48, 2026-11-19-36

Assumptions, each checked in the code:

- The person's yes covers each change's checks as `land-check` showed them. `land_parts()` takes them from `sdlc.py preflight`'s `checks` part, which is `acceptance()`, the same parser `sdlc.py accept` runs them with.
- Between the question and `train --begin`, the land skill runs only `factory.py accept` and `cases`. Neither writes `checks.md`: a check that leaves the tree changed fails (`left`).
- After `--begin`, only a landing agent can change `checks.md`: the `land-fix` builder, or the resolver when the file is conflicted. Both edit inside the change's folder.
- `accept` as stacked comes up only in a landing round (`land_round() > 0`), because `_train_reading()` step 4 skips a change with none.

**The acceptance checks, as stacked**

R1. `train --begin` records two things for each change in the train's state: `checks_sha` (sha256 of its `checks.md` bytes, or `null` with no file) and `checks` (each check's `name` and `command`, as `sdlc.py preflight`'s `checks` part gives them). Test: `test_begin_records_each_changes_approved_checks`. It fails if the state lacks either key, or holds a hash for a change with no `checks.md`.

R2. When a change's landing round names `accept` and its `checks.md` hashes to its `checks_sha`, the reading names `accept` with `checks: {"clear": true, "why": "as approved"}`. The loop then runs `factory.py accept <NNN>` itself and goes on. Test: `test_unchanged_checks_run_as_stacked_without_a_stop`. A train of two, both with checks, is stacked over a moved base and runs to `done`. Each `build/land-accept.md` holds an attempt on its stacked commit. The test fails if the loop stops at `accept`.

R3. A FAIL from `accept` run by the loop is not a failed command. The loop reads the train again, and the reading ejects the change with `cause` `review`, which pauses as today. Test: `test_checks_failing_as_stacked_pause_as_a_review_ejection`. It fails if the loop stops with `fix what it says …`, or if the loop makes the ejection itself.

R4. When `checks.md` changed, the script lists each check that was added or edited: its `(name, command)` pair is not among `checks`. If any of those fails the read-only test (R5), the loop stops at `accept` and runs no agent and no check. The stop says `checks.md` changed since the yes, and names each failing command with why. Test: `test_a_changed_check_off_the_list_stops_before_the_approver`. It fails if a fake `claude` or `sdlc.py accept` is called, or if the reason doesn't name the command.

R5. `read_only_command(text, checkout)` passes a command only when every rule below holds. Test: `test_read_only_command`, parametrized over each rule, passing and refused. It fails if any listed case gives the other answer.
- It splits on `&&`, `||`, `|`, `;` and newlines into simple commands.
- Outside single quotes, none of `>`, `<`, `` ` ``, `$`, `\`, a lone `&`, `(`, `)`, `{`, `}`, or an unquoted `*`, `?` or `[` that isn't a command's first word.
- Each simple command's first word is `grep`, `cat`, `head`, `tail`, `wc`, `test`, `[`, `true`, `false`, or `git` with `log`, `show` or `diff` as the very next word. No path to a program, no `VAR=value` prefix, no option before the git subcommand.
- No git argument starting `--output`, `--ext-diff` or `--textconv`.
- No word, and no value after an option's `=`, is absolute, starts with `~`, or has a `..` component.
- A word naming an existing path resolves inside the checkout, so a symlink out of it is refused.

R6. When the changed checks all pass R5 and no current approver record exists for the file as it stands, the reading names a new step, `checks`. The loop runs `agent <NNN> --task land-checks`: the approver in a fresh session, told the approved checks, the current ones and which changed. Its reply is filed in `build/land-<n>.checks.md` under a first line the script writes, `Judged: <sha16>`. `agent --task land-checks` refuses in two cases: the change is in no live train, or its `checks.md` still hashes to `checks_sha`. Tests: `test_changed_read_only_checks_go_to_the_approver` and `test_land_checks_refuses_outside_a_changed_train_change`, plus a fixture in `tests/prompts/` that pins the prompt.

R7. A record is current when its `Judged:` hash is the file's hash now. The reading names `accept` with `clear: true` only when the current record's reply opens with `CHECKS: HARMLESS` (read by `opening()`, with no disagreeing `CHECKS:` line) and R5 still passes. Otherwise it names `accept` with `clear: false`, and the loop stops showing the approver's reasons. That covers `CHECKS: ESCALATE`, a reply with no readable `CHECKS:` line, and lines that disagree. A stale record (a hash that no longer matches) sends the change back to `checks`. Test: `test_the_approvers_answer_decides_a_changed_check`, one case each for HARMLESS, ESCALATE, unreadable, disagreeing and stale. It fails on any wrong step or a missing reason.

R8. The approver's word alone never runs a check. A current HARMLESS record for a file holding a command that fails R5 stops the loop as in R4. Test: `test_harmless_never_clears_a_command_off_the_list`, with the record written by hand for a check running `rm -rf x`. It fails if `accept` runs.

R9. Just before it starts `accept`, the loop works out the clearance again from `checks.md` as it is (in `_run_plan()`), and stops if that disagrees with the reading. Test: `test_the_loop_rechecks_before_it_runs_accept`. It edits `checks.md` between a reading and `_run_plan()`, and fails if `accept` is planned.

R10. With checks in the batch, `land_question()`'s clause reads `its acceptance checks run as shown, and again as stacked`. With a change that calls for the build (R12), it adds `its build check run once at the tip`. Each clause appears only when it applies. Test: extend the `land_question` tests. They fail if a clause is missing, or shows up when nothing calls for it.

**`commands.build`**

R11. `gate <NNN> --land --build` runs the base branch's `[commands] build` (read from `<base>:.sdlc/config.toml`, never the checkout's) through `_run_check()`. It holds a gate slot, applies the same PASS rule as the gate (exit 0, tree unchanged, within `GATE_TIMEOUT`), and adds the attempt to `build/land-<n>.build.md` in the gate file's shape, first line `BUILD: <verdict>`. It refuses when the base branch names no build. Tests: `test_gate_build_runs_the_bases_build_and_records_it` and `test_gate_build_refuses_without_a_build`. They fail if the checkout's command runs, or if a record is written on a refusal.

R12. A change calls for the build when the base branch sets `commands.build` and at least one of these holds:
- `build_when` is unset;
- a path in its diff (`_changed_paths()`) matches `build_when` by `re.search`;
- a path in its diff is on the base branch's `[review] sensitive` list (`risk_paths()`);
- `build_when` is not a valid regex, which errs towards running.

Test: `test_which_changes_call_for_the_build`, parametrized over each case and over a base with no build. It fails on any wrong answer.

R13. The train names `build` at the tip when two things hold: any live change calls for it, and no PASS build attempt sits on the tip's stacked commit. That comes after the tip's gate is green, or when no gate is due, a train of one that never moved included. A PASS covers every change stacked below the tip, as `_land_gate_state()` reads a gate's PASS. Test: `test_a_train_of_one_runs_the_build_before_it_lands`. With `build = "true"` and `build_when = "."` it lands, and its commit holds `build/land-1.build.md`. The test fails if no build ran.

R14. A red build at the tip stops the train with a reason naming the exit and the record's file. It isn't bisected, and the loop ejects nothing. Test: `test_a_red_build_stops_the_train`, with `build = "false"`. It fails on an `eject` or a `done`.

R15. The build never runs when the base branch sets no `commands.build`, or when no live change calls for it. Test: `test_no_build_runs_unless_a_change_calls_for_it`. It fails if a `.build.md` file appears or a `gate --build` is planned.

R16. A build round's gate (`gate <NNN>` without `--land --build`) never runs `commands.build`. Test: `test_a_build_rounds_gate_never_runs_the_build`, with `build = "false"` and the round's gate PASS. It fails if the round's gate fails.

**The nits**

R17. In `_not_already_made()`'s refusals for an empty landing fix, `FIX: ALREADY MADE` appears at most once across the whole list, and each line is under 160 characters. Each still says what's wrong: no report, no answer or not first, no `## Evidence`, no `exit:`. Test: extend the case loop in `tests/test_land.py` (lines 2559–2571). It fails on a second mention or a long line.

R18. `taken_lines()` ends a `Nits taken in:` line's continuation at an indented line that starts a new list item (`-`, `*`, `+`, or `<digits>.` then a space). An indented sub-bullet naming an id to say it's left out retires nothing, and a wrapped plain continuation is still read. Test: extend `test_the_nits_taken_in_line_is_read_in_its_forms`. It fails if `"Nits taken in: 2026-11-17-11\n  - 2026-11-17-1 is left out"` names `-1`.

R19. `purpose_of()`'s docstring says a run whose `claude` gave no figures writes no `costs.jsonl` row, so the next try of the same task is not a `rerun`. Test: `test_a_run_with_no_figures_leaves_the_next_try_its_own_purpose`. It runs `agent` once with a fake `claude` that reports no figures, then once with figures. It fails if the first run wrote a row, or the second is tagged `rerun`.

**The docs**

R20. Each doc that states the old rule says the new one:
- `AGENTS.md`'s factory paragraph: `_run_check()` runs `check` and, for `gate --land --build`, `build`; the loop stops at `accept` only for checks not cleared.
- `plugins/factory/README.md`: the train paragraph and the script paragraph.
- `plugins/factory/skills/land/SKILL.md`: Step 3 (no more "The loop runs neither."), the steps list, the stops, and Resuming.
- `cmd_accept()`'s docstring.
- `RUN_STOPS`' comment.
- `landing.py`'s and `_run_check()`'s docstrings.

No test can read a doc's meaning, so the Verification grep and the review's "a doc's claim the change made false" pass check this one.

## Design

**What the yes approved, recorded.** `_train_begin()` reads each picked change's `checks.md` from its worktree. It calls `_preflight()` (already in `landing.py`) once per change that has the file, and stores `checks_sha` and `checks` in that change's entry in `TRAIN_STATE`, beside `pre` and `rounds_before`. The commands come from the parser that runs them, so the allow-list judges the same text `sdlc.py accept` executes. There is no copy of `acceptance()` to drift. An older train state without the keys reads as "no approved checks", so every check counts as changed and the loop stops as today: safe by default.

**The clearance, one function.** `checks_clearance(tree, folder, mine)` in `landing.py` returns `{"clear", "step", "why", "changed", "off_list"}`. The steps, in order:
1. Hash `checks.md`. If it equals `checks_sha`: clear, step `accept`, why `as approved`. Nothing else runs.
2. Otherwise read the current checks through `_preflight()`. A `problems` entry stops the train, saying what it is.
3. `changed` is the current checks whose pair isn't among the approved ones. Checks that were removed are listed for the approver but run nothing.
4. `off_list` is each changed command that fails `read_only_command()`, with why. If any: not clear, step `accept`, why naming them (R4, R8).
5. Read `build/land-<n>.checks.md`. If it's missing, or its `Judged:` hash isn't the current hash: step `checks` (R6). If it's current and opens with HARMLESS: clear (R7). Anything else: not clear, with the approver's reasons quoted.

`_train_reading()` step 4 calls it when `land_verdict()` names `accept`. It names `done("accept", name, checks=…)` or `done("checks", name, …)`. `_run_plan()` turns `accept` into `("accept", "{change}")` when the reading says clear, and first calls `checks_clearance()` again (R9). Otherwise it stops as today, its reason prefixed by the clearance's `why`. `RUN_STEPS` gains `"accept": (("accept", "{change}"),)`, `"checks": (("agent", "{change}", "--task", "land-checks"),)` and `"build": (("gate", "{change}", "--land", "--build"),)`. `TRAIN_STEPS` gains `checks` and `build`. `RUN_STOPS` keeps `accept`, now only for a reading that isn't clear. The loop's "failed" rule exempts `accept`, as it already exempts `gate`: its FAIL is read by the next reading (R3), while a refusal still stops it.

**`read_only_command()`** (R5) is a small hand-written scanner over the command text. It tracks single and double quotes, refuses the listed characters outside single quotes, and splits on the listed separators. Each simple command's words go through `shlex.split(posix=True)` (safe once the scanner has refused `$`, `` ` `` and `\`). Then it checks the program list, the git subcommand and its refused options, and the path rule against `checkout.resolve()`. It never runs anything. It lives in `landing.py` beside the clearance, so a later edit to the list gets the sensitive file's full review.

**The approver's landing task.** `land-checks` joins `TASKS`, `LAND_TASKS`, `TASK_ROLE` (`approver`), `TASK_PURPOSE` (`land`), `LAND_TASK_STEP` (`recheck`, an existing step, so the board's and `factory_records.py`'s copies of `LAND_STEPS` don't change) and `TASK_PROMPTS`. A new `prompts/land-checks.md` gives the approved checks, the current ones, the changed and removed names, and the question. The question asks whether any added or edited command writes, deletes, reaches the network, reads outside the checkout or reads a secret, or does anything but check. The reply must open `CHECKS: HARMLESS` or `CHECKS: ESCALATE`, then say why. `_land_task()` refuses unless `checks_clearance()` names `checks` for the change (R6), so the task can't be run out of turn. `cmd_agent()` files the reply under `Judged: <sha16>` in `build/land-<n>.checks.md`, never under `reviews/land-<n>/`, whose every file the landing reads as a review. `holds()` learns that for this task the approver's answer is a `CHECKS:` line, not a `DECISION:` one. A new `CHECKS_RE` sits beside `FIX_RE`. The approver gets no mend: an unreadable reply stops the train, and the person reruns the land skill.

**The build check.** `_base_command(root, base, key)` generalises `_base_check()`, which becomes `_base_command(root, base, "check")`. `cmd_gate()` takes `build`: with `land` it picks `"build"`, writes `land_build_path(folder, n)` = `build/land-<n>.build.md` with first line `BUILD:`, and refuses without one (R11). Everything else in `cmd_gate()` is shared: the slot, `_tree_hashes()`, `_placeholders()`, the attempt shape and `read_gate_file()`. `_run_check()` stays the one place a host's command runs; only its docstring changes. `build_due(tree, base, cfg)` in `landing.py` decides R12 for one change, from `_changed_paths()`, `build_when` on the base branch, and `risk_paths()` over `_sensitive()`. `_train_build(main, state, trees)` follows `_train_gate()` in `_train_reading()` step 3 and runs only when that returns None, meaning green or no gate due. `_read_builds()` gathers the tip's attempts into `state["builds"]` the way `_read_gates()` gathers gates. It returns:
- `None` when no live change calls for the build, or a PASS sits on a commit that has the tip's stacked commit as an ancestor;
- `build` at the tip when no attempt sits on its stacked commit;
- `stop` with the reason when the last attempt there is red (R14).

A re-stack, an ejection or a move changes the tip's stacked commit, so the build runs again, as the gate does. `runs/land-train.md` is unchanged, since core's copy of its parsing is pinned. The build record is amended into the change's commit with the other landing records by the existing `_amend_record()` path. `land-check` adds `build: true|false` per change, which feeds R10's clause.

**The nits.**
- -47: `_not_already_made()` words one refusal per case. `<nothing>, and <rel> doesn't open with that answer alone` names `FIX: ALREADY MADE` once, in the case where it is missing. The evidence case lists `read_evidence()`'s problems under a short lead without restating it.
- -48: `taken_lines()` leaves `inside` at a line matching `^\s+([-*+]|\d+\.)\s`.
- -36: one sentence in `purpose_of()`'s docstring, with R19's behaviour test pinning the fact it states. That behaviour lives in `cmd_agent()`'s `if figures:` guard.

**Edge cases.**
- A change with no `checks.md` at begin that gains one later: hash `null` against a file, so every check counts as changed.
- A removed `checks.md`: `accept` has nothing to run, and `land_verdict()` already counts no file as PASS.
- A `checks.md` edited during `accept`: the loop holds the run lock and runs one step at a time. The window between R9's check and `sdlc.py accept` reading the file is open only to an orphaned agent from a SIGKILLed loop, the known case behind `_run_loop()`'s comment.
- A train of one that never moved has no gate due. R13 still runs the build, through `cmd_gate`'s train rule `n == 0 → 1`.

### Boundaries

- **Always:** the base branch's commands only. A change's own `checks.md` runs unattended only when it is the file the yes covered, or when both the approver and the script clear what changed. Every run is recorded in the change's folder in the gate file's shape.
- **Asks first (stops):** a changed check off the list, an approver's ESCALATE or unreadable reply, a red build at the tip, and every stop that exists today.
- **Never:** run `commands.build` on a host that doesn't set it; run it in a build round; bisect a red build; run a changed check on the approver's word alone; add a skill rule; or touch `sdlc.py`, `board.py` or `factory_records.py`.

## Contracts touched

**A policy change, for the person to decide.** Today a check a change wrote runs only behind a prompt the person answers; `sdlc.py`'s `cmd_accept()` says "a person sees them listed and answers a prompt first", and `factory.py`'s says "the harness asks before every run". The intent restates the rule as "behind the person's yes for that exact command". The design as specified goes further, and that is the edit to approve: a check the person never saw also runs unattended when the approver judges it HARMLESS and the script's read-only list passes every added or edited command. That is the intent's Outcome, and it meets the Constraint, since the approver's word alone never runs a check (R8). The edit to `AGENTS.md`'s factory paragraph needs explicit approval:
- "`factory.py gate` and `check`, through one function (`_run_check()`), the only places it runs a host's command, the base branch's `[commands] check`" becomes "…`[commands] check`, and `[commands] build` for `gate --land --build`".
- "stopping at every other ejection, `accept` and a refused push" becomes "…at `accept` only for checks not cleared (`checks.md` changed since the yes and not cleared by the approver and the read-only list together)".

Other invariants this comes near, and how it stays inside them:

- **`[review] sensitive` covers `landing.py`.** The clearance, the allow-list and the build's train step all live there, so later edits get full depth. `factory.py` gets only the generalised config reader, `cmd_gate`'s `--build`, and the agent task's plumbing.
- **Modules loaded by path, placement by `tests/test_modules.py`.** New functions go where the rule puts them. Code only `landing.py` calls stays there. `_base_command()` and the prompt plumbing, which `factory.py` calls, stay in `factory.py`. `factory.py` never imports `sdlc.py`; it still reaches `accept` through `_sdlc()`.
- **The loop runs `RUN_STEPS` and no other command.** The new steps (`accept`, `checks`, `build`) are entries in `RUN_STEPS`, each a command of `factory.py` itself.
- **Agents that judge have no Write; no agent commits.** The approver's new task only replies, and the script files the reply.
- **A change can't edit the gate it is judged by.** `commands.build`, `build_when` and `[review] sensitive` are read from the base branch, never the checkout.
- **The run lock and every existing stop stay** (intent's Constraint). The one stop removed is `accept` for checks the yes covered, which is the intent's point. Every other stop, the lock, `--cancel` and the repeated-step guard are untouched.
- **Records a landing writes.** Every record goes through `_placeholders()`. The `LAND_STEPS` names, `runs/land-train.md` and the gate file shape are unchanged, so core's pinned copies don't move.
- **Windows.** No new module-level imports. Each new `write_text` passes `newline="\n"`, and paths are compared with `as_posix()`.
- **`git.base`.** No git call names `main`. `<base>:.sdlc/config.toml` is read through `_git(root, "show", …)`, as `_base_check()` reads it now.

## Alternatives rejected

- **A sandbox for the loop's checks.** Too much friction and too big a footprint for every host, and it's the idea's own rejection.
- **A permission rule.** It doesn't reach a background loop's subprocess, which no harness prompts.
- **The allow-list alone, or the approver alone, for a changed check.** The list can't see intent: `cat .env` is read-only and still leaks into a committed record. The approver's word can be wrong or steered by what it reads. The intent asks for both, and R8 pins that.
- **Running the allow-list over every check, unchanged ones included.** Simpler, but a check the person approved word for word (`uv run pytest …`) would then stop every landing whose fix touched `checks.md` at all.
- **Hashing the rendered command list instead of the file's bytes.** Bytes are stricter. An edit outside the `sh` blocks costs one approver run, never a wrong pass.
- **A copy of `acceptance()` in the factory to diff the checks.** A copy could parse differently from the parser that runs them, and the list would judge text that never runs.
- **Running the approver before the allow-list.** It's a paid run whose answer can't clear a command off the list anyway.
- **`awk`, `sed`, `find`, `sort` and `xargs` on the list.** Each can write a file or run a program (`system()`, `w`, `-exec`/`-delete`, `-o`, its argument). The idea's list named `awk`; it is left out (see the questions below).
- **`commands.build` in every build round.** Each round would pay the slow gate, and `ship` runs it once too. The bug's expected behaviour names the train's tip gate.
- **Bisecting a red build.** A slow command times ⌈log₂ n⌉ more runs, and a build that needs real services fails for reasons no change caused. The yes covered bisecting the gate only.
- **Recording the build in `runs/land-train.md`.** That file's parsing is copied in core and pinned, and the build's own record already shows each attempt.
- **A new `LAND_STEPS` name for the approver's judgement or the build.** That would touch `board.py` and `factory_records.py` in core for a label. `recheck` and `gate` already describe the two steps.

## Verification

```bash
uv run --group dev pytest -q -n auto tests/test_train.py tests/test_land.py tests/test_factory.py tests/test_prompts.py tests/test_modules.py
```

Healthy: every test passes, R1–R19's named tests among them, and the existing train, land and prompt tests are unchanged in what they assert. The exception is the `accept`-stop tests that R2 replaces, each now asserting the run goes on.

```bash
./check.sh
```

Healthy: `ruff check` and `ruff format --check` are clean, the full suite passes across the cores, and `claude plugin validate --strict` reports the plugin valid.

```bash
grep -rn "The loop runs neither\|harness asks before every run\|the base branch's \`\[commands\] check\`" AGENTS.md plugins/factory
```

Healthy: no line still states the old rule (R20). Each hit, if any, already names `build` or the cleared checks.

By hand, once, in a scratch host with the factory enabled (the plan may make this an acceptance check):
- With `[commands] build = "false"` and `build_when = "."` on the base branch, land a factory-built change. The train stops at `build`, naming the exit and `build/land-1.build.md`.
- With `build = "true"`, it lands, and its commit holds the record.

