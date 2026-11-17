---
id: 123
slug: evidence-reads
tier: 2
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-18
shipped: 2026-11-18
idea:
depends_on:
fixes: [2026-11-17-90]
serves: [O3, O6]
---

# 123 — A passing check isn't stopped for a read without its exit

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

**2026-11-17-90:** the behaviour reviewer leaves `exit:` off read-only commands in its
`## Evidence`, and the one mend 109 allows doesn't cure it. On 2026-11-17, 119-ui-review-folders'
landing behaviour check gave `VERDICT: PASS`, but `grep … build/round-1.gate.md ; grep …
build/land-1.gate.md ; cmp …` had no `exit:` line. The mend's reply, again PASS, left it off
`cat .sdlc/work/119-ui-review-folders/plan.md`, so `land-verdicts` stopped the landing ("has no
`exit:` line") on a change that passed, and the person shipped it by hand. 108's builder (round 1,
a before-the-fix `pytest … | grep`) and earlier landings hit the same class. 109's spec chose a
mend over exempting reads, and this is the evidence against that choice.

## Outcome

- A change whose behaviour check passed is never stopped only because a command that changes
  nothing has no `exit:` line.
- A command that could change the tree, or whose result a claim rests on (a test run, a gate, a
  script that writes), still needs its `exit:`, and still stops or mends without one.
- Tests in `tests/test_factory.py` and `tests/test_land.py` pin both: 119's two real replies pass,
  and a test run without its exit still stops.
- **Moves O3:** a landing stops only for what needs the person.
- **Moves O6:** a passing change finishes without a hand ship.

## Affected

- **Area:** sdlc-factory's evidence rule.
- **Files & components:** `plugins/factory/scripts/factory.py` (`read_evidence()`,
  `land_verdict()`, `verdicts`), `plugins/factory/agents/reviewer-behaviour.md`,
  `plugins/factory/agents/builder.md`, `AGENTS.md`'s factory paragraph, `plugins/factory/README.md`
  and tests.
- **Downstream:** every factory build round and landing.
- **Overlaps:** 121 (landing-review-base) and 112 also edit `factory.py`.
- **Contracts:** a reply is never patched by the supervisor; the evidence rule is the factory's
  guard against a claim no one saw run.

## Constraints

- No claim may rest on a command whose result nobody recorded: an exemption covers only commands
  the script can tell are reads.
- The board's and `status`'s copies of the evidence parsing stay pinned.

## Open questions

- ~~Exempt reads in the script (which commands count as reads, and how is a pipeline judged?), or
  tighten the reviewer's prompt and keep the rule as is?~~ Resolved: in the script, by a closed
  allowlist that `is_read()` judges stage by stage, `jq` and `awk` included (spec R1, Design).
- ~~Does the builder's report get the same exemption as the behaviour check?~~ Resolved: yes, through the one parser (spec R6).
