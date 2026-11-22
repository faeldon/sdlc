---
id: 228
slug: autopilot-readiness
kind: spec
created: 2026-11-22
updated: 2026-11-22
---

# 228 — The autopilot loop is tested end to end before anyone runs it unattended · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions, each checked in the code:

- **How the loop runs.** It already starts every step as `factory.py` in a subprocess (`autopilot.run_step()`, autopilot.py:424). It calls `factory._sdlc()` in its own process for `new`, `status --json` and `config`. `_sdlc()` finds the clone's `sdlc.py` through `sdlc_path()` when the factory is read in place, which `test_candidates_come_from_the_real_status_json` already relies on.
- **Each piece already works on its own.** A real `train --run` with a stand-in `claude` on `PATH` lands changes through the real `ship` and `close` (`test_a_killed_train_run_resumes`). A real `run_step` child passes `--by autopilot` under the lock (`test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does`). So the end-to-end test puts together paths that each work alone. The new part is running them as one loop of real children.
- **Half of nit 2026-11-21-54 is already done.** `test_the_changes_own_code_never_runs_as_a_loops_child` (tests/test_autopilot.py:1287) shows that a host's `[commands] check` run by a `gate` step through `run_step` sees neither marker. What is missing is a test of `take_markers()` itself, and the same check made inside a real `--run`.
- **Who writes `decisions.md` in an autopilot run.** Only `decisions` (`cmd_decisions`, factory.py:2219, the first command of the loop's `read` step) and `answer` (`cmd_answer`, factory.py:2511) write it. `agent` files a reviewer's reply under `reviews/` and never writes the ledger. The loop runs a change's answers one after another (autopilot.py:555). The only commands it starts together are a review's roles (`run_all(..., together=True)`), and none of those writes the ledger.
- **`BUILT_RE` has one reader and no copy.** It is read only by `unbuilt_defaults()` (factory.py:2385), which `cmd_ask()` and autopilot's `hold_causes()` call. `scripts/factory_records.py` has no copy of it, so no pinned copy needs to change.
- **Idea 2026-11-21-48 is not on the nits line.** It is this change's `idea:` and is retired through that link, so it isn't listed below.

Nits taken in: 2026-11-21-51, 2026-11-21-53, 2026-11-21-54, 2026-11-22-1, 2026-11-22-2, 2026-11-22-11

1. **R1. One real loop, from a seed to a landed change.**
   - A new test, `test_autopilot_run_lands_a_seed_through_real_subprocesses` in `tests/test_autopilot.py`, builds a scratch host. It has one `[idea]` seed, `[autopilot] enabled = true` and a `[commands] check` on the base branch, and no remote.
   - It runs `factory.py autopilot --begin`, then `factory.py autopilot --run`, as subprocesses of the test. Nothing in the loop is monkeypatched, since no monkeypatch reaches a child process.
   - A stand-in `claude` is first on `PATH` (`train_driver.fake_claude()`). It answers the planner, the intent-writer, the builder, the reviewers, the approver and the landing's agents.
   - The test asserts that:
     - the run exits 0 and the state records the change's place as `landed`;
     - the base branch's first-parent line holds `Close NNN-slug`;
     - a commit on the base branch carries `Sdlc-Landed: by=autopilot`;
     - the change's `intent.md`, read from history at its last commit before close, holds `opened_by: autopilot`;
     - its `decisions.md`, read the same way, holds at least one `→ decided by autopilot:` line and no ` → decided: `;
     - the stand-in's log names the planner, the intent-writer and the builder, so the real agents path ran.
   - The test fails if any step a loop takes in its own process today is moved behind a stand-in, or if any child loses what it needs to pass `--by autopilot`. For example, the train's `land --by autopilot` would fail if `loop_env()` stopped giving the markers back to `train --run`'s children.
2. **R2. Inside that same real run, nothing outside the loop holds a marker.**
   - The host's `[commands] check` writes its environment to a file outside the tree. That covers the loop's own `gate` step and the train's tip gate.
   - The stand-in `claude` records, for each session, whether `AUTOPILOT_RUN_ENV` or `TRAIN_RUN_ENV` was in its environment. This is a new `markers` field in `FAKE_CLAUDE`'s log line.
   - The test asserts that every check environment holds `PATH=` and neither marker, and that every session's `markers` is empty.
   - It fails if `take_markers()` stops being `main()`'s first step, or if `_run_check()` or `_claude()` is given `loop_env()`.
3. **R3. `take_markers()` has a test of its own.**
   - `test_take_markers_moves_both_markers_out_of_the_env` starts with both markers set in `os.environ` and an empty `LOOP_MARKERS` (both through `monkeypatch`). After `take_markers()`, it asserts:
     - neither marker is in `os.environ`;
     - `LOOP_MARKERS` holds both values;
     - `loop_marker()` returns each value;
     - `loop_env()` holds both again;
     - `agent_env()` holds neither.
   - A second case starts with neither marker set. It asserts that `take_markers()` leaves `LOOP_MARKERS` empty and `os.environ` unchanged.
   - The test is marked `portable`, since it starts no process.
4. **R4. The refused half of the real-step test goes through `_claude`.**
   - In `test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does`, the direct `subprocess.run(..., env=factory.agent_env())` is replaced. Instead, `factory._claude()` is called under the lock, with the loop's env set, and starts the stand-in `claude`.
   - The stand-in runs `factory.py answer 008 D2 --by autopilot` and writes that command's output to a file outside the tree.
   - The test asserts that the output holds `BY_AUTOPILOT_REFUSED`, that D2 is still open in the ledger, and that the `run_step` half still answers D1 as autopilot.
   - It fails if `_claude()` stops passing `env=agent_env()`.
5. **R5. `cmd_answer`'s missing lock is stated where it is relied on, and pinned.**
   - `cmd_answer`'s docstring says three things:
     - It reads and rewrites `decisions.md` with no lock.
     - That is safe only because the loop never runs `answer` or `decisions` for a change while another command for that change is running. It answers a change's lines one after another, and the only commands it starts together are a review's roles, which never write the ledger.
     - Anything that starts `answer` beside another writer of the same change's ledger must add a lock first.
   - `cmd_decisions`'s docstring names the same rule.
   - A new test, `test_no_ledger_writer_runs_beside_another_step_of_its_change`, drives the in-process loop through the `Steps` stand-in. It uses two independent seeds, so changes run in parallel, and a review with several roles. The stand-in records which commands are running for each change, with a short sleep to widen the window. The test fails if `answer` or `decisions` ever starts while any other command of the same change is running.
6. **R6. A refused agent leaves no landing step and no session behind.**
   - In `cmd_agent`, `record_closes()` runs after every check that can refuse, and before anything is written. That means before the new session id is added to `runs/<agent>.sessions`, and before `_record_land()`.
   - `test_an_agent_refused_on_its_closes_leaves_nothing_recorded` makes the ledger append raise `OSError` and runs a landing task. It asserts that:
     - the exit is 1, with the refusal `couldn't record the intent's closes: in the ledger:`;
     - `runs/land-step.md` was not written;
     - the sessions file is as it was;
     - `claude` was never started.
   - With the old order the test fails, because `land-step.md` exists.
7. **R7. `recorded_closes()` keeps its reread, and the docstring states the cost.**
   - No cache. The docstring says it reads the ledger once per call, and that `start` and `agent` each call it once per process. Each `agent` call also starts a whole agent session, so a cache inside one process would save nothing.
   - `test_an_agent_run_reads_the_closes_once` counts `recorded_closes()` calls in one `cmd_agent` run and asserts exactly one. A change that starts calling it in a loop fails that count.
8. **R8. A `- BUILT:` line inside a code fence doesn't count as built.**
   - `unbuilt_defaults()` reads a builder report's lines through a new helper, `unfenced_lines(text)`, in `factory.py`. The helper uses the CommonMark fence rule `split_draft()` already uses (`FENCE_MARK_RE`):
     - a fence opens on three or more backticks or tildes;
     - it closes only on the same character, at least as long, with nothing after it;
     - a fence that never closes runs to the end of the report.
   - The parametrized `unbuilt` cases in `tests/test_factory_decisions.py` (near line 832) gain four cases:
     - a `- BUILT: D2` only inside a backtick fence → `rebuild`;
     - the same inside a tilde fence → `rebuild`;
     - the same inside a fence that never closes → `rebuild`;
     - the line after a closed fence → `ship`.
   - `test_a_fenced_built_line_still_holds_autopilot` calls `hold_causes()` on the same fenced report and asserts the `unbuilt` hold. Each case fails with today's `BUILT_RE` scan.
   - `plugins/factory/README.md`'s sentence about `- BUILT: D<n>` (line 606) gains "outside a code fence".
9. **R9. A person's runs see no change.**
   - `agent`, `answer`, `ask` and `decisions` print the same JSON and write the same files on every path that doesn't refuse.
   - Every existing test passes unedited, except the refused half of the real-step test that R4 replaces and `FAKE_CLAUDE`'s extra log field from R2.
   - `./check.sh` is green.

## Design

**The end-to-end test (R1, R2).**

- It lives in `tests/test_autopilot.py` under a new section, `# ---- the whole loop, as it runs`.
- It is marked `needs_uv` (the loop's `_sdlc` and the landing's `ship`/`close` run `sdlc.py` through `uv`). It is also skipped with `os.name == "nt"`, because the stand-in `claude` is a shebang file. It isn't `portable`, so CI's Windows job never collects it.
- The scratch host is built as `test_train.py`'s `_repo()` builds one: a `README.md`, `.gitignore` with `.claude/worktrees/`, and the register holding one seed.
- On `main` it commits:
  - `.sdlc/factory.toml` with `[autopilot] enabled = true` and enough `debt`;
  - `.sdlc/config.toml` with `[commands] check` set to `"<python>" "<script>" "<out-dir>"`. That script appends its env to a numbered file in `<out-dir>`, so the loop's gate and the train's tip gate each leave one.

**The stand-in `claude`.**

- It is `train_driver.fake_claude()` with one plan entry per agent name, and no change name in the key: there is one change, and its number isn't known in advance.
  - `autopilot-planner` replies `- WAVE: <seed>`.
  - `intent-writer` replies a Tier 1 draft, the shape `_draft()` gives.
  - `builder` writes one file in its worktree (`keep.txt`), and on its first call replies with `## Evidence` and one raised line, `- DECISION: [blocking] …` with two `- OPTION:` lines. Autopilot then really answers it through `answer --by autopilot`, and resumes the builder with `agent --task decided`.
  - `approver` replies `DECISION: READY` with `- IMPACT: patch`.
  - Reviewers and the arbiter take the fake's passing defaults.
- **The builder must raise its line once.** The `decided` session resumes the same agent, so a reply that raises the line again would raise a second ledger line. `FAKE_CLAUDE` gains a `once` option: the entry's `reply` is used only on its first call, and `then_reply` after that. Each call stays one log line.
- **What the plan confirms.** If the real `verdicts` path reaches the decision with a default left open, a default line is the simpler choice, and the plan picks whichever the code takes to `answer`. The check the requirement holds to is a `→ decided by autopilot:` line made by a real `answer` child.
- **`FAKE_CLAUDE`'s new log field.** It is `"markers": [n for n in ("SDLC_FACTORY_AUTOPILOT_RUN", "SDLC_FACTORY_TRAIN_RUN") if n in os.environ]`. The names are written out in full because the fake can't import `factory`. A test asserts they equal `factory.AUTOPILOT_RUN_ENV` and `factory.landing.TRAIN_RUN_ENV`, so a rename fails loudly.

**Running and reading the loop.**

- The loop is started with `subprocess.run([sys.executable, FACTORY_SCRIPT, "autopilot", "--run"], cwd=root, timeout=600, ...)`. Its env has `VIRTUAL_ENV` dropped, as `_sdlc` drops it. The timeout makes a hang fail instead of stalling `pytest -n auto`.
- The intent and ledger are read from history, because close removes the folder. The plan finds the commit with `git log --format=%H -1 -- .sdlc/work/<name>/intent.md` on the base branch's first-parent line, then reads each file there with `git show <sha>^:<path>` (the commit's parent, before the removal).

