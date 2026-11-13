---
id: 053
slug: skill-evals
kind: spec
created: 2026-11-12
updated: 2026-11-12
---

# 053 — Behavioural evals for the core skills · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1.** A suite of 6 cases (8 planned; R3's two moved on) in `evals/` at the repo root (the plugin's default eval directory),
   each a `prompt.md` whose body is a core skill's slash command, a `case.yaml` naming a
   `scaffold_script`, and `graders/`, each case tagged with the skill it tests (`ship`,
   `intent`…). `claude plugin eval . --scaffold` finds and loads all 8, and
   `claude plugin validate --strict` still passes with `evals/` present.
2. **R2.** Stop-at-WAIT cases for `/sdlc:intent`, `/sdlc:spec`, `/sdlc:ship`, `/sdlc:close`,
   `/sdlc:idea`, and `ship-open-finding` (refuses to commit while a finding is `open`), with
   Write, Edit and Bash granted so the negative graders mean something. Each asserts the skill ran
   `sdlc.py config`, that nothing its WAIT approves was written before it asked (no `new`, `ship`,
   `git commit`, `close` without `--check`, `inbox-commit`; no Write/Edit to a path but ship's
   `findings.md`), and that the last message carries the skill's literal question shape (ship's:
   the question `preflight --question` printed, run in that session).
3. **R3.** *Carried forward, with R5 and R6: see `notes.md`.* Approve-path cases `intent-approved` and `ship-approved` continue a
   `context.history_file` that ends at their stop case's question, with `yes` as the prompt, and
   assert the write ran exactly once (`new --worktree`; `ship` then one `git commit`), that no
   `git push` ran, and that the commit carries no `Co-Authored-By:` or "Generated with" line.
4. **R4.** Each case's scaffold builds its host repo in the empty workspace from a committed
   `fixture/` tree and plain `git`. A pytest test builds every fixture in a temp dir and asserts
   `sdlc.py check --strict` exits 0 there, so a script change that breaks a fixture fails the
   gate without running a model.
5. **R5.** *Carried forward with R3.* Each `history.jsonl` sits beside a `history.meta` recording the hash of the skill file
   it was captured against. A pytest test asserts each history's last assistant text ends with
   that skill's question shape; `sdlc.py cases` reports a history `stale` when its skill's hash
   has changed.
6. **R6.** *Carried forward with R3.* `sdlc.py capture-case <case> <run-dir>` writes a stop case's kept trace (a run made
   with `--keep-temp`) as the approve case's `history.jsonl` and `history.meta`; it refuses,
   saying so, when the run kept no trace. It is its own subcommand, so no rule for `cases`
   grants it.
