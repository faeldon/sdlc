---
id: 105
slug: factory-run-records
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 105 — A factory run's records say what it did · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions, each checked in the code:

- The supervisor's draft comes from `factory.py agent --task spec`. Today `_task()` returns `None` as its target, and `cmd_agent()` sends the reply back only in its JSON (`"reply"`). `/sdlc-factory:spec` uses the `Agent` tool. In both cases a model copies the draft into `spec.md`, so a long draft is typed out a second time and can come out short.
- The draft's own frontmatter opens and closes with `---`, and the spec-writer marks its questions with another `---`. A bare `---` inside a code fence is text. Splitting on "the `---` line" by eye therefore fails on fenced drafts.
- The ledger line format (`LEDGER_RE`) has three copies: `factory.py`, `sdlc.py`'s `FACTORY_LEDGER_RE` and `board.py`'s `LEDGER_RE`. Tests pin all three. Readers that treat an unticked line as open: `factory.py` (`cmd_decisions`, `loop_state`, `land_signals`), `board.py` (`assumed`) and `sdlc.py` (`_factory_files`'s `defaults_open`). The approver and ship's `factory.md` read the ledger as prose.
- A fresh first build starts with `factory.py agent --task build` **before** any `verdicts --record`. While that build runs there may be no `runs/step.md` at all. `runs/builder.sessions` is appended when the session starts, which is the sign `board.py`'s `_progress()` already uses. No agent session outlives `AGENT_TIMEOUT` (3 hours).

R1. `factory.py agent <NNN> --task spec` writes the spec part of the spec-writer's reply, byte for byte, to `runs/spec-draft.md` in the change's folder. It writes the questions after the separator to `runs/spec-questions.md`. Its JSON names both (`to`, `questions`) and no longer carries the draft as `reply`. `--revise` and `--recheck` overwrite both files. `spec.md` is untouched. A test fails if `spec.md` changes, or if either file is missing after a run.

R2. The split is mechanical. The draft runs from the first line that is exactly `---` (the frontmatter's opening) up to the last line that is exactly `---` and sits outside a ``` or `~~~` fence after the frontmatter's closing line. The questions are everything after that line. With no such line, the whole reply from the frontmatter on is the draft and `questions` is null. Any text before the frontmatter goes into the JSON as `preamble` and never into the draft. A test with a draft holding a fenced block with a `---` line and a nested fence fails if the draft is cut at the fence or loses a line.

R3. A new `factory.py write-spec <NNN>` copies `runs/spec-draft.md` into `spec.md` byte for byte and writes nothing else. It refuses, writing nothing:
- with no draft;
- for a change that isn't Tier 2 at `stage: plan`;
- when `spec.md` is no longer the scaffold (two or more lines starting with `<`, `sdlc.py`'s `is_unfilled()` rule copied), so a person's text is never overwritten.

A test fails if the copy differs from the draft by one byte, or if any of the three refusals writes.

R4. `/sdlc-factory:build` and `/sdlc-factory:spec` show the draft by reading `runs/spec-draft.md` and `runs/spec-questions.md`. After the yes, each writes `spec.md` with `write-spec`, never with `Edit`. `/sdlc-factory:spec` drafts through `factory.py agent --task spec` (in the background, revisions through a ticked `R<n> (person, revise)` line in `decisions.md`, as build does) in place of the `Agent` tool. `tests/test_skills.py` fails on a rule nothing runs, a command with no rule, or an `Edit` of `spec.md` left in either skill's text.

R5. An agent raising a default that replaces an earlier one writes `- DECISION: [default] (supersedes D<n>) <text>`. `factory.py decisions` adds the new line as usual, with the `(supersedes D<n>)` prefix left out of its text, so the dedupe key stays the decision's own words. It then rewrites the named line, and only that line, from `- [ ] D<n> (…, default): …` to `- [x] D<n> (…, default): … → superseded by D<m>`. A test with the D2/D4 shape fails if D2 stays unticked, any other line changes, or a second run marks it twice.

R6. `decisions` marks nothing in these cases, adds the new default unmarked and lists it under `unmarked` with why:
- the named id doesn't exist;
- it isn't a `default`;
- it is already decided by the person;
- it is already superseded;
- it is the new line itself.

The command's exit stays 0. A test per case fails if a line is marked.

R7. `read_ledger()` gives each record `superseded_by` (the id, or null). `decided` is true only for a ticked line not superseded, and a new `open` is true only for an unticked line. `pending`, `assumed` (in `decisions` and `verdicts`), `land_signals()`'s open-decision signal and `agent --task decided` all read `open`/`decided`. `--decision D2` on a superseded D2 is refused. A test fails if a superseded default appears in `assumed`, blocks a landing, or is accepted as `--decision`.

R8. With no edit to their regexes, `board.py`'s `assumed` and `sdlc.py`'s `_factory_files()` `defaults_open` leave a superseded line out, and `defaults` still counts it. A test in `tests/test_board.py` and one in `tests/test_metrics.py`, each on a ledger holding a superseded line, fail otherwise.

R9. `builder.md` and each reviewer agent that documents `[default]` (`reviewer-code`, `-security`, `-ui`, `-ux`) say how to write `(supersedes D<n>)`, and that a ticked line with `→ decided:` is settled and can't be superseded. Ship's `skills/ship/factory.md`, `approver.md` and build's hand-back say a `→ superseded by D<m>` line is no assumption the build rests on, and show it as one line beside the default that replaced it. A test fails if `builder.md` lacks the syntax.

R10. `sdlc.py check` (and so `check --strict`) leaves out `plan.md is still the template at stage: build`, and only that problem, for a Tier 2 change whose factory run is in its live first build:
- `runs/builder.sessions` exists, last written less than `FACTORY_AGENT_TIMEOUT` (3 hours) ago;
- no `build/round-*.md` exists;
- no `runs/stopped.md` exists;
- `runs/step.md` is absent, or reads `STEP: build` with `ROUND:` empty or `1`.

Tests fail if:
- the problem shows during such a build;
- it hides with a report written, a stop recorded, a stale session (mtime past the window), or a step other than `build`;
- any other problem (`spec.md` unfilled, `intent.md` unfilled) is hidden.

R11. `sdlc.py`'s new copies (`FACTORY_STEP`, `FACTORY_STEP_RE`, `FACTORY_ROUND_RE`, `FACTORY_AGENT_TIMEOUT`) are pinned to `factory.py`'s in `test_sdlcs_copies_of_the_factorys_patterns_match_its_own`. That test fails if one drifts.

## Design

**The draft goes to a file (R1–R4).** In `_task()`, the `spec` branches (draft, `--revise`, `--recheck`) return `folder / "runs" / "spec-draft.md"` as their target. In `cmd_agent()`, a spec task goes through a new pure `split_draft(reply) -> (preamble, draft, questions)` before writing. Fences are tracked with the opening marker's character and length, as CommonMark closes them: a fence closes only on the same character, at least as long. `FENCE_RE` is reused for detection. The draft and the questions are written with `newline="\n"` and `encoding="utf-8"`. A spec task never appends (`append` False). The JSON for a spec task is `out` plus `questions` (the path, or null) and `preamble` (text, or null), and drops `reply`.

`cmd_write_spec()` goes beside `cmd_stage()`. It reads tier and stage with the existing `frontmatter()`, and checks the scaffold rule with a local `_scaffold(text)` copied from `sdlc.py`'s `is_unfilled()` (`PROMPT_RE`, `UNFILLED_THRESHOLD`), pinned by a test. It copies with `shutil.copyfile`, so nothing is decoded or re-joined. The module docstring's "writes only where its name says" list gains `write-spec` to `spec.md` and `agent --task spec` to `runs/spec-draft.md` and `runs/spec-questions.md`. The README's file tree gains both `runs/` files.

The skills change as follows:
- **Build.** Step 1 reads the two files rather than "the reply". Step 3 runs `factory.py write-spec <NNN> && factory.py stage <NNN> design && … build` in place of `Edit`. Striking the intent's resolved questions stays an `Edit` of `intent.md`.
- **Spec.** It drops `Agent`. It gains `Write` (for the revise line) and rules for `agent` and `write-spec`. Its Step 1 starts `agent --task spec` with `run_in_background` and picks the draft up from the files when the command exits.

**Superseded defaults (R5–R9).** Answering the open question: the agent raising a default names what it replaces. `decisions` records it and checks only the shape and that the named line can be superseded (R6). The new `SUPERSEDES_RE = ^\(supersedes (D\d+)\)\s*(.+)$` is applied to `RAISED_RE`'s text group. `cmd_decisions()` gathers the raised lines as now. For each new default with a prefix, it validates the target against the ledger *including the lines added in this same pass* (so D4 can name D2 raised in the same report). It rewrites `decisions.md` line by line, appending ` → superseded by D<m>` and ticking only the target. A rerun finds the target already superseded and the new text already known, so nothing changes (idempotent).

Marking by ticking keeps all three `LEDGER_RE` copies and their pins unchanged. It also makes every reader that counts unticked lines (board, metrics, the approver's and ship's reading) right without editing them. Only `factory.py`, which reads answers, needs `superseded_by`. `SUPERSEDED = " → superseded by "` sits beside `DECIDED`, and `read_ledger()` strips it from `text`. The new `open` key replaces the four `not d["decided"]` filters (lines 1094–1095, 1250–1251, 2294) and the `decided` check at 1965.

Only a default supersedes, and only a default. A blocking decision is answered by the person, and a ticked `→ decided:` is the person's word, which no agent overturns (builder.md already says never re-raise one). An agent that thinks a decided call is wrong raises a new `[blocking]` one.

**The first-build exemption (R10, R11).** Add `factory_first_build(folder) -> bool` in `sdlc.py`, next to `factory_stop()`. It applies R10's four conditions, reading `runs/step.md` through the copied regexes and never raising: an unreadable file is "not live". In `cmd_check`'s artifact loop, the `elif is_unfilled(folder / name)` branch for `plan.md` at `stage: build` skips the problem when it returns true. Nothing else in the loop changes. The time window is `FACTORY_AGENT_TIMEOUT = 3 * 3600`, `factory.py`'s `AGENT_TIMEOUT`: no first build can still be running after it. A build whose agent crashed is exempt for at most that long, and then the problem returns.

**Edge cases.**
- A reply with no frontmatter line at all: the draft is the whole reply, so the supervisor's check against the scaffold (prompts left, frontmatter) catches it and sends a recheck.
- A body `---` rule with no question trailer: the tail after it lands in `spec-questions.md`, where the person sees it. The templates forbid `---` rules, so the spec-writer's scaffold has none.
- A `write-spec` rerun after the first copy: refused, since `spec.md` is no longer the scaffold. `stage` then runs alone.

## Contracts touched

- **Agents that judge have no Write** (AGENTS.md, *The factory*). The spec-writer keeps `Read, Grep, Glob`. `factory.py agent` writes its reply, as it already writes every reviewer's. No agent gains a tool.
- **Mechanism vs. judgment.** Splitting the reply, copying the draft, checking a supersede target's shape and the liveness test are mechanical, in the scripts. Whether one default replaces another is a judgment, made by the agent that raises it, never matched by the script.
- **Writes before a WAIT.** Before the spec's WAIT, `agent` already writes `runs/<agent>.sessions` and `runs/costs.jsonl`. `runs/spec-draft.md` and `runs/spec-questions.md` are the same kind of uncommitted run record in the change's own folder, and decide nothing. `spec.md` is written only after the yes, by `write-spec`. `/sdlc-factory:spec` takes on build's existing named exception, the ticked `R<n> (person, revise)` line. This is the same exception, not a new one.
- **`sdlc` reads a run's files with copies of `factory.py`'s parsing, pinned by tests.** The new `FACTORY_STEP*` and `FACTORY_AGENT_TIMEOUT` copies are pinned in `tests/test_metrics.py`. `factory.py`'s copy of the scaffold rule is pinned to `sdlc.py`'s. `LEDGER_RE`'s three copies are unchanged.
- **`factory.py` never imports `sdlc.py`.** `write-spec` reimplements the scaffold rule rather than calling `sdlc.py`.
- **`check --strict` is a gate** (*Setup*: "A nudge in `status` is never a problem: `check --strict` is a gate"). Only the one problem is hidden, and only under four conditions with a time bound. Every other problem, and this one outside a live first build, still fails the gate.
- **Narrow `allowed-tools`.** Each new command gets a `Bash(...)` rule written as run, and `Agent` leaves the spec skill with its last use. Bash blocks stay plain `&&` chains, and the branching (split, refusals) lives in `factory.py`.
- **One WAIT per writing skill.** Both skills keep their single WAIT. `write-spec` runs after it.
- **Windows.** New writes pass `newline="\n"` and `encoding="utf-8"`. `copyfile` is binary. The mtime comparison is platform-neutral, and the new tests that need no fakes are marked `portable`.
- **Frontmatter is never round-tripped.** `write-spec` copies bytes. `decisions` edits one ledger line in place.

## Alternatives rejected

- **The script matches defaults by what they're about** (the intent's other option). Text similarity can't see that 086's D2 ("no badge on a shipped escalated card") and D4 ("keep `was ESCALATE`") contradict: they share almost no words. It would also be judgment in the mechanism, which AGENTS.md puts in skills and agents.
- **A third ledger state (`- [~]`) or an unticked line with a suffix.** Either needs all three `LEDGER_RE` copies and every reader changed in step. An unticked superseded line would also keep reading as an open assumption in every reader not taught about it. Ticking with a suffix is right for all of them as they stand.
- **Writing the whole reply, questions included, to `runs/spec-draft.md` and having the skill cut it.** That keeps the cut the intent's 2026-11-17-42 was about in a model's hands.
- **The skill reads the draft and `Write`s `spec.md` itself.** That is a model copying a long text again, the failure itself. A byte copy in the script can't come out short.
- **Copying the draft inside `stage <NNN> design`.** A command would then write a file its name doesn't say. `write-spec` names its write.
- **Exempting by `runs/step.md` alone** (the intent's wording). A fresh run's first build starts before the first `verdicts --record`, so there is no `step.md` while the plan is being written, and the problem would still show. `runs/builder.sessions`, which the board already reads as "first build under way", is the sign that holds. `step.md`, when present, still has to agree.
- **Exempting with no time bound.** A crashed first build would hide the problem for good, and the constraint says "only while a run is live".
- **Downgrading the problem to a warning.** `check --strict` would then pass a change with a template plan outside a run too, unless the downgrade carried the same liveness test. Leaving it out under that test is simpler and no weaker.

## Verification

```bash
uv run --group dev pytest -q tests/test_factory.py -k "spec_draft or write_spec or supersed or decisions"
uv run --group dev pytest -q tests/test_sdlc.py -k "first_build or unfilled_plan"
uv run --group dev pytest -q tests/test_board.py tests/test_metrics.py -k "supersed or copies"
uv run --group dev pytest -q tests/test_skills.py
uv run --group dev pytest -q -m portable
./check.sh
```

Healthy: every selected test passes, and `./check.sh` ends green (ruff, format, the full suite, `claude plugin validate --strict`). The `-k` filters are on the plan's test names. Each R above maps to at least one of them, named after its requirement.

By hand, in a scratch repo with a fake `claude` that replies with a draft holding a fenced block of YAML with a `---` line:
- `factory.py agent <NNN> --task spec` prints `to: .sdlc/work/<NNN>-…/runs/spec-draft.md`, and `diff` against the fake's draft section is empty.
- `factory.py write-spec <NNN>` makes `spec.md` match it byte for byte (`cmp` silent), and a second run is refused.
- `sdlc.py check --strict` during a faked first build (fresh `runs/builder.sessions`, no `build/round-1.md`) has no plan problem. With the sessions file's mtime set back four hours (`touch -t`), the problem is back.

