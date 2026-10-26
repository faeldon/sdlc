---
name: health
description: Run every deterministic scan this repo defines (its configured scan command, plus the change pipeline's own audit) and present one consolidated report in which every finding carries a response tier — report, fix inline, or write an intent. Use at the start of a session, after a large change, or when the human asks how healthy the repo is. Read-only; it reports and routes, it never fixes. Use /sdlc:status instead for the change pipeline alone.
argument-hint: "[optional: an area to focus on]"
allowed-tools:
  - Read
  - Grep
  - Glob
  - 'Bash(cd *)'
  - 'Bash(git rev-parse *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py check *)'
  - 'Bash(echo *)'
disable-model-invocation: true
---

# Health — run every scan, then route what it finds

The scans are the deterministic detection Stage 6 of the repo's process asks for. What they lack is
**somewhere for findings to go**. Run one at a time, when someone remembers, they produce several
outputs and no decisions.

**The failure mode to avoid is a report nobody acts on.** A finding without a tier is an
observation, and observations evaporate into conversation. Every finding here ends in one of three
dispositions, or it does not belong in the report.

**This skill is also a budget.** One call, one consolidated picture. Do not open source files,
`.sdlc/work/` artifacts or the process doc to "add context" — Step 0's output, the findings table it
names and the defaults below are the whole input. Step 3 is the one exception.

**Read-only.** Never edit code, never write an artifact, never advance a `stage:`, never fix what a
scan reports. Anything that needs writing leaves through `/sdlc:intent` or the human's own hands.

## Step 0 — Run every scan (no confirmation needed)

```bash
cd "$(git rev-parse --show-toplevel)" && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config
```

If `commands.scan` is set, run it from the repo root and note its exit code. That's the input.
**The skill names the setting, not the scans** — which scans exist is the repo's business, so
adding one is an edit to the repo rather than a rewrite of this prose.

If it isn't set, the repo has configured no scans. Run the pipeline's own audit instead, and say in
the report that it is the only scan there is:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py check; echo "check exit: $?"
```

A scan is a different thing from the gate `/sdlc:ship` runs (`commands.check`), and from the
slower gate it runs when a changed path matches (`commands.build`). Both gates run on this diff and
answer "is the code correct", pass or fail. A scan (`commands.scan`) looks for drift across the
whole repo and produces findings, which is a different question with a different response. A
clean gate says nothing about what has been quietly drifting for three weeks.

**What each finding means** is the repo's to say. If the file `docs.health` names exists
(`.sdlc/HEALTH.md` unless the repo set another), read it once: it lists each finding a scan can
report, what it means, and the response tier it usually gets, and its blind spots say what a clean
scan can't vouch for. That table, plus the defaults in Step 1, is how every finding is routed. Without one, route by Step 1's
defaults and the finding's own text, and say the repo has no findings table.

A scan that couldn't reach what it scans should say so. If one reports clean having looked at
nothing, that is itself a finding: the worst outcome a health check can have.

## Step 1 — Assign a response tier to every finding

Use the process doc's Stage 6 tiers, or these three where it has none. Say **"response tier"**
explicitly: the same doc likely uses "Tier 0/1/2" for the *size of a change*, and the two scales
mix easily in one sentence.

1. **Report** — a one-off, already understood. Note it and move on.
2. **Fix inline** — mechanical and local. Fix it now, or hand it to the human as "fix this now".
3. **Write an intent** — structural, recurring, or it needs a decision. `/sdlc:intent`, re-entering
   Stage 1.

The findings table's defaults come first. These hold for every repo, and for anything the table
doesn't list; depart from any default with a reason rather than re-derive it each run:

| finding | default | why |
| --- | --- | --- |
| a `sdlc check` problem | 2 | the pipeline describing itself wrongly; fix before extending it |
| an open change ≥ 14 days old | 1 | an unmade decision. Say that's what it means rather than nagging |
| the same finding in several places | 3 | that's a convention not being followed, not several mistakes |
| **a scan that is itself wrong or blind** | **3** | always. A scan reporting clean because it looked at nothing is the worst outcome |

A clean scan is a finding too: say so in one line.

## Step 2 — Report

Compact, and in this order. Skip any heading with nothing under it — **a health check that always
prints two screens is a health check nobody reads.**

1. **One line of shape** — what's green, and where the findings bunch.
2. **Response tier 3** first, if any, then tier 2, then tier 1. Severity, not scan order: the human
   does not care which script noticed.
3. Each finding on one line: what it is, the tier, and a half-sentence of why that tier.

Report findings, not scan transcripts. If the scans are clean, the whole output is a few lines.

## Step 3 — Route the tier 3 findings

For each, end with a **proposed intent title** and `run /sdlc:intent to open it`. Do not open one —
the human decides what becomes committed work, and `/sdlc:intent` has its own gate.

Only here may you read one file to make a proposal concrete, and only the one the finding names. If
a tier 3 finding duplicates an open change in `sdlc check`'s `open` list, say so and drop it rather
than proposing a second intent for the same thing.

## Out of scope

- **Fixing anything.** `/sdlc:intent` owns opening changes, and a tier-2 edit is the human's to
  approve in the normal way.
- **Judging whether the code is right.** The scans check what they check, not whether logic is
  correct. That is the review's correctness pass, at Stage 5, with a diff in front of it.
- **The gate** (`commands.check`) — code correctness, which `/sdlc:ship` runs. This skill is about
  drift, not the repo's tests.
