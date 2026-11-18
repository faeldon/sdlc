---
id: 162
slug: lead-time
tier: 2
impact: minor
stage: shipped
created: 2026-11-18
updated: 2026-11-19
shipped: 2026-11-19
idea: [2026-11-18-94, 2026-11-18-106]
depends_on:
serves: [O4]
---

# Lead time, and where it goes, on every change

## Problem

The retrospective times a change by `elapsed`, which counts only the measured segments of its
stages. It leaves out the time a change waits before its first agent or edit, and the time it
sits finished and ready before anyone decides or lands it. On 2026-11-18, changes 139–148 showed a
median `elapsed` of 43.5 minutes against a real lead time of 250 (from their GitHub issues' open
times to their `Close` commits), and across 68 factory changes about half of all lead time was a
ready change waiting. None of it is recorded, so it was found only by a one-off analysis of
issues, transcripts and run files. `docs/RETRO-SCORECARD.md` makes lead time the Speed pillar's
headline (S1). And in a host on local numbering there is no issue to read a start time from, since
`intent.md`'s `created:` holds only a date (seed 2026-11-18-106).

## Outcome

- `sdlc.py new` records when a change was opened, to the minute, in a form every host has whether
  its numbers come from GitHub or locally.
- Close records on the `Close` commit, as `Sdlc-*` trailers extending the metrics contract, each
  change's lead time (opened to `Close`) and its breakdown: queued before the first agent or edit,
  agents working, idle between them, ready and waiting (from the approver's decision, or the
  ship stage for a change built by hand, to landing), and landing.
- `sdlc.py retro` reports each tier's and way of building's median and 85th-percentile lead
  time, and the shares of the breakdown, beside `elapsed`, which is unchanged.
- A change closed before this has no lead-time trailer, and retro counts it as unmeasured, never
  as zero.
- Recomputed for 139–157 from the same sources, the new figures match the hand-run analysis to
  within a minute or two.
- **Moves O4:** the retrospective's Speed headline is a recorded number, and the biggest lever
  (ready-waiting) shows up without a one-off analysis.

## Affected

`scripts/sdlc.py` (`new`, `retro`'s process figures), `scripts/closing.py` and
`scripts/metrics.py` (close's measure step and its trailers), `scripts/retro.py`, the report
template's process section, and the factory's run records it reads (agent sessions' times,
`runs/land-times.jsonl`). `docs/REFERENCE.md`'s *Metrics* and *Retrospectives* sections describe
the new trailers. Every host gets the new frontmatter line and trailers when it updates.

## Constraints

- The metrics trailer format is extended, never redefined; measuring never refuses (a failure is
  recorded as such, as `Sdlc-Coverage: none: <reason>` is).
- `metrics.py` stays pure: no subprocess, no import of `sdlc.py`.
- Frontmatter is read as text, never through YAML; `stamp_shipped` keeps editing lines in place.
- `closing.py` is in `[review] sensitive`, so the run is reviewed at full depth.
- Nothing local in the trailers: times and durations only, no paths.
- Must land before R6 (split `cmd_close` into steps), which would otherwise be redone.

## Open questions

- ~~Where the start time lives: a new `opened:` frontmatter line, or a time added to `created:`
  (which hosts' history already holds as a date).~~ Resolved: a new `opened:` line written by
  `new`, UTC to the minute (spec R1).
- ~~What counts as "agents working" for a change built by hand, with no factory sessions: the
  transcripts' active time, or leave the split to factory changes and record lead time alone.~~
  Resolved: the transcripts' turn and sub-agent time when read at close; without them, `lead` and
  `ready_wait` alone (spec R10).
- ~~Whether lead time's breakdown needs the agent transcripts at close (as `measure` reads today),
  or only the run files and git, so a close on another machine still records it.~~ Resolved: run
  files and git first, transcripts as the fallback (spec R8–R10).