7. **R7.** `sdlc.py cases [<NNN>]`, read-only, reports: `available` (the suite exists in this
   plugin's own repo; false in a host), the cases by tag, for a change the cases whose tags match
   `landing_reach()`'s skills for its diff, the last run's score, date, `claudeVersion` and cost,
   the current `claude --version`, and stale histories. It is not in `READ_ONLY`, which setup
   proposes to every host; ship's own `allowed-tools` grants it. No command name contains `eval`:
   the harness refuses any command line containing the word from a worktree session.
8. **R8.** `sdlc.py cases compare <dir>` reads a run's `aggregate-result.json` and the previous
   run's, and prints each case's score and delta, the regressions, and the `--case` arguments
   that rerun only the failures. It never writes; a missing or unreadable result is reported,
   never raised.
9. **R9.** `sdlc.py run-cases <NNN>|--full` runs `claude plugin eval` as a subprocess (never a
   shell) into a fresh run folder under `.sdlc/reports/`, which it creates with the `.gitignore`
   that ignores it, as `factory.py`'s `report-dir` does, pinned to it by a test. It always passes
   `--scaffold --no-publish --trust-plugin --ablation none --json` and an `--allow-tools` for each
   tool the cases grant (a case's `allowed_tools` alone grants nothing), plus `--tag … --runs 1
   --max-cost-usd 5` scoped to a change, or `--runs 3 --max-cost-usd 20` for the full suite.
   Results are never committed.
10. **R10.** In the plugin's own repo, when the diff reaches a skill with cases, `preflight` gets an
    `cases` part (R7's scope). Ship names `run-cases <NNN>` in prose (no `allowed-tools` rule, so the
    harness asks), runs it after the gate and before its review, and writes `Skill evals: ran,
    <score>` or `Skill evals: skipped, <why>` into `findings.md`'s note. A failing case is an
    Important correctness finding, `open`, naming the case. `ship_question()` adds `without the
    skill evals (<why>)` when skipped, and `sdlc.py ship` refuses a diff with a `cases` part whose
    note says neither, as it does for the fresh review. In a host, or a diff reaching no skill
    with cases, nothing changes.
11. **R11.** In the plugin's own repo, release's question carries the last full run's date and
    score, or `the skill evals not run since <change>`; release offers the full-suite command,
    named in prose, before its WAIT. It never refuses on it.
12. **R12.** `status` nudges, never as a problem, when the current `claude --version` differs from
    the last full run's `claudeVersion`: `skill evals last ran on Claude Code <v>; run the full
    suite`.
13. **R13.** No skill's `allowed-tools` grants `sdlc.py run-cases` or `sdlc.py capture-case`,
    and nothing in `check.sh` or `.github/workflows/` runs either;
    `test_no_skill_lets_accept_run_unasked` grows to cover both.
14. **R14.** A missing `claude`, an unavailable or early-access `plugin eval`, or exit 2 (cost cap)
    is reported as a skip with its reason, never a ship or release failure.
15. **R15.** Fixtures and cases use neutral examples (`reopen-drafts`) and pass
    `tests/test_nothing_local.py`.
16. **R16.** Nit 2026-10-26-3: `tests/test_adoption.py` gains a test that runs a change with
    `closes: [N]` from `new` to `close` through `uv run --script`, in a scratch repo with
    `archive.target = "github"` and a fake `gh` first on `PATH` answering the tracker's calls, and
    asserts the `Close` commit's message ends with `Closes #N` and the fake saw the issue labelled
    `landed`. Not `portable`: the fake is a shebang script.

## Design

**Where it lives.** `evals/` at the repo root, the eval default, so no `plugin.json` key. A host's
cached copy of the plugin carries `evals/` but never runs it: `cases` reports `available: false`
unless the main checkout is this plugin's own repo, decided as `_handoff()` and `reaches` already
decide it.

**Cases and fixtures.** `intent`, `intent-approved`, `spec`, `ship`, `ship-approved`,
`ship-open-finding`, `close`, `idea`. Fixtures: a set-up host with no change (intent, idea); a
Tier 2 change at `stage: plan` (spec); a built Tier 1 change (ship, ship-approved); the same with
an `open` finding (ship-open-finding); a shipped change (close). Each `fixture/` is a plain tree;
`evals/scaffold.sh`, shared by every `case.yaml`, copies it and makes its git history, with no
`uv` or `sdlc.py`, since scaffolds run outside the sandbox with a minimal `PATH`.

**Graders.** `tool_used` `min: 0, max: 0` for each write command (by `input_match` on the Bash
command) and for Write/Edit outside `findings.md` (a negative-lookahead regex); `tool_used`
`min: 1` for `sdlc.py config` and `preflight .* --question`; `regex` on `last_message` for the
question shape; `regex` on `trace` `not_contains` for attribution lines; an `llm` judge only for
intent's tier reasoning.

**Script.** `cases`, `cases compare`, `run-cases` and `capture-case` are new `sdlc.py`
subcommands. `cases` reuses `landing_reach()` through `_reaches()` over the change's diff against
its base; `compare` is a pure function over two JSON texts, beside `findings_trailer()`;
`claude --version` runs through the existing subprocess helper with `encoding="utf-8"`.

**Ship.** Step 1 gains a paragraph after the acceptance checks: with `preflight`'s `cases` part,
show its cases and command, then run it; it has no rule, so the harness prompt is the person's
consent, as for `accept`. Step 3 gains `cases compare` on the run's folder and the note line.
`findings_evals()` reads the note line as `findings_fresh()` does; `ship_question()` gains its
clause.

**Release.** `cmd_release`'s question data gains `cases` from R7; the skill shows it and offers the
full-suite command before its WAIT.

**Status.** `_nudges()` gains R12's line.

## Contracts touched

- **One WAIT per writing skill.** Ship and release keep one each. The eval run happens before the
  WAIT under the harness's own tool prompt, which metrics counts as `prompts`, beside stops and
  never in them, exactly as `accept`. No stop is added.
- **A skill's WAIT step (always Tier 2).** Ship's question gains a clause and ship a refusal over
  the note, mirroring the fresh review; what a yes approves doesn't change.
- **Narrow `allowed-tools`.** No rule for `run-cases` or `capture-case`. `cases` and
  `cases compare` write nothing, yet stay out of `READ_ONLY`, which setup proposes to every host.
- **Only the named steps push.** Nothing here pushes; the approve cases assert no skill does.
- **Nothing about a project.** Fixtures are neutral, and the test scans `evals/` with the rest of
  the repo.
- **Windows.** `claude --version` with `encoding="utf-8"`; `write_text(newline="\n")`; the fixture
  test is `portable`, while `scaffold.sh` is `sh`, as `_sh()` already assumes. R16's adoption test
  isn't `portable`, for its shebang fake, like `test_archive.py`'s.
- **Script dependencies.** None new.
- **`.sdlc/reports/` ignores itself.** Shared with the factory, through a copy pinned by a test.

## Alternatives rejected

- **A `/sdlc:evals` skill.** It would ship every host a command only this repo can use, and its
  name sits beside `/sdlc-factory:eval`. The person runs `sdlc.py run-cases`, or reaches it
  through ship and release.
- **Running in `check.sh` or CI.** Every run is a paid model call; the intent rules it out.
- **Scripting replies with `--resume` outside `plugin eval`.** It loses `plugin eval`'s sandbox,
  grading and cost cap.
- **Refusing a release on a stale eval.** Decided against: release advises.
- **Detecting the default model itself.** There is no reliable local reading; `claudeVersion` is
  in every result and changes when the default does.
- **Reusing `tests/test_adoption.py`'s Python builder in scaffolds.** Scaffolds run outside the
  sandbox with a minimal `PATH` and no Python environment; the pytest fixture test (R4) is where
  the builder's guarantees are checked instead.

## Verification

1. **Probe first, before building anything else:** a one-case run with `/sdlc:status` as the
   prompt must show the skill's own `sdlc.py status` call in the trace. Done 2026-11-12: it passed
   (3 turns, $0.14) once Bash was granted at run level and the no-plugin arm was off, which is
   why R9 passes `--allow-tools` and `--ablation none`.
2. `uv run --group dev pytest -q tests/test_evals.py tests/test_adoption.py`: the fixture, history,
   compare, reach, unasked and `closes:` adoption tests pass, and the compare and reach tests fail
   without their code.
3. `./check.sh` passes, `claude plugin validate --strict` included, with `evals/` present.
4. By hand, behind the harness prompt: `sdlc.py run-cases --full` scores all 8 cases;
   `sdlc.py cases compare` on its folder prints each score; a deliberately broken ship (a write moved above its
   WAIT, uncommitted) makes `ship` fail, and is reverted.
5. `sdlc.py preflight 053` on this change shows a `cases` part, since 053 itself edits
   `skills/ship/`.
