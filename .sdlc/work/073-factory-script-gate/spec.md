---
id: 073
slug: factory-script-gate
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 073 — Run the gate as a script step before a factory round's reviewers · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1. A new command, `factory.py gate <NNN>`.** It runs `[commands] check` from the base
   branch's `.sdlc/config.toml` (`git show <base>:.sdlc/config.toml`), never from the checkout's
   copy.
   - It runs through `_sh()` in the change's worktree, with `encoding="utf-8"`,
     `errors="replace"`, no stdin, and a 30-minute timeout.
   - It adds one attempt to `build/round-<N>.gate.md`, where `<N>` is the newest builder report's
     round.
   - It prints `{change, round, attempt, verdict, exit, seconds, tree}`.
   - A test fails if the checkout's own `config.toml` is the one that runs.
2. **R2. The attempt record.**
   - The file's first line is `GATE: PASS` or `GATE: FAIL`, the latest attempt's verdict.
   - Each attempt is a `## Attempt <k>` section: the command, a `Build:` hash of
     `build/round-<N>.md` together with `build/round-<N>.files`, the exit (or `timeout`), the
     seconds, `Tree: unchanged` or `Tree: changed: <paths>`, and the output's last 80 lines.
   - A verdict is PASS only on exit 0, within the timeout, with the tree unchanged. The tree is
     hashed as `snapshot` hashes it, before and after the run.
3. **R3. `verdicts` names `gate` before `review`.** Once a builder report exists that no review
   round has read, `next` is `gate` unless `build/round-<N>.gate.md` holds an attempt whose
   `Build:` hash matches the report and snapshot as they stand now.
   - A PASS on the current build goes on to `review`.
   - A FAIL on the current build gives `fix`.
   - A test walks build → gate (fail) → fix → gate (pass) → review.
4. **R4. A new task, `factory.py agent <NNN> --task fix`.**
   - It resumes the builder with `The gate failed on round <N>: read
     <folder>/build/round-<N>.gate.md, fix what it shows, then report.`
   - It appends the reply to `build/round-<N>.md`, as an answer before review does.
   - The build skill snapshots round `<N>` again. The hash then differs, so `verdicts` says `gate`
     again.
   - `agent` refuses `fix` unless `verdicts` names it.
   - No reviewer or verifier runs on a build whose gate is red.
5. **R5. A cap on red gates.** At most `GATE_FIXES = 2` fixes per round. The third red gate in a
   round is a `stop`, with the problem `the gate failed 3 times in round <N>: <exit>`, and the
   change stays at `stage: build`. A red gate does not count against `rounds`, and `max_runs()`
   becomes `2 + rounds × (reviewers + 2 + GATE_FIXES)`.
6. **R6. With no `[commands] check` on the base branch, the step is skipped.** `verdicts` reports
   `gate: null` and why, goes straight to `review`, and writes no gate file. Step 1 and the WAIT
   say there is no gate.
7. **R7. The gate runs at both depths.** A light run gets the same script gate as a full one.
8. **R8. `reviewer-behaviour` stops running the gate.**
   - It no longer runs `[commands] check`. It reads the round's `build/round-<N>.gate.md`, runs the
     spec's end-to-end path, and still ends with `## Evidence` (`RUNS_THE_CHANGE` is unchanged).
   - The builder may still run the gate while it works. Its report says the script's file is the
     record.
   - `test_no_agent_but_the_builder_runs_checks` still passes.
9. **R9. The build skill.**
   - `allowed-tools` gains `factory.py gate *`.
   - The loop gains `gate` and `fix` branches. Both run in the background, as every agent step
     does.
   - Step 1 names the gate command, the gate file and the fix cap.
   - The WAIT gains a clause after the builder: `, the base branch's gate <command> runs on each
     build before any reviewer (up to 2 fixes a round)`, or `, with no gate configured`.
   - The rule tests pin each new rule.
10. **R10. A record of red gates in the history.**
    - `sdlc.py`'s `_factory_files()` counts FAIL attempts across `build/round-*.gate.md` as
      `gate_fail`, and only when some gate file exists.
    - `metrics.rework()` adds `gate_fail=<n>` to `Sdlc-Rework` when it is known. A trailer without
      the key reads as unknown, never as 0.
    - `skills/ship/factory.md` names the gate file as the script's record, beside the agents'
      evidence.
11. **R11. Shell helper.** `factory.py` gains a copy of `sdlc.py`'s `_sh()`, pinned by a test as
    `trackers/command.py`'s is. There is no `shell=True`, and `tests/test_windows.py` passes.
