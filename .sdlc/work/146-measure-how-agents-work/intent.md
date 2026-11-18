---
id: 146
slug: measure-how-agents-work
tier: 2
impact: minor
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea:
depends_on: [139]
serves: [O4]
---

# 146 — Measure how factory agents work, not only how long

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Close's `measure` step already reads each agent session's transcript, and writes time, tokens and
stops as `Sdlc-Role:` and `Sdlc-Stage:` trailers, which retro reads. It records nothing about
**how** an agent worked. On 2026-11-18, finding out took reading a transcript by hand: 139's Fable
builder used no Read or Edit tool, reading with `sed`/`grep` and editing by inline Python
`str.replace` 28 times (once leaving `sdlc.py` unparseable), and twice had a piped `pytest` go to
the background, the pattern behind bug 2026-11-18-26; 141's Fable builder cost $11.09 against
$0.99–6.04 for the Opus builders that day. Seed 2026-11-18-40 (the Fable experiment) needs exactly
these comparisons, and so does knowing whether a prompt rule holds, such as 140's "nothing in the
background". The transcripts that show it live on one machine and are deleted after about 30
days, so what isn't measured at close is lost.

The person's own words: "Maybe also include the tools it calls." And on observing habits as prose:
"Maybe we should convert it to actual measurable behaviors that we really care about. I'm worried
that those pros will always repeat every time, and that storage will also be a design issue." So
behaviour is measured as named counts, not written up.

## Outcome

- Each `Sdlc-Role:` trailer gains counts read from that role's transcripts: the tools called, by
  name and count, and a small set of named behaviours that matter, each a count. The starting set:
  `edits=` (Edit/Write tool calls), `shell_edits=` (Bash commands that write files), `bg=`
  (commands sent to the background), `tool_errors=`, `test_runs=`, and `broke=` (a check or test
  run that fails to even parse or import right after an edit). A test feeds `measure` a fixture
  transcript with one of each and finds every count on the trailer.
- They are counted in the pass `measure` already makes over each transcript, never a second; a
  failure to count is no stop, as `Sdlc-Coverage: none: …` is today.
- Retro reports them by role and by model (from `runs/costs.jsonl`), so it can compare, say, Fable
  builders with Opus builders, and see a prompt rule's effect (`bg=` before and after 140). A test
  builds two closed changes and finds the comparison in the report.
- No prose about an agent's habits is written or stored: a behaviour worth watching is added as a
  named count.
- **Moves O4:** a retro says from evidence which model or prompt makes a factory role work better,
  not from one hand reading of a transcript.

## Affected

`scripts/sdlc.py` (`measure`, at close), `scripts/metrics.py` (the trailer format, a contract to
extend, never redefine), `scripts/retro.py` (what it reads and reports), `docs/REFERENCE.md`'s
*Metrics*, and `tests/test_metrics.py` and `tests/test_retro.py`. Every host whose factory runs
close, and every retro; reading old `Close` commits must not change. It waits on 139, which changes
`cmd_close()`, where `measure` runs.

## Constraints

- Numbers and names only on a commit: never a prompt, a reply, a path or a command.
- Transcripts stay local: read where they are, never copied or committed (`test_nothing_local`).
- Metrics never refuse or noticeably slow a close: one pass over each transcript.
- The trailer contract is extended, never redefined; an old `Close` commit reads the same.
- `metrics.py` stays pure: no subprocess, no import of `sdlc.py`.

## Open questions

- ~~Which behaviours make the starting set, and which are left out: is each one tied to a decision
  retro would make (a model, a prompt rule, a bug's fix)?~~ Resolved: the six named, each tied to
  a retro decision (spec R1–R6).
- ~~How is a shell edit, a test run, or a broken build recognised: by the command, as `is_read()`
  does for reads, or by the tool's own result?~~ Resolved: shell edits and test runs by named
  command shapes, `bg=` by the tool's result, `broke=` by the output after an edit (spec R3–R6).
- ~~Is the batch already closing (139–143) backfilled: can retro, or a one-off `measure --recount
  NNN`, add the counts for closed changes whose transcripts still exist? Seed 2026-11-18-40's
  comparison depends on it.~~ Resolved: no backfill in this change; the spec was approved without
  one.
- ~~Is "the tools called" every tool's count, or only the top few, to keep the trailer short?~~
  Resolved: every tool, on its own `Sdlc-Calls` line (spec R7).
