---
id: 137
slug: approver-weighs-defaults
tier: 2
impact: minor
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea: [2026-11-18-13, 2026-11-18-15]
depends_on:
serves: [O6]
---

# 137 — The approver weighs the defaults it can, and the person decides the rest one at a time, with the alternatives in view

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

When an agent makes a call it can leave to a default, it raises a `- DECISION: [default] …` line,
and `factory.py decisions` gathers it into the change's `decisions.md` as an unticked line. The
approver escalates while any such default is unconfirmed (`plugins/factory/agents/approver.md`,
and the build skill's account: "the approver escalates while any is unconfirmed"). So an
escalation often says nothing more than "these defaults were assumed". 129's `decision.md` on
2026-11-18 escalated with every reviewer at PASS, solely because D1 and D2 were unticked. Status's
"What needs me" listed 127 as "confirm 3 defaults" and 128 as "confirm 1 default".

Confirming one is hard to judge. The ledger line holds the agent's question and its default, but
not the alternatives it weighed, why it chose that default, or what the code looks like either
way. The person has to rebuild that context from the spec, the diff and the rounds, for each
default and each change. The only place that asks is the supervisor, for blocking decisions.
Defaults reach the person as lines in `decision.md` and in ship's or the landing's question.
Nothing walks through them.

## Outcome

- Each default the build assumed carries its alternatives in the ledger, with the default first:
  each option with a line on its pros and cons, and why the default was chosen. A test files an
  agent's `- DECISION: [default]` line with options, and finds them in `decisions.md` in that
  shape.
- The approver weighs each unticked default itself. One it can settle from the spec, the code and
  the rounds is marked as the approver's call with its reason, and no longer escalates on its own.
  One it can't is escalated with the alternatives shown. A test gives the approver's reply both
  kinds and checks what the ledger and `decision.md` record.
- A new skill, `/sdlc-factory:decide NNN`, walks the person through one change's open decisions
  and confirmations, one at a time. For each it shows the background, the default, the
  alternatives and why the default was chosen, and asks in a dialog with the default first. It
  records each answer in `decisions.md` as the supervisor already does (`→ decided:`), and says
  what the change needs next.
- A default the approver settled is never counted as the person's word. Ship, the landing's
  question and `measure` still tell an approver's call from one the person made.
- **Moves O6:** a factory change escalates only for what needs the person, and each of those
  decisions takes less of their time.

## Affected

- **Area:** the factory's decision ledger, its approver, and a new skill, in `plugins/factory/`.
- **Files & components:**
  - `factory.py`: `decisions`, which parses `- DECISION:` lines and writes the ledger;
    `land-check`'s "an open decision" signal; the stop reading `verdicts --record` writes.
  - `agents/approver.md` and the prompts that teach agents the `- DECISION:` line.
  - A new `skills/decide/SKILL.md`.
  - `plugins/factory/README.md`, plus tests in `tests/test_factory.py` and `tests/test_skills.py`.
- **Downstream:**
  - `sdlc.py` and the board read `decisions.md` through pinned copies of the factory's parsing:
    the board's "confirm N defaults", status's "What needs me", ship's `factory.md` branch, and
    `measure`'s `defaults=`/`defaults_open=` in `Sdlc-Rework`.
  - A new ledger mark for "settled by the approver" must read the same in each.
  - The landing passes itself only with no open decision, so what counts as open changes when a
    batch lands without asking.
  - Depends on no open change. 136 also reads the approver's escalations, so the two should agree
    on what an escalation means.
- **Contracts:**
  - Agents that judge have no Write: the approver's verdict reaches the ledger only through the
    script.
  - Every skill that writes has one WAIT that asks in a dialog (`tests/test_skills.py`).
  - `decisions` stays the only writer of the ledger's shape.
  - The factory never imports `sdlc.py`.

## Constraints

- A ticked line is the person's word, and nothing marks it for them. An approver's settlement is
  its own mark, never `[x] … → decided:`.
- A ledger written before this change, with no alternatives, still reads, and `decide` asks it
  with the default alone.
- The supervisor's `decide` step for blocking decisions keeps working while the new skill exists.
  Whether they share code is the spec's call.
- No skill named `resolve`: that already means rebasing a conflict.

## Open questions

- ~~May the approver settle a default at all, or only recommend one, leaving every default for the
  person but sorted, with alternatives?~~ Resolved: it may settle, as its own mark, never the
  person's (spec R5–R7).
- ~~Does an approver-settled default still keep the landing from passing itself, or does only an
  escalated one?~~ Resolved: it still does; a settled default is a landing signal (spec R9).
- ~~Should `decide` take every change with open decisions in one run, one change at a time, or only
  the one named?~~ Resolved: only the one named (spec R15).
- ~~Where do the alternatives come from: the agent that raised the default, required to give two or
  more, or the approver when it can't settle one?~~ Resolved: the raising agent, two to four, its
  own first; the approver fills a bare one when it escalates it (spec R1, R3–R5).
- ~~Does `/sdlc:ship` show the alternatives too, or is `decide` the only place?~~ Resolved: ship
  shows them too (spec R12).
