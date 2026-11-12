---
id: 050
slug: own-script-and-asked-stops
tier: 1
impact: patch
stage: shipped
created: 2026-11-12
updated: 2026-11-12
shipped: 2026-11-12
idea:
depends_on:
fixes: [2026-11-12-3, 2026-11-12-4, 2026-11-10-3]
serves: [O3]
---

# 050 — Count ship's own questions as asked, and hand a change's own script every command ship runs

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Three bugs, found shipping 047 and 049, each making the plugin's numbers, or its own changes, less
trustworthy:

- **2026-11-12-3 (low, introduced by 015).** `main()` in `scripts/sdlc.py` calls `ap.parse_args()`
  before it hands `ship`, `drop`, `base` and `sync` to the change's own script, so main's copy
  rejects a flag the change adds: at 049's ship, `sdlc.py ship 049 --fixed F1,F2 --through F2`
  failed with "unrecognized arguments" and the worktree's script was run by hand. And `preflight`
  and `findings` never hand off, so the same ship read `findings.md` with main's parser, which
  didn't know the `fix` disposition the change added.
- **2026-11-12-4 (low, introduced by 047).** `metrics.read_events` marks a stop `asked` only when
  the agent's last text ends with `?` (`scripts/metrics.py:512`). Every WAIT question ends with its
  options instead, `…? (yes / edit the message)`, so at 049's ship the answers to "Fix F1, then
  commit this, …?" and "Fix F2, then review again?" counted as `unprompted`
  (`Sdlc-Extra: ship … unprompted=2`, 9 stops against a target of 6).
- **2026-11-10-3 (med, found by 047's review).** `metrics._membership()` looks for
  `<command-name>/sdlc:…` in every user entry, compaction summaries and task notices included: a
  summary quoting `/sdlc:intent` can move where a change's main-branch run starts, and one quoting
  a skill, or a notice typed after close's approval, can end close's run early, so close's stops and
  tokens go uncounted. 047 keeps those entries out of `read_events`; membership lacks the same
  check.

## Outcome

- From a change's worktree in the plugin's repo, `ship`, `drop`, `base`, `sync`, `preflight` and
  `findings` all hand off to the change's own `scripts/sdlc.py` before any argument is parsed, so a
  flag only the change knows reaches it. A test pins it.
- The agent's last text reads as a question when it ends with `?`, or with `?` followed by options
  in parentheses (quotes or backticks allowed), so an answer to ship's question that isn't the gate
  reads `asked`. A test with 049's two questions pins it.
- `_membership()` ignores compaction summaries and task notices, as `read_events` does. Tests: a
  summary quoting `/sdlc:intent`, a notice quoting `/sdlc:close`.
- `preflight` with `--context`, `--nits`, `--bugs`, `--closing` or `--split` and no `--question`
  refuses and says so, instead of dropping them (nit 2026-10-27-6).
- **Moves O3:** a WAIT question's answer counts as asked, never unprompted, so the stops above
  target close records are the ones worth cutting.

## Affected

- **Area:** the script's entry point in the plugin's own repo, and close's measuring.
- **Files & components:** `scripts/sdlc.py` (`main()`'s handoff before `parse_args`,
  `OWN_SCRIPT_CMDS`, `preflight`'s flag check), `scripts/metrics.py` (`read_events`' `asked`,
  `_membership()`), `AGENTS.md`'s handoff paragraph, `docs/REFERENCE.md` where it describes
  `asked`, and tests in `tests/test_metrics.py`, `tests/test_preflight.py` and the handoff tests.
- **Downstream:** the handoff runs only in the plugin's own repo (`_own_repo()`), so no host sees
  it. The stop kinds and membership feed `Sdlc-Extra`, `Sdlc-Totals` and `Sdlc-Stage` in every host
  that measures, read by retro; history isn't re-measured, only new `Close` commits count
  differently.
- **Contracts:** the handoff is never a refusal (a crash falls back to the running copy), kept as
  it is; `asked` keeps its documented meaning, an answer to a question the agent put in prose, only
  its detection changes; the trailers gain no key; read-only commands stay read-only handed off.

## Constraints

- `_own_script()` stays limited to the plugin's own repo and a change whose branch edits `scripts/`.
- Handing off before parsing still honours `SDLC_OWN_SCRIPT`, so a command is never handed off twice.
- No message text leaves `read_events`: the question test reads the text as now and keeps a boolean.

## Open questions

- Should a WAIT answer that isn't the gate get a kind of its own, rather than `asked`? Retro reads a
  recurring `asked` as "a skill that could ask it in its WAIT instead", and here it was the WAIT.
  Kept as `asked` unless the plan finds a reason.
- Does `close` belong on the handoff list? It has its own handoff (`_handoff()`), so probably not.

## Approach

In `main()`, read the subcommand from `sys.argv[1]` and call `_own_script(root)` before
`ap.parse_args()`, so `_run_own(own, sys.argv[1:])` sees the raw arguments and an unknown flag
reaches the change's own parser; `OWN_SCRIPT_CMDS` gains `preflight` and `findings`. In
`read_events`, `asked = said.rstrip().endswith("?")` becomes a small `_ends_with_question(said)`
that strips trailing backticks, quotes and `*` and matches `\?(\s*\([^()]*\))?$` on the last line.
In `_membership()`, skip an entry whose `origin.kind` is `task-notification` or that is
`isCompactSummary` before matching `SKILL_RE`, reusing `scripts/metrics.py:488`'s check. In the
dispatch, refuse those flags without `--question` (nit 2026-10-27-6). Tests in
`tests/test_metrics.py`, `tests/test_preflight.py` and wherever `_own_script` is tested;
`AGENTS.md` gets a sentence on the handoff coming before parsing and `preflight`/`findings` on the
list.
