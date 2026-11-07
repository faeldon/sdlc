---
id: 042
slug: permission-stops
tier: 2
impact: minor
stage: shipped
created: 2026-11-07
updated: 2026-11-07
shipped: 2026-11-07
idea: 2026-10-26-4
depends_on:
serves: [O3]
---

# 042 — Name each permission stop on the Close commit

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Close counts what it calls permission prompts, but the count isn't that. `metrics.read_events()`
emits a `permission` event for each user entry whose `permissionDecision.source` is
`user_temporary` (`scripts/metrics.py:351`), and in this repo's transcripts every one of those,
142 of them, is an `AskUserQuestion` answer or an `ExitPlanMode` approval: stops already counted as
`question` and `gate`. The person's 5 rejections (`user_reject`) aren't counted at all.

No tool has prompted the person here: every session runs in `auto` mode, where the classifier
decides, 041's `accept` included, which is why 041's ship shows `permission=0`. So the last
retrospective's "a Tier 2 change meets 3 permission prompts", and M4's "permission prompts are most
of the excess", rest on a mislabelled count. A host in default mode does get tool prompts, and
nothing says which tool or command each was for, so 2026-10-26-5 (cover the prompts a skill's
rules should have) has nothing to work from there either.

## Outcome

- Close records, for each tool prompt the person answered, rejections included, what it was for: the tool, and
  for `Bash` the command's first word (or `sdlc.py`'s subcommand). Numbers and names only, as the
  metrics contract requires: no arguments, paths or message text.
- It goes on the `Close` commit as a new trailer beside the existing ones (`Sdlc-Permission: …`,
  its shape for the spec), the `permission=` counts unchanged.
- `sdlc.py retro` groups the window's prompts by what they asked for, with how many changes each
  came from, so a retrospective can name the recurring ones.
- A test reads a transcript fixture with a prompted `Bash(git push …)` and a prompted `Bash(uv run …
  sdlc.py accept 042)` and asserts the trailer names `git` and `sdlc.py accept`, and nothing else
  from the command.
- **Moves O3:** the next retrospective can name the prompts behind the median change's permission
  stops, so 2026-10-26-5 covers the avoidable ones and the median Tier 2 change's stops fall toward
  6.

## Affected

- **Area:** close's `measure` step and retro's metrics.
- **Files & components:** `scripts/metrics.py` (`read_events`, `summarize`, `trailers`,
  `parse_trailers`); `scripts/sdlc.py` (`metrics_summary()` and retro's metrics);
  `tests/test_metrics.py`; `docs/REFERENCE.md` (*Metrics*).
- **Downstream:** every host's `Close` commits from the release that ships this; retro reads them,
  and the factory's eval and review read `Sdlc-*` trailers through pinned copies of the parsing.
- **Contracts:** the metrics event list and trailer format (extend, never redefine); no message
  text, file path or session id leaves `read_events`; measuring never refuses.

## Constraints

- **Names only.** A command's first word could still carry something private (a script named after
  a client): decide what is safe to keep before writing any.
- **Old trailers still parse.** A `Close` commit without the new line reads as "not recorded",
  never as "no prompts".
- **Measuring never refuses.** A prompt whose tool use can't be found is counted as unknown, not
  dropped.

## Open questions

- ~~Which decisions count. Today only `user_temporary` does; a prompt answered "always allow" (likely
  another `source`) and a denied one are stops too, and 041's ship showed `permission=0` though
  `accept` prompted.~~ Resolved: any `user_*` decision on a tool but `AskUserQuestion`,
  `EnterPlanMode` and `ExitPlanMode`; 041's `accept` never prompted, the auto-mode classifier
  approved it (spec R1).
- ~~How to name a command: the first word, `git` plus its subcommand, `sdlc.py` plus its subcommand,
  or the skill's own `Bash(...)` rule it failed to match.~~ Resolved: the program's basename, with
  the subcommand for `git`, `gh`, `sdlc.py` and `factory.py` (spec R2).
- ~~The trailer's shape: one `Sdlc-Permission:` line per change with `tool:name=count` pairs, or per
  stage.~~ Resolved: an `Sdlc-Prompt:` line per name, and `prompts=` per stage in place of
  `permission=` (spec R3).
- ~~Whether retro should also say which skill was running when each prompt came, so a gap points at a
  skill's `allowed-tools`.~~ Resolved: no; `prompts=` per stage says where they fell (spec
  Alternatives rejected).
