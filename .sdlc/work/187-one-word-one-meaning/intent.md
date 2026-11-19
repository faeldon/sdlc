---
id: 187
slug: one-word-one-meaning
tier: 2
impact: minor
stage: shipped
created: 2026-11-19
opened: 2026-11-19T13:00Z
updated: 2026-11-20
shipped: 2026-11-20
idea: 2026-11-19-62
depends_on: [184]
serves: [O1]
---

# 187 — One meaning per word, and sdlc.py check becomes sdlc.py vet

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Idea 2026-11-19-62: contributors meet the same words with several meanings. "Gate" is both the
host's check command and a person's approval at a WAIT (`docs/FEATURES.md` defines it as both);
"check" is `[commands] check` and `check.sh`, the acceptance checks in `checks.md`, and `sdlc.py
check`, the artifact audit; "build" is `stage: build`, the builder and its rounds, and
`commands.build`, the slower gate. The person, reading the board and the factory's reports today,
asked whether the gate was the tests, whether `sdlc.py check` was an audit agent, and whether there
was a fast and a slow check, each a question the words made.

The person also decided: "rename the command `sdlc.py check` to `sdlc.py validate` (with
`--strict`), with no shim: few hosts use it and skills are what run it, so its callers (skills,
their allowed-tools rules, READ_ONLY and the permission rule setup writes, tests, docs) move in the
same change." The person then chose another word over `validate`, which would carry validation's
meaning, then `lint`, and then: "I changed my mind. Let's use bet. I mean vet." `vet` names a
careful check of files against rules (as `go vet` does), which is what this does to a change's
folder, and collides with nothing: `lint` already means ruff's lint inside `./check.sh`.

The person also decided, discussing the factory's verifier: "verification" is software
engineering's word for checking a product against its specification, but the verifier only
judges whether each reviewer's requested change is real before the builder reworks it. Rename it
"arbiter" and keep it separate from the approver, which decides the whole change at the end.
The person then decided: "Let's use the term verifier to mean the umbrella, and validation to mean
the milestone and project outcome." Read as: "verification" is the umbrella (did we build it
right: the gate's tests, the reviewers and the acceptance checks together), "validation" is the
check of milestones and the product's outcomes (did we build the right thing, which the
retrospective judges), and nothing is named "the verifier" any more.

Three style nits come in: 2026-11-19-41 (an AGENTS.md factory-paragraph line past 100 columns),
-44 (a test docstring that cites "179 R1") and -52 (`# 183` comments in `tests/test_skills.py`).

## Outcome

- "Gate" means only the host's commands; a person's yes is an "approval" (its step a WAIT);
  "acceptance checks" always keeps "acceptance", shortened to "acceptance" after a doc's first use
  and on labels, and "accept" never means a person's yes (the landing question's "accepted as
  shown" becomes "approved as shown"); `checks.md` keeps its name, the glossary saying it holds the
  acceptance checks; `commands.build` is "the slow gate"; the arbiter "weighs the findings". `docs/FEATURES.md` defines each once, and its term test fails on a doc that
  uses a word in a meaning it no longer has.
- `sdlc.py check` is `sdlc.py vet` (and `vet --strict`), everywhere it is called, with no
  alias left.
- The factory's verifier is the arbiter: its agent (`sdlc-factory:arbiter`), its tasks, the
  board's step label and every doc and skill say so. Its record file, `reviews/round-N/verified.md`,
  keeps its name, since history holds it and core reads it through `factory_records.py`.
- `docs/FEATURES.md` defines "verification" as that umbrella and "validation" as the milestones'
  and outcomes' check, and no doc uses either word otherwise.
- The board says the same words. Its build and landing step tracks read `arbitrate` for `verify`,
  its round chip `arbiter: kept N · dropped N`, its landing track `acceptance` for `checks`, and
  its card `acceptance: N` (with how many passed once they ran) for `N check(s)`. Its gate badge
  keeps `gate green` / `gate red`, and shows the command the gate ran and its result (`./check.sh:
  3309 passed, exit 0`, or the failing line), so a reader sees what the gate is without the label
  claiming it is only tests.
- The three nits are fixed.
- **Moves O1:** a newcomer reading the docs, the board or a report meets one meaning per word.

## Affected

- **Area:** docs, skills, the scripts' messages, and one command.
- **Files & components:** `scripts/sdlc.py` (the command list, `READ_ONLY`, `ALLOW_RULES`),
  `skills/status/`, `skills/ship/`, `skills/spec/` (their bash blocks and `allowed-tools`),
  `docs/FEATURES.md` and its test, `docs/REFERENCE.md`, `docs/CONTRIBUTING.md`, `AGENTS.md`,
  README.md, the factory's README and prompts, the tests that run `check --strict`;
  `plugins/factory/agents/verifier.md` and the `verify` and `land-verify` tasks in `factory.py`
  and `landing.py`, and the board's step label.
- **Downstream:** every host: skills now call `sdlc.py vet`, which a host's settings haven't
  allow-listed until setup proposes the rule; a host's CI that runs `sdlc.py check` breaks.
- **Contracts:** a command removed with no shim, which `.sdlc/deprecations.toml` and the release
  impact must say; `[commands] check` and `check.sh` keep their names.

## Constraints

- No file, config key or other command is renamed.
- It lands after the rest of wave 4, so its wording covers what they added.

## Open questions

- ~~What release impact does removing `check` with no shim carry: major, or minor given how few
  hosts use it?~~ Resolved: minor, the person's call (spec R23).
- ~~Does `drift` or setup propose the `sdlc.py vet *` permission rule to a host on update?~~
  Resolved: setup does, through readiness's `permissions.missing` (spec R3).
