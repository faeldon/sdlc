---
id: 059
slug: lean-retro-release-output
tier: 2
impact: patch
stage: shipped
created: 2026-11-16
updated: 2026-11-16
shipped: 2026-11-16
idea: 2026-10-26-8
depends_on:
serves: none
---

# 059 — Leave each change's measured numbers out of retro's and release's output

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`sdlc.py unreleased`, `release --check` and `retro` print, for every closed change, the full
`metrics` blob `measure` parsed from its `Close` commit's `Sdlc-*` trailers: totals, each stage's
line, rework, fixes. `retro` prints it for each dropped change too. Neither skill needs it:
`/sdlc:release` reads none of it, and `/sdlc:retro` reads the top-level `metrics` summary,
`metrics_summary()`'s medians per tier and mode (`scripts/sdlc.py:6297`), not each change's blob.

Today `unreleased` prints 105 KB for the 17 unreleased changes since v1.7.0, and 66 KB of it is
the per-change `metrics` as printed (indented): about 16,000 tokens, which a release reads twice (from `unreleased`,
then `release --check`). The retrospective of 2026-10-26 measured the same at about 39 KB of
retro's 78 KB. It enters the model's context and stays for the session, grows with every change
closed since the last release or retro, so a late release pays the most, and crowds out the
titles, impacts and problems the skills actually write from.

Raised by the retrospective of 2026-10-26; M9's next seed ("A run reads what it needs"), after
056 and 058.

## Outcome

- `unreleased`, `release --check` and `retro` print no per-change `metrics` blob by default; a
  flag puts it back. Tests pin both.
- `retro`'s top-level `metrics` summary, `dropped_cost`, the bug counts and every other aggregate
  are unchanged, computed before anything is left out; a test compares the summary with and
  without the flag.
- `unreleased` for the current 17 changes is at most 45 KB, from 105 KB, the figures recorded in
  the notes.
- The retro and release skills still find everything they read, shown by checking each skill's
  text against the output's keys.
- Four open nits on the script, taken in at spec: 2026-10-25-15 (status walks history once),
  2026-10-26-2 (`mark_issues` skips issues already marked), 2026-10-27-8 (`_inbox_commit`'s
  parameters), 2026-11-12-1 (a hotspot says when its file is gone).

## Affected

- **Area:** the script's release and retro output.
- **Files & components:** `scripts/sdlc.py` (`cmd_unreleased()`, `cmd_release()`'s check output,
  `retro()`, their argparse flags); `skills/retro/SKILL.md` and `skills/release/SKILL.md` only if
  either names the per-change field; `tests/test_retro.py` and the release/unreleased tests;
  `docs/REFERENCE.md` and `AGENTS.md` where they describe the output.
- **Downstream:** the retro and release skills, which read this JSON; anyone else reading
  `unreleased` or `retro` output, possibly the factory's eval or review. The `Close` commits'
  trailers are untouched: only what's printed changes.
- **Contracts:** the metrics trailer format is a contract ("extend them, never redefine"), not
  touched; `test_release_publish_and_measuring_never_read_the_register`; `retro` isn't in
  `READ_ONLY`; the Windows rules for any new code.

## Constraints

- Every aggregate is still computed from the full blobs: leaving them out is a printing decision
  made last, never a reason to parse less.
- The trailers on `Close` commits and `metrics.py`'s parsing don't change.
- The full data stays one flag away: nothing is lost, only left out by default.
- No skill's question or WAIT changes.

## Open questions

- ~~What is the flag called (`--metrics`, `--full`), and do all three commands share it?~~
  Resolved: `--metrics`, on all three.
- ~~Are per-change `findings` and other per-change keys worth trimming too, or `metrics`
  alone?~~ Resolved: `metrics` alone; `findings` is 5 KB and retro's bug pairing reads it.
- ~~Does anything besides the two skills read per-change `metrics` from this output: the
  factory's eval or review copies, `cmd_publish`, the tests?~~ Resolved: no; the tests read the
  functions' return values, which keep it.
- ~~Should `release --check` drop the change list entirely, when `unreleased` was just read?~~
  Resolved: no; without metrics the list is small, and it shows what the release holds.
- ~~Is a small per-change summary (stops, elapsed) worth keeping in place of the blob?~~
  Resolved: no; no skill reads one, and `--metrics` gives the whole.