**The refused half through `_claude` (R4).**

- It reuses `fake_claude()` with a `builder` entry whose `run` is `["sh", "-c", "<python> <FACTORY_SCRIPT> answer 008 D2 --by autopilot > <out> 2>&1"]`.
- The test calls `factory._claude(["claude", "-p", "x", "--agent", "sdlc-factory:builder"], root)` while it holds `ap.autopilot_lock(root)`, with `AUTOPILOT_RUN_ENV` set. `_claude` adds no marker of its own, so the stand-in's child runs with `agent_env()`'s environment, as an agent's Bash would.

**`take_markers()` (R3).**

- `monkeypatch.setattr(factory, "LOOP_MARKERS", {})` isn't enough on its own: `take_markers()`, `loop_marker()` and `loop_env()` read the module global by name, so the patch must replace that global. It does, and the plan checks it.
- `monkeypatch.setenv` for both markers. `take_markers()` pops them, and the monkeypatch's undo is a harmless delete.

**The ledger-writer test (R5).**

- `Steps.__call__` takes a `threading.Lock`, adds `(change, argv[0])` to an in-flight set, sleeps 50 ms, and removes it when it returns.
- When the call is `answer` or `decisions`, it records an overlap if any other entry for the same change is in the set. The test asserts no overlaps.
- The run is the existing two-seed shape with independent seeds, and readings that give one change a `decide` with a pending blocking line, so `answer` really runs.

