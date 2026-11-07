---
id: 042
slug: permission-stops
kind: plan
created: 2026-11-07
updated: 2026-11-07
---

# 042 — Name each permission stop on the Close commit · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/metrics.py`:
  - `read_events`: tool-use map, the prompt detection, and the modes.
  - `_prompt_name` (new).
  - `_blank_stage`, `_active` and `summarize`: `prompts` in place of `permission`, plus `by_prompt`
    and `prompt_modes`.
  - `trailers`: `prompts=`, `prompt_modes=` and `Sdlc-Prompt:` lines.
  - `parse_trailers`: reads `Sdlc-Prompt` lines.
  - The contract docstring.
- `scripts/sdlc.py`: `COMPARED` swaps `permission` for `prompts` (line 5115). `metrics_summary()`
  gains a top-level `prompts` from a new `_prompt_report()`.
- `skills/retro/SKILL.md`: the Step 0 `metrics` list says what `prompts` holds, and the Process pass
  gets one bullet naming the recurring prompts and the modes.
- `docs/REFERENCE.md` (*Metrics*, line 641): what a prompt is, its name, the new line and keys, and
  that older `permission=` counted questions and plan approvals.
- `tests/test_metrics.py`:
  - rewrite `test_permission_prompts_and_gate_runs_are_counted` (line 260), whose fixture is the
    very case R1 changes;
  - new tests for naming, rejections, question and plan tools, modes and the round trip.
- `tests/test_retro.py`: one test with an old trailer (`permission=` only) and a new one, asserting
  the `prompts` median rests on the new one and `metrics.prompts` sums the new lines. The existing
  fixtures at lines 341 and 856 stay as they are, since they are old trailers.

## Work order

1. **Reading (R1, R2)**, in `scripts/metrics.py`.
   - In `read_events`, keep `uses: dict[str, tuple[str, dict]]` per file, filled in the assistant
     branch (line 379) for every `tool_use`.
   - In the user branch (line 350), replace the `user_temporary` check. When
     `str(decision.get("source", "")).startswith("user_")`, take each `tool_result` block's
     `tool_use_id` from `content`. Look it up, and skip the three question and plan tools. Emit
     `{"kind": "permission", "name": _prompt_name(tool, inp), "rejected": decision.get("decision")
     == "reject"}`, with `name` `unknown` for an id that isn't found.
   - Collect `entry.get("permissionMode")` from kept user entries, `plan` excluded, into a set per
     file. At the end of each file, emit one `{"kind": "mode", "modes": sorted(set)}` with the
     file's last kept timestamp.
   - `_prompt_name(tool, inp)`. Non-`Bash` tools return `_word(tool)`.
     - Split with `shlex.split(cmd)`, falling back to `cmd.split()` on `ValueError`.
     - Split the words into segments on `&&`, `||`, `;` and `|` tokens. Take the first segment whose
       first word isn't `cd`, and drop leading `NAME=value` words.
     - The program is `Path(word).name`.
     - `git` and `gh` get their first word that doesn't start with `-`.
     - `uv` gets the basename after `--script` when it is `sdlc.py` or `factory.py`, then the next
       word not starting with `-`.
     - The result is `Bash:` plus the parts joined by `:`, each through `_word()`. A missing part is
       `unknown`.
   - Tests:
     - one fixture holding `user_temporary` on `Bash(git push -q origin main)`, `user_reject` on
       `Bash(FOO=1 uv run --quiet --script /x/scripts/sdlc.py accept 042)`, `user_temporary` on
       `AskUserQuestion` and on `ExitPlanMode`, and `config` on `Bash`, asserting exactly
       `[("Bash:git:push", False), ("Bash:sdlc.py:accept", True)]`;
     - a parametrized `_prompt_name` table (`cd x && make -j4 test` gives `Bash:make`, a path script
       gives its basename, an unbalanced quote gives a name, not a raise), with an assert that no
       name contains `/`, `=` or a space;
     - the `question` and `gate` counts unchanged by the decisions.
