---
id: 042
slug: permission-stops
kind: spec
created: 2026-11-07
updated: 2026-11-07
---

# 042 — Name each permission stop on the Close commit · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. A permission prompt is a tool use the person was asked to allow: a user entry whose
   `permissionDecision.source` starts with `user_` (`user_temporary`, either `grantScope`, and
   `user_reject`), on a tool other than `AskUserQuestion`, `EnterPlanMode` and `ExitPlanMode`, which
   are the person's questions and plan gates and are already counted as `question` and `gate`. A
   `config` decision (a rule, the mode, the classifier) is never one. A test feeds `read_events` a
   transcript with one of each and asserts exactly the two tool prompts come out.
2. Each prompt is named, numbers and names only: the tool's name, and for `Bash` the program the
   command runs, by its basename (`cd …` segments skipped), with the subcommand for `git`, `gh`,
   and `sdlc.py` or `factory.py` run through `uv run --script`: `Bash:git:push`,
   `Bash:sdlc.py:accept`, `Bash:make`, `Edit`. Anything it can't parse, and a tool use it can't
   find, is `Bash:unknown` or `unknown`, never dropped. A test asserts no argument, path or flag
   from the command reaches the name.
3. The `Close` commit carries, per prompt name, an `Sdlc-Prompt: <name> asked=<n> rejected=<n>`
   line, and `Sdlc-Totals` and each `Sdlc-Stage` carry `prompts=<n>` in place of `permission=`.
   `parse_trailers()` reads both back; a round-trip test pins it.
4. `Sdlc-Totals` carries `prompt_modes=`, the permission modes the change's entries ran in other
   than `plan` (`auto`, `default`, `acceptEdits`…, comma-separated, `-` for none seen), so a
   reader can tell "no prompts, because auto mode decided" from "no prompts asked".
5. `sdlc.py retro`'s `metrics` compares `prompts` where it compared `permission`, over the changes
   whose trailers carry it: a `Close` commit without `prompts=` reads as unrecorded, never as 0, and
   its old `permission=` is not read. A test with one old and one new trailer asserts the median
   rests on the new one alone.
6. `sdlc.py retro` gives `metrics.prompts`: each name across the window with `asked`, `rejected`
   and how many changes it came from, most asked first, and `modes`, how many changes ran in each.
   The retro skill's Process pass names the recurring prompts from it.
7. `docs/REFERENCE.md` (*Metrics*) and `scripts/metrics.py`'s contract docstring say what a prompt
   is, its name, the new lines and keys, and that `permission=` on older commits counted questions
   and plan approvals, not prompts.

## Design

**Reading (`read_events`).** The user entry that answers a prompt carries `permissionDecision` and a
`tool_result` whose `tool_use_id` names the assistant's `tool_use`, which `read_events` already
walks. It keeps a map of tool-use ids to `(name, input)` for the file, and on a `user_*` decision
looks the id up and emits `permission{name, rejected}` (the event kind kept, its fields added),
skipping the three question and plan tools. The name is computed there, from `_prompt_name(tool,
input)`, so no command text leaves `read_events`. Modes come from the `permission-mode` entries and
each entry's `permissionMode`, collected as a set on a `mode{modes}` event at the end of each
session's entries.

**Naming (`_prompt_name`).** `Bash`: `shlex.split` the command, falling back to `str.split` on a
quoting error; split on `&&`, `||`, `;` and `|`; take the first segment that isn't `cd`, skip
leading `NAME=value` words, and take the program's basename. `git` and `gh` add their first
non-flag word; `uv` with `--script` adds the script's basename when it is `sdlc.py` or `factory.py`,
then that script's subcommand. Every part goes through `_word()`. Other tools: their name, `mcp__`
names included. Unknown pieces are `unknown`.

**Summary and trailers.** `summarize()` counts `prompts` per stage and in totals in place of
`permission`, and keeps `by_prompt: {name: {asked, rejected}}` and `prompt_modes`. `trailers()`
writes `prompts=` where `permission=` was, `prompt_modes=` in totals, and one `Sdlc-Prompt:` line
per name, sorted, after the `Sdlc-Role:` lines; `parse_trailers()` files `Sdlc-Prompt` under
`prompts`. `stops=` is unchanged: prompts sit beside it, not in it.

**Retro.** `COMPARED` swaps `permission` for `prompts`. `metrics_summary()` already takes the median
over the totals present; a missing `prompts` is skipped, not zero. A new `_prompt_report()` sums
`Sdlc-Prompt` lines across the window into `metrics.prompts`, with `modes` from `prompt_modes`.

## Contracts touched

- **The metrics contract: extend, never redefine** (AGENTS.md, *Metrics*). This change **stops
  writing `permission=`**, because what it counted (questions and plan approvals, already counted as
  `question` and `gate`) was never what its name said, and writes `prompts=` beside it under a new
  name rather than redefining the old one. History keeps every `permission=` as it was; retro stops
  reading it. That is a removal from the trailer format, said here so it is approved, not slipped
  in. `permission` stays an event kind, with fields added.
- **No message text, file path or session id leaves `read_events`**: the name is built inside it
  from the command, and keeps only a program basename and a fixed subcommand. A host's script name
  can reach its own `Close` commit, in its own history; nothing goes anywhere else.
- **Measuring never refuses**: an unparseable command or a missing tool use is named `unknown`.
- **What `sdlc.py` writes in a host** (always Tier 2 here): new trailer lines and keys on every
  `Close` commit from this release on.
- **The factory's pinned copies of trailer parsing** read `Sdlc-Fixes` and `Sdlc-Base` only, so
  nothing there changes.

## Alternatives rejected

- **Fixing `permission=` in place.** Same key, a different count from this release on: retro's
  medians would mix the two silently across a window, which is the redefinition the contract
  forbids.
- **Counting prompts in `stops=`.** A prompt does stop the person, but folding it in changes what
  `stops=` meant on every earlier commit, and O3's target with it. Kept beside `stops=`, where retro
  shows both.
- **The skill's `Bash(...)` rule the command failed to match, as its name.** The harness doesn't
  record which rule it tried, so this would mean re-running the matcher on the command text after
  the fact, and the skill that was running isn't always one with rules.
- **Recording each prompt with its stage.** `Sdlc-Stage`'s `prompts=` already says where they fell;
  a name-by-stage table would double the lines for little.

## Verification

```bash
./check.sh                                         # the gate
uv run --group dev pytest -q tests/test_metrics.py # the reading, naming and trailers
uv run --quiet --script scripts/sdlc.py retro | python3 -c "import json,sys; print(json.load(sys.stdin)['metrics'].get('prompts'))"
```

Healthy: the gate is green; on this repo's own history `metrics.prompts` is empty with `modes`
unrecorded for every change so far, since none carries the new keys, which is the honest answer.
042's own `Close` commit is the first to carry `prompts=`, `prompt_modes=auto` and no
`Sdlc-Prompt:` line, since every session here runs in auto mode.