**`cmd_agent`'s order (R6).** After the `if resumed:` branch's refusal (no session to resume), the code runs, in this order:

1. `record_closes()`, returning the refusal on `OSError`, as now;
2. the new session id's append (moved out of the `else:` branch, run only when the session isn't resumed);
3. `_record_land()`.

Nothing between them can refuse, so on success the outputs and files are those of today.

**`unfenced_lines()` (R8).**

- It is a generator over `text.splitlines()`, keeping the open fence's mark. It doesn't touch `split_draft()`.
- The two functions share `FENCE_MARK_RE`. Each keeps its own loop, because `split_draft()` also tracks the bare `---` cut.
- A fence that never closes hides every line after it. That errs towards "unbuilt", so autopilot holds the change rather than lands it, which is the safe direction.

**Edge cases.**

- **A loop that doesn't finish.** If the loop parks or holds the one change, R1's `landed` assertion fails and prints `runs/autopilot.md`'s `held:` line in its message, so a broken loop shows why.
- **The host's `sdlc.py` version.** `sdlc_path()` refuses an `sdlc.py` of another version than the factory's. The test runs from the clone, where both manifests come from one commit.

## Contracts touched

- **`autopilot.py` is `[review] sensitive`.** No requirement edits it. If the end-to-end test exposes a defect in the loop, the fix lives there and the review weighs it as sensitive. The plan names any such fix as its own step (see Verification and the Boundaries below).
- **Only `loop_env()` gives the markers back, and only to a loop's own children.** R2–R4 test this rule. Nothing changes it.
- **The records ledger vouches for what it writes first.** R6 moves the `closes:` row's append earlier. That row carries no `record` or `sha256`, so it never vouches, and the vouched records (gate, build, accept, `parked.md`) are untouched. R7 adds no reader of the ledger.
- **`--by autopilot` is refused to every process but the loop's children** (`autopilot_running()`). R1 relies on it through the real path. `test_only_autopilot_names_by_autopilot` covers skills, not tests, so the new tests may name it.
- **No test reaches the network or a real `claude`.** The stand-in is first on `PATH` and its log must name every agent R1 lists. The scratch host has no remote and `git.push` is unset, so close pushes nothing. `status --json`'s CI reading has no tracker to reach, as in `test_candidates_come_from_the_real_status_json`.
- **The scripts run on Windows.** The new helper in `factory.py` starts no process and writes nothing. The test-only shebang fakes are skipped on Windows, and R3 is `portable`.
- **Factory and core stay apart.** `BUILT_RE` and the new helper are factory-only. `scripts/factory_records.py` has no copy of them, so `tests/test_modules.py`'s pinned copies are unaffected.
- **A doc's claim the change made false** (REVIEW.md). Nothing in `AGENTS.md` or `docs/REFERENCE.md` names the order in `cmd_agent` or the fence rule. `plugins/factory/README.md`'s `- BUILT:` sentence is made exact by R8. The comment above `_closes_line()` ("appended by `record_closes()` before any agent runs") stays true.