2. **Summary and trailers (R3, R4)**, in `scripts/metrics.py`.
   - `_blank_stage` and `_active`: `permission` becomes `prompts`.
   - `summarize` counts `here["prompts"]`, builds `by_prompt[name] = {"asked", "rejected"}`, and
     unions the `mode` events' modes into `prompt_modes`.
   - In totals, `prompts` replaces `permission` (line 603), and `prompt_modes` is
     `",".join(sorted(modes)) or "-"`. Return `by_prompt`. `history_summary` returns
     `by_prompt: {}`.
   - `trailers`: `prompts` in the stage fields in place of `permission` (line 848), and after the
     `Sdlc-Role` lines one `Sdlc-Prompt: {_word(name)} asked=.. rejected=..` line per sorted name.
   - `parse_trailers`: `key == "prompt" and name` goes to `out.setdefault("prompts", {})[name]`.
   - Update the docstring (lines 23–25) to `permission{name, rejected}  mode{modes}`.
   - Tests:
     - a round trip: `trailers()` then `parse_trailers()` gives back `prompts`, `prompt_modes` and
       `by_prompt`;
     - `Sdlc-Totals` has no `permission=`.
3. **Retro (R5, R6)**, in `scripts/sdlc.py` and `skills/retro/SKILL.md`.
   - `COMPARED`: `permission` becomes `prompts`. `metrics_summary()`'s `median` already drops
     non-ints, so a missing `prompts` is skipped.
   - `_prompt_report(captured)` builds `{"names": {name: {asked, rejected, changes}} most asked
     first, "modes": {mode: changes}, "recorded": n}` from each change's `metrics.get("prompts")`
     and its `totals.get("prompt_modes")`. A change without `prompts` in its totals isn't counted
     as `recorded`.
   - Put it at `out["prompts"]`.
   - In the skill, add `prompts` to the Step 0 `metrics` list, and add the Process bullet "which
     prompts recur across changes (`metrics.prompts`), against the modes they ran in: in `auto`
     mode the classifier decides, so few prompts there says nothing about a skill's rules".
   - Test (`tests/test_retro.py`): two closed changes, one with an old `Sdlc-Totals` (`permission=3`,
     no `prompts=`) and one with `prompts=1 prompt_modes=default` and `Sdlc-Prompt: Bash:git:push
     asked=1 rejected=0`. Assert the median `prompts` is 1, `recorded` is 1, and the names and modes
     are as written. Use the existing helpers there for making `Close` commits.
4. **Docs (R7).** In REFERENCE *Metrics*, add a paragraph after the stops sentence (line 654): what a
   prompt is, the name format, `Sdlc-Prompt:`, `prompts=` and `prompt_modes=`, and that a commit
   from before this release has `permission=`, which counted questions and plan approvals and isn't
   read.
5. **Gate.**
   - Run `./check.sh`.
   - Run `uv run --quiet --script scripts/sdlc.py retro` and confirm `metrics.prompts` reads
     `recorded: 0`.
   - Grep that `"permission"` survives only as the event kind, and in tests of old trailers.

## Tests

- **R1:** the mixed-decisions fixture, and the rewritten `test_permission_prompts_…`.
- **R2:** the `_prompt_name` table, and the no-`/`, `=` or space assert.
- **R3:** the trailer round trip.
- **R4:** `prompt_modes` from the fixture's `permissionMode` fields, with `-` when none was seen.
- **R5:** the old-plus-new retro test, where the median rests on the new trailer.
- **R6:** the same test's `metrics.prompts` names and modes. The skill bullet passes
  `tests/test_skills.py`.
- **R7:** read in ship's context pass.

## Rollback

`git revert <sha>` undoes it. `Close` commits made while this was live keep their `prompts=` and
`Sdlc-Prompt:` lines in history. A reverted retro reads their `permission=` as missing, which is
honest, since they have none. Nothing is created outside the repo, and setup's files don't change.
