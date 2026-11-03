---
id: 039
slug: factory-evidence-and-replay
kind: spec
created: 2026-11-04
updated: 2026-11-04
---

# 039 — The factory proves its builds, replays its reviewers, and reviews old code · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

This change builds seed 2026-11-03-12 only: the builder's evidence and a behaviour check. The
replay eval (-13) and the scheduled review (-14) were split off at this spec, the person's call,
and their agreed designs ride on those seeds (R8).

## Requirements

1. **R1. The builder shows its evidence.** `plugins/factory/agents/builder.md`: every round report
   ends with a `## Evidence` section: for each command it ran (the gate, the tests, anything a
   claim rests on) a `$ <command>` line, the tail of its output, and an `exit: <n>` line. The
   report claims no result its evidence doesn't show.
2. **R2. A report without it stops the run.** `factory.py verdicts` says `next: stop` when the
   newest `build/round-<N>.md` has no `## Evidence` section, none of its `$ ` lines, or a `$ ` line
   with no `exit:` line before the next `$ ` or the section's end; the problem names the file.
   Tests: a good report, a missing section, an empty one, a command without its exit.
3. **R3. A behaviour check.** A new reviewer role, `behaviour` (`REVIEWERS` gains it), with
   `plugins/factory/agents/reviewer-behaviour.md`: tools `Read, Grep, Glob, Bash`, writing nothing
   and never committing. It runs the repo's gate (`[commands] check` in `.sdlc/config.toml`, read
   by the agent) and the end-to-end path the spec or the intent's Approach describes, and returns
   what ran and what it printed. It reads `checks.md` and says, for each check, what it expects and
   why, but **never runs** those commands: ship's `accept` runs them with a person seeing them
   first. `VERDICT: CHANGES` with a `- CHANGE:` line when the gate or the path fails, through the
   verifier like any other. A test pins its tools and the never-run rule.
4. **R4. Its reply carries evidence too.** `verdicts` applies R2's rule to every
   `reviews/round-<N>/behaviour.md`, and stops on one without it.
5. **R5. Run at the full depth by default.** The default top-level `reviewers` becomes `["code",
   "security", "test", "behaviour"]`; `[light]` stays `["code"]`. A host that set `reviewers` keeps
   exactly its list; `load_config` accepts `behaviour`. `max_runs` with the defaults becomes 20, and
   the build skill's question, Step 1 and the README say so.
6. **R6. Ship reads it.** `/sdlc:ship` Step 0 names the builder's `## Evidence` and `behaviour.md`
   among the factory evidence it reads; a result claimed there is not one ship ran, and Step 1's
   gate still runs.
7. **R7. Docs.** `plugins/factory/README.md` (agents table, folder listing, defaults, `max_runs`
   20, the evidence rule) and `AGENTS.md`'s factory paragraph (reports carry their evidence; the
   behaviour check never runs `checks.md`).
8. **R8. The split recorded.** The intent's Outcome moves the eval and scheduled-review bullets
   under "Left for the next change". At ship: 2026-11-03-12 leaves through `idea:`;
   2026-11-03-13 loses `After: 2026-11-03-12` and gains `Agreed in 039's spec: the diff as text,
   files read at the commit with git show; caught means a CHANGE: on the bug's paths, each shown
   for the person to judge.`; 2026-11-03-14 gains `Agreed in 039's spec: an uncommitted report of
   proposed [bug] entries, filed by /sdlc:bug through inbox-commit behind its own WAIT; run when
   asked, with /schedule shown in the README.`

## Design

- **Evidence check.** `read_evidence(text) -> list[str]` (the problems): find `## Evidence`;
  within it, until the next `## `, walk the lines: a `$ ` line opens a command, an `exit: \d+` line
  closes the open one; fenced blocks are allowed, their content read the same way. `verdicts` calls
  it on `build/round-<built>.md` and each `behaviour.md`, adding to `problems`.
- **Role.** `REVIEWERS` and `ROLES` gain `behaviour`; `DEFAULTS["reviewers"]` grows to four;
  `read_rounds` reads `behaviour.md` like any reviewer; depth, verify, carry and `_factory_files()`
  treat it as one more reviewer, no special case.
- **The agent.** The reviewers' common sections (later rounds, `PREEXISTING`, decisions), no file
  written, a `## Evidence` in the builder's format, and a `## checks.md: read, never run` section.
- **Skill.** No new step: `behaviour` is in `missing` like any reviewer. Text changes in Step 0
  (the default reviewers), Step 1 (agents) and Step 2 (the question's reviewers come from `config`,
  unchanged in form).

## Contracts touched

- **Agents that judge have no `Write`:** the behaviour check has `Bash`, like the reviewers, told to
  write nothing.
- **`accept` never runs unasked:** the behaviour check never runs `checks.md`; a test pins the rule,
  and `test_no_skill_lets_accept_run_unasked` stands.
- **Nothing commits; `HEAD` is watched:** unchanged.
- **The factory's cached copy has no `sdlc.py`:** the agent reads `.sdlc/config.toml` itself;
  `factory.py` needs nothing of `sdlc.py`.
- **Metrics trailers extend, never redefine:** `Sdlc-Review` gains a `behaviour` row, same keys.
- **One WAIT, narrow `allowed-tools`:** the question's form and the rules are unchanged.

## Alternatives rejected

- **The behaviour check runs `checks.md`:** an agent wrote them, and the run would bypass the
  prompt `accept` exists for (the person's call).
- **Folding it into the test reviewer:** that one judges whether tests prove the requirements; this
  one runs the change. One agent doing both blurs which failed.
- **Evidence trusted as prose:** the claim-without-proof the seed is about; the check is mechanical.
- **Building the eval and the scheduled review here:** split, the person's call; their agreed
  designs ride on the seeds.

## Verification

- `./check.sh`, its exit code read directly.
- `uv run --group dev pytest tests/test_factory.py tests/test_skills.py -q`, cases for R2–R5.
- `factory.py config` shows the four reviewers; `factory.py start` shows `max_runs: 20`.
