---
id: 164
slug: prompts-in-files
tier: 2
impact: patch
stage: shipped
created: 2026-11-18
updated: 2026-11-19
shipped: 2026-11-19
idea:
depends_on:
serves: none
---

# The factory's agent prompts live in files, not code

## Problem

Every prompt a factory agent receives is built in Python string code in
`plugins/factory/scripts/factory.py`: `_task_prompt` (232 lines) for each build-loop task (build,
fix, rework, review, verify, approve, mend, decided, restart, upgrade, spec) and `_land_task` (138
lines) for the landing's (land-review, land-verify, land-fix, land-mend, train-resolve). They were
among the most-rewritten functions in the last window: 17 and 9 changes. Most of those edits were
wording, a sentence an agent needed to read differently, yet each one is a code diff in a script
reviewers read as code, entangled with the f-string plumbing around it, and it conflicts with any
other change to the same function. `docs/RETRO-SCORECARD.md` lists this as R2.

## Outcome

- Each task's prompt text lives in a file of its own under the factory plugin (one per task),
  with named placeholders for what varies (the change, its folder, the round, the reviews to
  read, the check line), and `factory.py` fills and sends it.
- A pure move: for every task, on the existing test fixtures, the prompt an agent receives is
  byte-identical before and after. A test builds each task's prompt both ways (or against a
  recorded copy) and compares.
- `factory.py agent` stays the one place the factory runs `claude`; the prompt files are text the
  script reads, nothing runs them.
- A prompt file whose placeholders don't match what the script fills is refused when the factory
  starts a task, never sent half-filled, and a test covers it.
- `_task_prompt` and `_land_task` shrink to choosing a file and filling it.

## Affected

`plugins/factory/scripts/factory.py` (`_task_prompt`, `_land_task`, `_task`, `check_line`), the new
prompt files, `tests/test_factory.py` and `tests/test_land.py` (the tests that read a prompt's
wording), and `plugins/factory/README.md`, which says where the prompts are. Every factory agent
reads these prompts on every run, in this repo and in any host with the factory, so a wording slip
changes what an agent does. `landing.py` is in `[review] sensitive`; if its tasks' prompts are
assembled there, the run is reviewed at full depth.

## Constraints

- No prompt's text changes in this change. Wording edits come later, as their own diffs in the new
  files.
- No machine path is written into a prompt file. Paths are filled in at run time, as today.
- The cached plugin carries the files: they sit under `plugins/factory/`, which the marketplace
  copy includes.
- `factory.py` still never imports `sdlc.py`; the files need no new dependency (plain text with
  stdlib substitution).
- Windows: files read with `encoding="utf-8"`.

## Open questions

- ~~The placeholder syntax (`str.format`, `string.Template`, or a small marker of its own), given
  prompts that quote braces and backticks.~~ Resolved: `string.Template` (`${name}`, `$$`), spec
  Design.
- ~~Where the files live (`plugins/factory/prompts/`, beside `agents/`), and whether a host can
  override one, as it can `.sdlc/templates/`, or not, so agents stay predictable.~~ Resolved:
  `plugins/factory/prompts/`, read from the plugin alone, no host override (spec R8).
- ~~How the conditional parts (a restart's reasons, a person's words, round-2 context) are expressed
  without logic in the files: separate fragment files, or the script assembling sections.~~
  Resolved: the script keeps its `if`s and joiners; each task's file holds named `## <part>`
  sections (spec Design).
