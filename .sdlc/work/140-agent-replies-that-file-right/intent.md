---
id: 140
slug: agent-replies-that-file-right
tier: 2
impact: patch
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea:
depends_on:
fixes: [2026-11-18-26]
serves: [O6]
---

# 140 — An agent's verdict is filed from the reply that holds it, and a reply's shape stops costing a mend

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

From 2026-11-18-26: "136's code and test reviewers (round 1, 2026-11-18) each started their own
background wait on ./check.sh, gave VERDICT: PASS, then were woken by that wait's notice and
replied again ('my verdict stands'). `factory.py agent` files only the session's last reply, so
reviews/round-1/code.md and test.md held just that note, and `verdicts` stopped the run as
`rerun`, not `mend`, losing both reviews."

The same day showed the wider tax. The script reads every reply mechanically, and a reply in the
wrong shape cost a mend or a stop nine times: 138's approver twice and 137's (a sentence before
`DECISION:`), 136's code reviewer (`Status: …` before `VERDICT:`), 137's ux reviewer (a
preamble), 125's, 131's and 135's behaviour checks (an `## Evidence` command without `exit:`),
and 136's rerun. Each mend is another agent run, and a second bad reply in a round is a stop the
person must clear.

## Outcome

- `factory.py agent` files the reply that holds the verdict, decision or report; a later reply in
  the same session (a background task's notice answered) never replaces it. A test runs a
  stand-in agent that replies twice and finds the first, verdict-bearing reply filed.
- A reply whose verdict or decision line follows only prose is read as that verdict, the prose
  kept in the file, without a mend; a reply with no verdict is still a stop. A test feeds
  `preamble()`'s cases through `verdicts` and `land-verdicts`.
- No reviewer runs the base branch's `[commands] check` itself: the script's gate already ran it,
  and the reviewer prompts say so.
- **Moves O6:** a factory run stops for what a reviewer found, not for how its reply was laid out.

## Affected

`plugins/factory/scripts/factory.py` (`cmd_agent`, `preamble()`, `decision_preamble()`,
`read_evidence()`, `verdicts`, `land-verdicts`), `plugins/factory/agents/*.md`, the board's
copies of the parsing in `scripts/board.py` (pinned by `tests/test_board.py`), and
`tests/test_factory.py`. Every factory host's runs.

## Constraints

- Only the script judges a reply; never patch a verdict.
- A mend stays once a round for each role.
- The board's copies of the parsing change with `factory.py`'s, pinned by tests.
- `is_read()`'s rules for `exit:` are unchanged.

## Open questions

- ~~Is "the reply that holds the verdict" the first such reply in the session, or the last?~~
  Resolved: the last reply that holds an answer (spec R2, *First or last*).
- ~~Should a missing `exit:` on a read-only command still need a mend, or be judged by
  `is_read()` alone?~~ Resolved: `read_evidence()` already judges a read by `is_read()` alone; no
  change (spec, *Alternatives rejected*).
