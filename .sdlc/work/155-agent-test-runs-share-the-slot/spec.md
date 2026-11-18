---
id: 155
slug: agent-test-runs-share-the-slot
kind: spec
created: 2026-11-18
updated: 2026-11-18
---

# 155 — Agents' test runs share the machine with the gate · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions, each checked in the code at this worktree's base:

- The builder can't cite the gate record for its own build. `cmd_gate()` refuses with "no builder report yet: build/round-1.md comes first", and the build step's order is `gate` after the builder's report and before `review`. So the gate always runs right after the builder reports, and its record never exists when the builder writes `## Evidence`. The intent's "a builder cites the gate record" therefore becomes "a builder leaves the full suite to the gate that runs next". Reviewers can cite the record, because it exists before they start.
- The reviewer prompts (`reviewer-code.md`, `reviewer-test.md`, `reviewer-behaviour.md`) already say to read `build/round-N.gate.md` and never run the gate. None of them says not to run the whole suite another way (`pytest -n auto`, or the test runner with no test named). That gap is what this change closes.
- `is_read()` already treats `cat`, `head` and `tail` as reads. So `$ cat .sdlc/work/NNN-slug/build/round-N.gate.md`, followed by its output, already passes `read_evidence()` with no `exit:` line. The evidence rules need a test that pins this, not new code.
- An agent session (`claude -p --agent …`, `cmd_agent()`) is told no path to `factory.py`. The prompts `_task()` builds name the change folder and the worktree only. An agent can't run a new command unless its prompt names it.
- `metrics.py` counts a `test_runs=` run as the host's check, `sdlc.py gate` (`HAND_GATE_RE`), or a `TEST_RUNNERS` program. It doesn't count a run of `factory.py check`, so moving full runs into `check` would hide them from the count the Outcome measures by.
- The resolver (`resolver.md`) also runs the gate itself, and its `## Evidence` example is `$ ./check.sh`. It is an agent running full suites outside the slot, so it is in scope under the Outcome's "agents are told to use it in place of a bare `./check.sh`", although the intent's Affected list doesn't name it.

R1. `factory.py check <NNN>` runs the base branch's `[commands] check` (`_base_check()`) in the change's worktree (`change_root()`). The command's stdout and stderr go straight through to the caller, and `check` exits with the command's exit code. A test sets the base branch's check to `echo base-ran; exit 3` and the change's own `.sdlc/config.toml` to a different command. It asserts that `base-ran` is printed and the exit is 3. The test fails if the worktree's own command runs or the code is swallowed.

R2. `check` refuses without running anything, printing `{"refusals": [...]}` and exiting 1, in three cases: no base branch, no `[commands] check` on the base branch, or an id that names no change. The refusal wording matches `cmd_gate()`'s. A test covers each case, with a check command that writes a stamp file, and fails if the stamp appears.