No invariant needs to change.

## Alternatives rejected

- **A lock for `cmd_answer`.** A lock file in the change folder writes into the tree. A lock in the git common dir is a new state file beside the two AGENTS.md lists, and it would be taken around a write that the loop already keeps from running twice at once. Neither lock covers the other writer that exists outside the loop: the person's `/sdlc-factory:decide`, which edits `decisions.md` with the Edit tool and takes no lock. Stating the rule and pinning it with R5's test protects exactly what a lock would, without a new file.
- **Caching `recorded_closes()`.** A cache inside one process saves nothing, because each process calls it once. A cache across processes is a new state file that has to stay in step with every ledger append. Both cost more than one read of a small file per agent session.
- **Running the end-to-end loop in process, with `subprocess` patched.** That is what `test_autopilot_end_to_end` already does. A monkeypatch can't reach a child, and the environment passed down to children is exactly what this change must test.
- **Also driving a hold and a park through the real loop.** `hold_causes()` and the park are decided from files the loop reads in its own process. They are covered in process by `test_held_change_and_its_dependents_never_land` (every cause) and `test_autopilot_waits_out_a_park_and_holds_past_its_deadline`. What only a real subprocess run can show (the markers passed to the loop's children, the real `answer`, `land --by autopilot` and close) is all on the clean path. Each extra path adds another full loop's run time to the gate.
- **Making `split_draft()` use the new fence helper.** That would touch how spec drafts are filed for no gain here. The two share the regex and keep their own loops.
- **Counting indented code blocks as fences for `- BUILT:`.** The nit names fences only, and a builder's report quotes in fences.
- **A Windows stand-in `claude` (`claude.cmd`), so the end-to-end test runs on Windows.** It isn't in the intent. The train's tests skip the same way.

## Verification

```bash
uv run --group dev pytest -q tests/test_autopilot.py -k "real_subprocesses or take_markers or real_step or ledger_writer or fenced_built" --durations=5
uv run --group dev pytest -q tests/test_factory_decisions.py tests/test_land.py tests/test_train.py -n auto
uv run --group dev pytest -q -m portable -k take_markers
./check.sh
```

What healthy looks like:

- The first command passes and lists the new tests. The end-to-end test reports one duration, and on a developer machine it should finish within about a minute. If `--durations` shows it over two minutes, the plan cuts steps: no `wave` round after the first, and the fewest reviewer roles a Tier 1 change takes.
- On a machine without `uv`, the end-to-end test shows as `s`, not `F`.
- The second command is green. It shows `FAKE_CLAUDE`'s new log field and the move in `cmd_agent` broke no landing or train test.
- The third collects R3's test alone.
- `./check.sh` ends green: ruff check, ruff format --check, `pytest -n auto` and `claude plugin validate --strict`.
- Each new test fails before its fix. The plan's build runs R6's and R8's tests against the old code once and records the red run.

**Boundaries.**

- **Always:**
  - put the stand-in `claude` first on `PATH`;
  - drop `VIRTUAL_ENV` for the loop's subprocess;
  - read landed files from history;
  - keep every success path's output as it is.
- **Ask first:**
  - any edit to `autopilot.py` or `landing.py` the end-to-end test turns out to need, since both are `[review] sensitive`, with the defect it fixes stated;
  - any change to what `FAKE_CLAUDE` replies by default, which the train's tests depend on;
  - growing the end-to-end test past one seed.
- **Never:**
  - a real `claude` or the network in any test;
  - a lock file or a new state file;
  - a change to `split_draft()`;
  - a nit not on the line above.

