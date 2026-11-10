---
id: 047
slug: cut-extra-stops
kind: spec
created: 2026-11-10
updated: 2026-11-10
---

# 047 — Cut the stops a change makes between its gates · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

What the last 14 changes' 53 extra stops were (108 typed entries, 55 gate answers): 19 after the
gate (almost all "plan" or "plan and build" after spec's or a Tier 1 intent's yes, once in every
change), 15 harness entries (12 background-task notices, 3 compaction summaries), 10 unprompted or
answers to a prose question, 7 revisions at a gate, one `/reload-plugins`, one interrupt. "Tool
loaded." never lands as a user entry in a saved transcript. All 66 `EnterPlanMode` calls were
allowed by config, unasked.

1. **Harness entries are not stops.** `read_events` reads a user entry whose `origin.kind` is
   `task-notification`, or that has `isCompactSummary: true`, as a `harness` event, never a
   `human` one: no stop, no response or away time, and it doesn't end the agent's wait. A test
   feeds both shapes and asserts `extra=0`, unchanged clocks and `harness=2`.
2. **Other slash commands are not stops.** A typed `<command-name>/…` that isn't one of the
   plugins' skills (`/reload-plugins`, `/compact`) is counted as `command`, not a stop, as the
   plugins' own skills already aren't; its wait still counts as the person's response. A test
   asserts it.
3. **Each remaining extra stop gets a kind, by shape alone:** `after_gate` (inside a gated skill's
   span, after the stop picked as its gate); `revise` (inside a span, before the gate, a `revise`
   reply); `asked` (the agent's last text before it ended with `?`); `interrupt` (the entry is
   `[Request interrupted by user…`); `unprompted` (anything else). No text leaves `read_events`:
   `asked` is a bool on the `human` event, and a test asserts the event carries no string beyond
   its classes.
4. **A trailer records them.** Close writes one `Sdlc-Extra: <stage> after_gate=<n> revise=<n>
   asked=<n> unprompted=<n> interrupt=<n> harness=<n> command=<n>` line per stage that has any.
   `Sdlc-Stage`'s `extra=` equals the sum of the five person kinds, and `Sdlc-Totals` carries
   `harness=` and `command=` always, so a change with no extra stop still reads as counted this
   way. `parse_trailers` reads it; a round-trip test pins it.
5. **Old commits read as unclassified.** A `Close` commit with no `harness=` on `Sdlc-Totals` is
   not counted as zero kinds; its `extra=` stays what it was, an upper bound that includes harness
   entries.
6. **Retro reports the kinds.** `sdlc.py retro`'s metrics gain an `extra` report: per kind, the
   total and the changes it came from, and `recorded`, the commits carrying `Sdlc-Extra`, beside
   `_prompt_report()`. A test with a window mixing old and new commits.
7. **Spec starts plan mode.** Its WAIT question becomes `Write this as
   .sdlc/work/NNN-<slug>/spec.md, advance the change to stage: design, update its issue and then
   start plan mode? (yes / revise a requirement / rethink the design)`; Step 6 calls
   `EnterPlanMode` after `sync`; `EnterPlanMode` joins its `allowed-tools`. The plan is still
   approved at plan mode's own exit: the gate count is unchanged.
8. **A Tier 1 intent offers it in its question.** Tier 1's WAIT question ends `…off <git.base>,
   then start plan mode? (yes / yes, without plan mode / change the tier / edit a section)`; on
   yes, Step 6 calls `EnterPlanMode` once the session is in the worktree. Tier 2's is unchanged
   (`/sdlc:spec` is next). `EnterPlanMode` joins its `allowed-tools`.
9. **Skill tests pin it.** A test asserts both skills name `EnterPlanMode` in `allowed-tools` and
   in a step after their WAIT, and that their WAIT question says `plan mode`.
10. **The docs tell the truth.** `metrics.py`'s docstring replaces the "Tool loaded." caveat with
    the harness entries it now reads; `docs/REFERENCE.md` *Metrics* documents `Sdlc-Extra`, its
    kinds, and that `harness` and `command` entries are not stops; the intent and spec skills'
    "do not continue" lines say plan mode is where they hand over, and that it approves nothing by
    itself.

## Design

`read_events` already looks at each user entry's own keys (`isMeta`, `permissionMode`). The
harness check sits beside the `isMeta` skip and emits `{"kind": "harness"}`. The command check
widens the `SKILL_RE` test: any `<command-name>/` sets `command: True`, and a new `plugin: bool`
keeps stage detection on the plugins' skills alone. `asked` comes from the last assistant text
block seen before the entry, running state like `uses`.

`summarize`: a `harness` event bumps the stage's `harness` and nothing else; a non-plugin command
bumps `command` and adds no stop. `close_span()`, which already picks the gate, gives every other
stop in the span its kind (`after_gate` after the pick, `revise` for revise replies before it,
`asked` or `unprompted` for the rest); stops outside a span get `asked`, `unprompted` or
`interrupt`. `trailers()` writes `Sdlc-Extra` after `Sdlc-Prompt`. `sdlc.py`'s `metrics_summary()`
carries the parsed kinds per change, and `_extra_report()` sits beside `_prompt_report()`. The
skills change only their WAIT wording and the step after it.

Expected effect, from the sample: harness and command entries leave the count (about 1.1 a
change); the plan hand-off goes (14 of the 19 `after_gate`, about 1 a change). The median excess
goes from about 3.5 to about 1.5. The rest, revise, asked and unprompted, is the person's own
conversation, which the trailer now names for the next retro.

## Contracts touched

- **Metrics trailer format: extend, never redefine.** `Sdlc-Extra` is a new line. `extra=` and
  `stops=` keep their meaning, "a message the person typed between gates", and stop counting
  entries the person never typed. **This changes what a host's new `Close` commits count**: the
  always-Tier-2 rule on a trailer's meaning, as 042's `permission=`. `Sdlc-Extra`'s presence marks
  a commit counted the new way, and retro's `recorded` keeps old and new apart.
- **No message text leaves `read_events`.** Kinds and bools only; R3's test asserts it.
- **Measuring never refuses.** An unknown shape falls to `unprompted`, never an error.
- **Each skill has exactly one WAIT.** The question gains a clause; the plan approval stays plan
  mode's own. No approval folds into another: entering plan mode approves nothing.
- **Narrow `allowed-tools`.** `EnterPlanMode` writes nothing, so it is not a command that writes
  run unasked.
- **The factory's pinned copies** parse `Sdlc-Fixes` and `Sdlc-Base`, not `Sdlc-Stage`: nothing
  there moves.

## Alternatives rejected

- **Dropping harness entries silently**, with no `harness=` count: a retro couldn't see why
  `extra` fell between windows.
- **A new key on `Sdlc-Stage`:** that line already holds 25 fields; a line of its own can be
  absent on old commits.
- **Asking about plan mode with `AskUserQuestion` after the WAIT:** a typed "plan" becomes a
  question, the same stop.
- **Ship committing straight after "fix a finding first"** without asking again: two approvals
  folded into one. It stays `revise`.
- **Classifying `asked` from wording:** that stores or matches text; the trailing `?` is a shape.

## Verification

- `./check.sh` green, with new tests for R1–R6 and R9 in `tests/test_metrics.py`,
  `tests/test_sdlc.py` and `tests/test_skills.py`.
- `sdlc.py close 047 --check` previews the trailers; the real `Close 047` commit shows
  `Sdlc-Extra` lines whose `harness=` matches the task notices this change's sessions received.
- The scratch classifier rerun on 033–046 through the new `read_events`, against the table above.
