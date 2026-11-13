---
id: 053
slug: skill-evals
tier: 2
impact: patch
stage: shipped
created: 2026-11-12
updated: 2026-11-13
shipped: 2026-11-13
idea: 2026-11-12-6
depends_on:
serves: [O3]
---

# 053 — Behavioural evals for the core skills

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The gate proves `sdlc.py`'s mechanism, and `tests/test_skills.py` proves the skills' *text*: one
WAIT heading, narrow `allowed-tools`, phrases that must appear. Nothing runs a skill under a model,
so a regression in what a skill *does* (writing before its WAIT, pushing, putting agent
attribution in a commit, guessing instead of asking `config`, wording ship's question by hand
instead of from `preflight --question`) passes `./check.sh` and surfaces only later, as rework on
another change (`Sdlc-Rework`), an extra stop (`Sdlc-Extra`) or a bug a host files, by which time
the change that caused it has landed and been released. The factory has this for its reviewers
(`/sdlc-factory:eval` replays escaped bugs and scores them against the last run); the core skills,
which every host runs, have nothing like it.

## Outcome

- A `claude plugin eval` suite for the core skills, about eight cases to start, each a scratch
  host repo at a known stage (built with `tests/test_adoption.py`'s builder) with scripted replies,
  run once to stop at the WAIT and once approved through it.
- Cases cover what the skills must never do (write before the WAIT, push, agent attribution, guess
  instead of asking `config`, write on the base branch), their judgment calls (intent's tier, ship's
  question from `preflight --question`, finding dispositions, refusing while a finding is `open`),
  and cases seeded from skill bugs in the register and `Sdlc-Rework` history.
- Grading by repo state and `sdlc.py check` first, then the transcript's tool calls, and an LLM
  judge only for prose. Scores go under `.sdlc/reports/`, each run compared with the last.
- Run by hand behind one approval, never in `check.sh` or CI: at ship, offered only for the skills
  the diff touches (`landing_reach()` already knows when a diff reaches `skills/`, `agents/`,
  `guide/` or `templates/`); the full suite before a release; and when the default model changes.
- Cost kept down: runs scoped to the touched skills, stop-at-WAIT cases preferred, only failures
  rerun, and a cheaper model for cases that test rules.
- **Moves O3:** a skill change that would add a stop (writing before its WAIT, asking a question
  its tier doesn't need, a hand-worded question) is caught by the eval before it lands, so the
  stops-over-target figure for changes after a skill edit holds instead of rising.

## Affected

- **Area:** a new eval suite and its runner; the ship and release skills; `sdlc.py` for the reach
  and report readers the hooks need.
- **Files & components:** a new eval directory (its name a design call); `skills/ship/SKILL.md`,
  `skills/release/SKILL.md`; `scripts/sdlc.py` (`landing_reach()` reused, `preflight`'s parts);
  `tests/test_adoption.py`'s builder, shared rather than copied; `.sdlc/reports/`.
- **Downstream:** every change that edits a skill (the offer at ship), every release, and the
  people maintaining the plugin, who pay the eval's tokens. Hosts never run it: the suite tests the
  plugin itself.
- **Contracts:** ship's one WAIT (always Tier 2); "Only the named steps push"; narrow
  `allowed-tools`: the eval never in `ALLOW_RULES` and never run unasked, like `accept`; "Nothing
  about a project or a workspace": cases use neutral examples; `.sdlc/reports/` ignores itself, as
  the factory's eval already relies on.

## Constraints

- Ship keeps exactly one WAIT and its stop count: the eval offer goes inside the question
  `preflight --question` words, not as a new stop, or the change works against O3.
- Nothing runs the eval without the person's yes; nothing in `check.sh` or CI does.
- Reports stay under `.sdlc/reports/`, never committed; the register and docs are never written by
  the eval.
- A host never needs the eval to use the plugin; a missing `claude plugin eval` or no network is
  reported, never a failure of ship or release.
- Cases build their repos in scratch directories and never touch the checkout running them.

## Open questions

- ~~What does `claude plugin eval` support: scripted multi-turn replies, a sandboxed repo per case,
  reading the transcript's tool calls, choosing a model per case? Does the case format have to
  follow it, or does the eval wrap it?~~ Resolved: one prompt per isolated run, history files,
  scaffolds, `tool_used`/`regex`/`llm` graders and a model per case; the cases follow its format.
  Whether a slash command expands in `claude -p` is the spec's first verification step.
- ~~How does ship offer the run without adding a stop: a clause in its one question, a part of
  `preflight`, or a line in its report?~~ Resolved: a `preflight` part, run under the harness's
  own prompt like `accept`, and a `Skill evals:` note line read into the question.
- ~~Before a release, does a failing or stale eval refuse the release (as a deprecation does) or
  only advise?~~ Resolved: it advises, never refuses.
- ~~How is "the default model changed" detected: recorded in the last report and compared, or left
  to the person?~~ Resolved: the last full run's `claudeVersion` against `claude --version`, as a
  status nudge.
- ~~What does one run cost in tokens and minutes, and what budget is acceptable before ship stops
  offering it?~~ Resolved: `--max-cost-usd 5` scoped (`--runs 1`), 20 for the full suite
  (`--runs 3`); results give cost and duration, not tokens.
- ~~Where does the suite live and what is it called, so it isn't confused with
  `/sdlc-factory:eval`?~~ Resolved: `evals/` at the root and `sdlc.py evals`, with no skill.
- ~~How are cases seeded from `Sdlc-Rework` history and the register's bugs: by hand at first, or
  proposed by `/sdlc:retro`?~~ Resolved: by hand at first; retro proposing them is a later seed.