12. **R12. 072's land keeps a gate.** If `plugins/factory/skills/land/` exists on the base branch
    when this is built, land's post-rebase step runs `factory.py gate <NNN>` before its behaviour
    round. Otherwise the same duty falls to 072 when it rebases over this change, which its notes
    must say.
13. **R13. Docs.** The factory README ("Rounds that converge", the files list, Mechanism) and
    `AGENTS.md`'s factory paragraph describe the script gate, its file and the fix cap.
    `docs/REFERENCE.md` says the factory runs `[commands] check` from the base branch.
14. **R14. Old run folders still read.** A run folder from before this change still reads:
    reviewed rounds without a gate file are not a problem, and nothing asks them to be gated after
    the fact.
15. **R15. `./check.sh` passes.**

## Design

The loop becomes: build → snapshot → **gate** → review → verify → rework → snapshot → **gate** →
… → approve.

`verdicts` stays the only place that says what comes next. Whether a gate attempt still applies is
a content check: does its `Build:` hash match the report and the snapshot as they stand now? So
`verdicts` needs no state of its own, and still writes nothing. A fix appends to the report and is
snapshotted again, so it always earns a fresh gate attempt. A blocking decision answered before
review does the same.

`factory.py gate` is the second subprocess the factory runs, after `_claude()`. Like `_claude()`,
it is a function with no shell. The gate file sits beside the builder's reports, under `build/`.
Neither `build_round()` nor `raised_decisions()` reads it, since both take only stems ending in a
digit, and `_factory_files()` reads it only to count `gate_fail`.

A change can't edit the gate command, which comes from the base branch, but it can edit the script
that command runs (here `./check.sh`). This design accepts that gap and says so in the docs. A host
guards those files by listing them in `[review] sensitive`, as this repo lists `check.sh`. That
deepens the review and names the files at ship.

## Contracts touched

- **An `allowed-tools` rule that lets a command that writes run without asking.** `factory.py gate`
  runs a host command and writes in the change's folder. It is listed only in the build skill's
  rules, never in an `ALLOW_RULES`. The run's one WAIT names the command, so the person's yes
  covers it.
- **A skill's WAIT step.** The build question gains the gate clause. It still approves the same
  thing, one run.
- **Agents that judge have no Write; only the builder edits; nothing commits.** Unchanged. The gate
  is the script's, and `fix` resumes the builder.
- **`checks.md` only under `accept`.** The gate step runs `[commands] check`, never `checks.md`.
- **The scripts run on Windows; `factory.py` is self-contained.** A pinned `_sh()` copy,
  `encoding="utf-8"`, `newline="\n"` on every write.
- **The metrics trailer format.** Extended with `gate_fail`, never redefined. Old trailers read as
  unknown.
- **Base-branch reads.** The gate command joins `[review] sensitive` and `mode` as read from the
  base branch.

## Alternatives rejected

- **A red gate counting against `rounds`.** It would make `Sdlc-Rework`'s `rounds` mean two things.
  A red gate is cheap, so a separate small cap keeps "round" meaning "reviewed".
- **The gate's file under `reviews/round-<N>/`.** Sdlc's reviewer counting and the decision scan
  would both read it.
- **Running the base branch's copy of the gate script.** A command string doesn't name its files,
  so there is nothing general to copy. `[review] sensitive` is the host's lever.
- **Dropping `reviewer-behaviour`.** It still runs the spec's end-to-end path, which no gate does.
- **Retrying a failed gate before telling the builder.** A flaky gate is the host's to fix. One
  rerun after each fix is enough.

## Verification

- `uv run --group dev pytest tests/test_factory.py tests/test_skills.py tests/test_metrics.py
  tests/test_windows.py -q`. It covers:
  - the gate reading the base branch's command, with the checkout's ignored;
  - PASS and FAIL records, a timeout, and a changed tree failing;
  - the step sequence through `fix` and back to `review`, and the cap's stop;
  - no command, so no step;
  - old rounds without a gate file;
  - `max_runs()`;
  - the `_sh()` pin;
  - `gate_fail` counted only when a gate file exists;
  - the new rules and the WAIT clause.
- `./check.sh`: green.
- Manual: `factory.py gate` from the main checkout on a scratch change whose base branch's `check`
  is `exit 1`. Expect `GATE: FAIL`, `verdicts` → `fix`, and after a builder fix and a snapshot,
  `verdicts` → `gate`.