R3. `check` holds one of `gate_jobs` slots (`gate_slot()`, the same `SLOT_NAME` lock files in the git common dir as `gate`, never `sdlc.lock`) for as long as the command runs. While it waits, it prints `NNN-slug: waiting for a gate slot (…)` on stderr.
- A test with `gate_jobs = 1` starts two `check` runs at once. Each runs a command that records its start and end times. The test asserts that the two intervals don't overlap and that one of the runs printed the waiting line.
- A second test holds slot 0 through the existing `HOLD` child (the gate's own slot). It asserts that `check` waits until the child is killed, which shows that gates and checks share the slots.

R4. `check` frees its slot however it ends. A test starts `check` with a command that sleeps, kills the `check` process, and then takes the slot through `gate_slot()` within 2 seconds. When the command runs past `GATE_TIMEOUT`, `check` kills it, says `timed out after <n>s` on stderr, and exits non-zero. A test with the timeout patched small covers this.

R5. `check` writes nothing: no `build/*.gate.md`, no file in the change's folder, and no change to what `verdicts` says. A green `check` never stands in for the gate. A test runs `check` green on a change whose `verdicts` says `gate`, then asserts two things: `verdicts` still says `gate`, and `git status --porcelain` of the folder is unchanged.

R6. Every prompt `_task()` sends the builder names the full `check` command: `uv run --quiet --script <this factory.py's absolute path> check <NNN>`. That covers `build`, `fix`, `rework`, a restart's build, an upgrade's build, and the reply to a decision. The prompt `_land_task()` sends the resolver names it too. No reviewer's, verifier's or approver's prompt names it. A test builds each prompt and asserts which ones hold `factory.py check <NNN>`.

R7. `builder.md` says the following, and `tests/test_skills.py` asserts each phrase:
- After each slice, run the slice's own tests by name, not the whole suite.
- The script's gate runs the whole suite on the build before any reviewer, so a whole-suite run only for the report repeats it.
- When a full run is wanted, use the `check` command the prompt names, never a bare `[commands] check` or the test runner with no test named.
- The report gives the named tests it ran and their counts, and leaves the gate's result to `build/round-N.gate.md`.
- The `## Evidence` example shows a named test run, not `./check.sh`. A test fails if the example's `$` line is `./check.sh`.

R8. The three reviewer prompts each say that the gate's record is the whole suite's result for the round. They each say never to run the whole suite another way (the gate's command, the test runner with no test named, or `factory.py check`), and to run only the named tests a finding rests on. `reviewer-behaviour.md` also still says to run the end-to-end path the spec describes. The existing assertion `never run the gate again yourself` stays, and a new one checks each prompt for the whole-suite phrase.

R9. `resolver.md` says to run the tests the conflict touched by name and, for a full run, the `check` command its prompt names. Its `## Evidence` example no longer shows `$ ./check.sh`. A test asserts both.

R10. A `## Evidence` section that cites the gate record with a read passes `read_evidence()` with no `exit:` line. That means `$ cat .sdlc/work/NNN-slug/build/round-N.gate.md`, or `head -n 3` of it, followed by its `GATE: PASS` line. A `$ uv run … factory.py check 155` line with no `exit:` still fails. One test in `tests/test_evidence.py` pins both.

R11. In `metrics.py`, a `Bash` command that runs `scripts/factory.py check` counts as a test run. It counts in `test_runs=` (`_shell()`) and wherever `HAND_GATE_RE` marks a run of the check today. `factory.py land-check` and `factory.py gate` don't count. A test in `tests/test_metrics.py` feeds `_shell()` all three commands and asserts `test` is true only for `check`.

R12. The docs say what `check` is. `plugins/factory/README.md` lists `check` among the commands and adds it to the gate-slot paragraph ("Gates and `check` runs from every worktree share `gate_jobs` slots"). The *factory* paragraph of `AGENTS.md` names `check` beside `gate` as the commands that run the base branch's `[commands] check` (see Contracts touched). `factory.py`'s docstring names `check`. An acceptance check in `checks.md` greps for the README's line; a test can't fail on it short of a revert.

## Design

**`cmd_check(root, ident)`, in `factory.py` beside `cmd_gate()`.**
- **Setup.** It reuses `find_change()`, `_base()`, `_base_check()`, `load_config(root)[0]["gate_jobs"]` and `gate_slot()` unchanged. `main()` already resolves `root` to the change's worktree through `change_root()` whenever the command takes an `id`, so `check` runs where `gate` does.
- **Running the command.** Inside `with gate_slot(root, jobs, folder.name)`, it runs `subprocess.run(_sh(command), cwd=root, stdin=subprocess.DEVNULL, timeout=GATE_TIMEOUT)` with no capture. The output reaches the agent's shell as `./check.sh` would print it, and since the call isn't text-mode, no `encoding=` is owed.
- **Exit and timeout.** It returns the command's exit code. On `TimeoutExpired` it prints the timeout line on stderr and returns 1. On `OSError` it prints `didn't run: …` and returns 1.
- **No record and no tree check.** It writes no record and doesn't hash the tree, because it proves nothing to the script (R5).

**One runner.** `gate` and `check` start the host's command through one helper, `_run_check(root, command, capture)`. That keeps a single function where `factory.py` runs `[commands] check`, which is the point of the policy line this change edits. `gate` keeps capturing, its timeout handling and its record exactly as now. Its tests (`test_a_killed_gate_frees_its_slot`, `test_a_factory_gate_waits_for_a_hand_gates_slot`, `tests/test_hand_gate.py`'s slot copies) must pass unedited.

**The lock is never inherited.** `os.open` descriptors are non-inheritable by default in Python 3 (PEP 446), so the host's command never holds the lock itself. If `check` dies, the OS frees the slot. A `check.sh` orphaned by that kill can keep running unslotted. That is the same as a killed `gate` today, and isn't new.

**Naming the command to the agent.**
- `FACTORY_SCRIPT = Path(__file__).resolve()`, next to the existing `FACTORY_ROOT`.
- `check_line(folder)` returns one sentence: `A full run of the suite, when you want one, is \`uv run --quiet --script <FACTORY_SCRIPT> check <NNN>\`: it waits for a gate slot.`
- `_task()` appends it to every builder prompt. `_land_task()` appends it to the resolver's.
- The absolute path is this machine's. It never reaches a committed file: a reply that quotes it is filed through `_placeholders()`, as every reply is.

**The agents' Bash timeout.** A `check` that waits for a slot can outlast the Bash tool's default timeout. `builder.md` and `resolver.md` tell the agent to run `check` in the foreground with the tool's longest timeout. If the tool kills it anyway, the slot is freed (R4) and the agent can fall back to named tests.

**Prompts.** The edits are the wording changes R7, R8 and R9 name and nothing else. The behaviour check's end-to-end run is untouched. In `builder.md`:
- *Then: build it*: step 3's "then run the repo's gate" becomes "then run the slice's tests".
- *Rework rounds*: "Rerun the tests and the gate" becomes "Rerun the tests the kept changes touch".
- *A red gate* already says the gate is the script's, and stays.
- *What you return*: "the gate's result (its test count)" becomes the named tests and their counts.

**Metrics.** `FACTORY_CHECK_RE = re.compile(r"scripts/factory\.py\s+check(?:\s|$)")`, used beside `HAND_GATE_RE` in both places that regex is matched. `land-check` can't match, since the regex needs whitespace before `check`. The trailer format is unchanged: only what counts as a test run is extended, which the module's docstring allows.

**Open question 2, the tests "near its change", is answered: the agent names them.** The plugin knows nothing about how a host lays out its tests (*Mechanism vs. policy* in `AGENTS.md`), so the script can't map touched paths to tests. The builder wrote the tests and the reviewers read them, so each names what it runs.

**Edge cases.**
- **`gate_jobs` is invalid.** `_gate_jobs()` already falls back to 1 with a warning.
- **Outside a git repo.** `gate_slot()` yields `(None, 0.0)` and `check` runs unslotted, as `gate` does.
- **A `check` while the same change's gate runs.** They are two holders of the slots like any others. With `gate_jobs = 1`, one waits for the other.

## Contracts touched

- **"`factory.py gate` the one place it runs a host's command, the base branch's `[commands] check`"** (`AGENTS.md`, *The factory*; README, the paragraph on `gate`). **This change needs that sentence edited**, to "`factory.py gate` and `check`, through one function (`_run_check()`), the only places it runs the base branch's `[commands] check`". Running the host's command from a second command is the whole point of the Outcome. One shared runner keeps the property the sentence protects: one place to read to know how the host's command is run. This is a policy edit for the person to approve with this spec, not a side effect.
- **The gate is the one proof the whole suite passed** (intent Constraints; `verdicts` decides from the rounds alone). `check` writes no record and `verdicts` never reads it (R5), so nothing it does can clear a `gate` step or the approver's `gate` reasons.
- **Slots: locks in the git common dir, never `sdlc.lock`; the hand gate takes them through pinned copies.** `check` calls `gate_slot()` itself, and `SLOT_NAME`, `_try_lock()` and `_unlock()` are unchanged, so `test_the_slot_copies_are_the_factorys` still holds. `sdlc.py`'s hand gate needs no edit, and `check` and the hand gate wait for each other.
- **No agent gets a permission it lacks today.** Builder, resolver and reviewers already have `Bash`, and the run's `mode` is unchanged. `check` runs only the base branch's command, which a change can't edit, the same command the agents' `./check.sh` runs today. No skill's `allowed-tools` gains a rule, since no skill runs `check`.
- **Agents that judge have no Write; no agent but the builder runs `checks.md`.** Untouched: `check` runs `[commands] check`, never a `checks.md` section.
- **Only the builder edits; no agent commits.** Unchanged.
- **The scripts run on Windows.** Host commands go through `_sh()`, never `shell=True`. The new `subprocess.run` isn't text-mode, and no platform module is imported at the top. `os.open`/`_try_lock()` are already portable, and the R3 and R4 tests are marked `portable` where they use no shebang fakes.
- **Metrics' contract: extend, never redefine.** R11 widens what counts as a test run and changes no key or format. `metrics.py` stays pure: it matches a command's text and runs nothing.
- **Nothing local.** The absolute path lives only in a prompt, which is never committed. Any reply quoting it is filed through `_placeholders()`.
- **Review doc, *A finding counted for the wrong reviewer*.** Not touched: no finding or `By:` changes.

## Alternatives rejected

- **A lock inside this repo's `check.sh`.** It would fix this repo alone. The plugin knows nothing about a host's command, and every factory host has the same contention.
- **The script picking the tests near a change from the paths it touched.** That needs knowledge of a host's test layout, which belongs to the host. A wrong mapping would also give the agent false confidence.
- **Letting reviewers use `check`.** The gate already proved the suite on exactly this build. A reviewer's full run, slotted or not, repeats that proof and adds a wait to every review.
- **A green `check` that records a result or clears the gate.** That would make two proofs of one thing, and an agent-run one could disagree with the script's. The intent's constraint rules it out.
- **A hook or permission rule that blocks `./check.sh` in agent sessions.** It depends on the permission mode, touches the agents' permissions (a constraint), and would block the resolver's legitimate runs. Prompts and a slotted alternative are enough for the Outcome.
- **Capturing `check`'s output and printing a tail, as the gate's record does.** That hides the failing test an agent needs. Streaming is what the agent gets from `./check.sh` today.
- **`-n <cores ÷ gate_jobs>` in this repo's own gate** (open question 3). It is this repo's own `check.sh` policy, not the plugin's, and is orthogonal to the slot. It is left out of this change (see the questions below).

## Verification

```bash
./check.sh
uv run --group dev pytest -q tests/test_factory.py -k "check"
uv run --group dev pytest -q tests/test_evidence.py tests/test_metrics.py tests/test_skills.py tests/test_hand_gate.py tests/test_windows.py
uv run --group dev pytest -q -m portable
```

Healthy output:
- `./check.sh` ends with ruff clean, pytest all passed, and `claude plugin validate --strict` passing.
- The `-k check` selection collects the new R1–R6 tests, more than zero, and all pass.
- `test_a_killed_gate_frees_its_slot`, `test_a_factory_gate_waits_for_a_hand_gates_slot` and `test_the_slot_copies_are_the_factorys` pass unedited.

By hand, in a scratch repo with `gate_jobs = 1` and a check of `sleep 5; echo done`:
1. Start `uv run --quiet --script plugins/factory/scripts/factory.py check 001` in two shells at once.
2. One prints `done` after about 5 s.
3. The other prints `001-…: waiting for a gate slot (1 of 1 in use)` first and `done` after about 10 s.
4. Both exit 0, and `git status` shows nothing new.

The Outcome is measured after landing, not by the gate. On the next parallel batch, the per-role `test_runs=` lines on the `Close` commits should show fewer whole-suite runs per builder and none per reviewer. Each gate's `Seconds:` should stay near its solo time.
