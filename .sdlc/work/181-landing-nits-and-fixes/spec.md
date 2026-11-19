---
id: 181
slug: landing-nits-and-fixes
kind: spec
created: 2026-11-19
updated: 2026-11-19
---

# 181 — A landing retires only the nits it takes in, and goes on past a fix already made · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

**Assumptions, checked in the code.** `named_nits()` (`plugins/factory/scripts/factory.py`) is
the only code that decides which nits a landing retires. Three places call it: `cmd_land()`
(both branches) and the `resolve` task's `gone` prompt in `_land_task()`, both in
`landing.py`, and the close path's `drop_entries()` call (`landing.py`, near line 2477). Core
`sdlc.py` never reads an Approach or a Requirements section for nits, and no file in `scripts/`
reads `build/land-<n>.md`. So neither change needs a copy in `scripts/factory_records.py`.
`land_verdict()` sets `fixed` from `build/land-<n>.ask.md`, and `land_signals()` raises
`LANDING_FIXED` from the same file, not from any edit, so the fix stays a signal whatever the
builder did. The tests for these paths are in `tests/test_land.py` (the intent says
`test_factory.py`), plus `tests/test_train.py`, `tests/train_driver.py` and
`tests/test_prompts.py`.

R1. A landing retires an open nit only when its id is on a `Nits taken in:` line in the intent's
    `## Approach` or the spec's `## Requirements`. An id written anywhere else in those sections
    retires nothing, even one the prose says is not taken in. `test_a_nit_named_but_not_taken_in_stays`
    lands a change whose Approach names one open nit in prose ("left to a later change") and
    another on a `Nits taken in:` line. It asserts that `retired_nits` and the `Retire` lines in
    `entries.md` hold only the second, and that after `land --close` the first is still in the
    register. It fails if `named_nits()` goes back to matching every id in the section.
R2. The marker line can take these forms:
    - a plain line, a list item (`- ` or `* `), or a bold lead (`**Nits taken in:**`), matched
      without regard to case;
    - a line continuing the marker line, indented by at least one space, up to the next blank or
      unindented line (a wrapped list item).

    Ids on it are matched whole, as today: one id is never matched by a longer id that begins
    with it. A `Nits taken in:` line in any other section (`## Problem`) retires nothing.
    `test_the_nits_taken_in_line_is_read_in_its_forms` checks each form, a continuation, the
    whole-id match and a marker under `## Problem`.
R3. `named_nits()` keeps its signature `(root, folder, text=None)`, its register parsing and its
    register order. `test_the_landings_nits_are_the_ones_sdlc_reads` keeps passing with its ids
    put on a marker line, so its parity with `sdlc.py`'s `parse_entries()` still holds.
    `test_a_landing_retires_the_nits_its_intent_names` and
    `test_a_landing_whose_commit_failed_commits_on_rerun` write a `Nits taken in:` line in place
    of their prose "Takes in nit …" and still retire that nit. Their old prose now retires
    nothing, which R1's test pins.
R4. The words that tell a person or an agent how to take a nit in all name the marker:
    `skills/intent/SKILL.md` (*Open nits, for a Tier 1 change*), `skills/intent/batch.md` (Step 2),
    `skills/spec/SKILL.md` (*Open nits*), `plugins/factory/skills/land/SKILL.md` (`commit`) and
    `plugins/factory/README.md`. `test_every_place_that_takes_a_nit_in_names_the_marker` (in
    `tests/test_skills.py`) fails if any of them stops saying `Nits taken in:`.
R5. `land-fix --commit` goes on when three things hold:
    - nothing is dirty outside the change's folder;
    - the builder's report `build/land-<n>.md` gives `FIX: ALREADY MADE` as its answer (read by
      `opening()`: first, or the only answer it gives);
    - the report's `## Evidence` passes `read_evidence()`.

    It then exits 0 with `fixed: []`, `already_made: true`, `round` and `head`, leaves `HEAD` as
    it was, and marks the train's stored fix `done`. `test_a_fix_already_made_goes_on_without_a_commit`
    asserts all of that, and fails if the step still refuses or amends a commit.
R6. With nothing dirty outside the folder, `land-fix --commit` still refuses, and leaves `HEAD` and
    the train's fix untouched, in three cases:
    - the report is missing;
    - the report gives no `FIX: ALREADY MADE` answer (none, or lines that disagree);
    - its evidence fails `read_evidence()`.

    The refusal says which, and names the line and section the builder owed. The extended
    `test_a_fix_commit_needs_an_ask` covers each case, and keeps its existing `changed nothing`
    assertion for a report with no claim.
R7. When the builder did edit outside the folder, `land-fix --commit` amends the edits into the
    change's commit as today, whatever its report says. `already_made` is then false.
    `test_a_fix_asked_at_landing_is_built_gated_and_reviewed_at_depth` gains the assertion.
R8. In a train, a stored fix that the builder reports as already made goes on to the tip's gate and
    then the landing review at the run's full depth, with no stop. This holds both for the
    driver's steps and for `train --run`. `test_a_train_fix_already_made_goes_on_to_the_gate` (in
    `tests/test_train.py`, through `train_driver.py`) asserts the reading after `--commit` is
    `gate`, then `review` with every reviewer at depth.
R9. A fix already made is still a fix made while landing:
    - `land_signals()` lists `a fix was made while landing`;
    - `land_verdict()` reports `fixed: true`;
    - `land --close` on a `by=auto` commit refuses as for any fix.

    `test_a_fix_already_made_is_still_a_signal` asserts all three. It fails if the ask file is
    removed or ignored on this path.
R10. The land-fix prompt (`plugins/factory/prompts/land-fix.md`, `## main`, still one line) tells
     the builder what to do when the asked-for state already holds: edit nothing, give
     `FIX: ALREADY MADE` as its answer, and show the commands that prove it under `## Evidence`.
     A `tests/test_prompts.py` assertion on the built `land-fix` prompt fails without it.

This spec takes in no nit.

## Design

**Which nits a change takes in.** `named_nits()` gets a new input. It no longer joins the
`NIT_SECTIONS` text and searches it. It joins only the marker lines found in those sections,
through a new helper, `taken_lines(text) -> str`. The helper scans the `_section()` output for
lines matching `TAKEN_RE`, which is
`^\s*(?:[-*]\s+)?(?:\*\*)?nits taken in:(?:\*\*)?(.*)$` with `re.IGNORECASE`. It keeps each
match's text after the colon, and keeps each following line that starts with whitespace and
isn't blank. The id match after that is unchanged: the register's open `[nit]` ids (fences
skipped, `NIT_RE`) are kept when found whole (`(?<![\w-])id(?![\w-])`) in that text. The
comment above `NIT_SECTIONS` and the docstring of `named_nits()` say the marker is what takes a
nit in.

`named_nits()` stays the one reader, so all three callers change together:
- `cmd_land()`'s `retired_nits` and the `Retired nits:` paragraph;
- the `entries.md` `Retire` lines (`retire_nits()`), and close's `drop_entries()` through them;
- the resolver's `gone` list for a register conflict.

Nothing else moves. Entries are still retired only inside the `Close` commit, from `entries.md`.

**Where the marker is written.** The words change, but no template does:
- Tier 1 (`skills/intent/SKILL.md`): "each one taken goes on a `Nits taken in: <id>, <id>` line
  in the **Approach**; an id written anywhere else is never taken in".
- Batch (`batch.md`): the same line for a Tier 1 in a batch.
- Tier 2 (`skills/spec/SKILL.md`): "each one taken becomes a requirement, and its id goes on the
  section's `Nits taken in:` line".
- The factory's land skill and README describe `retired_nits` as the ids on that line.

Core `/sdlc:ship` gets no new marker. Its Step 0 already lists the nits the diff touches, and
proposes each retirement with a reason for the person's yes. A change built by hand and one
built by the factory name their nits with the same line, because both use the same intent and
spec skills. They only retire them differently: ship by the person's judgment, the factory by
the line.

**A fix already made.** `factory.py` gets `FIX_RE = re.compile(r"^FIX: (ALREADY MADE)\s*$")`
beside `VERDICT_RE`. `cmd_land_fix(commit=True)` keeps its checks up to `fixed`, then branches.
When `fixed` is empty:
1. Read `build/land-<n>.md`. If it's missing, refuse: "the builder changed nothing outside the
   change's folder, and wrote no report".
2. If `opening(lines, FIX_RE)` finds no answer, refuse with today's message, extended: "…nothing
   to commit, and its report doesn't say `FIX: ALREADY MADE` first".
3. If `read_evidence(text, "build/land-<n>.md")` returns problems, refuse with them.
4. Otherwise call `_train_fix(root, folder, done=True)` and emit
   `{"change", "round": n, "fixed": [], "already_made": true, "head"}`, exit 0.

When `fixed` is not empty, the path is today's, plus `already_made: false`.

The report stays in the change's folder. It is amended into the change's commit by the next
`_amend_record()` (stack or close), as every file under the folder is, so the claim and its
evidence land with the change. This adds no write: the only file touched is the train state, and
`_train_fix()` already writes it.

**The train.** `RUN_STEPS["fix"]` doesn't change. `--commit` exiting 0 is what lets the loop go
on. With `HEAD` unmoved, `_train_reading()` doesn't re-stack (`head != mine["stacked"]` is
false). The fix is `done`, so the next step is the gate at the tip, then the landing round that
`--ask` opened, at full depth, because `fixed` comes from the ask file. Those reviewers read the
person's words in their prompt and the diff as it stands, so the landing review checks a false
"already made". With `--by person`, the person's yes at close still stands after that.

**Edge cases.**
- If the builder edits and also claims "already made", the edits are committed (R7). The claim
  is moot, and the review reads the edit.
- If the report has `FIX: ALREADY MADE` but no `## Evidence`, it's a stop (R6). A rerun of the
  train skips `--ask` (`asked`) and runs the builder again, so the rerun can recover. No mend is
  added.
- If the ask file is missing, the step refuses before any of this, as today.

## Contracts touched

- **The register: entries are retired only inside the `Close` commit, from `entries.md`
  (`held_entries()`, the factory's copies pinned).** The path doesn't change; only fewer ids
  reach `retire_nits()`. No new code commits the register, and none edits it on the branch.
- **`[review] sensitive` covers `landing.py`.** The change edits `cmd_land_fix()` there, so the
  review runs at full depth. That is expected, not avoided.
- **The factory: `factory.py` never imports `sdlc.py`; core reads a run's records only through
  `scripts/factory_records.py`, with pinned copies.** Neither the new `FIX_RE` nor `TAKEN_RE` is
  read by core (checked: nothing in `scripts/` reads `build/land-*.md` or nit markers), so no
  copy and no pin is owed. If a later change makes the board show "already made", that change
  adds the copy.
- **Agents that judge have no Write; only the builder edits; no agent commits.** This doesn't
  change. The builder's claim decides nothing alone: the script checks the empty diff and the
  evidence, and the landing reviewers and the person judge the claim.
- **A builder report ends with `## Evidence`, which only the script judges (`read_evidence()`,
  `is_read()`).** The new check reuses `read_evidence()` unchanged. The "one stop a run mends"
  rule covers build rounds and landing reviewers. This change adds no mend for the land-fix
  builder, so the stop stays a stop.
- **Writes before a WAIT.** None added. `land-fix --commit` runs after the person's yes, as
  today.
- **Skills (`tests/test_skills.py`).** Only prose changes in `SKILL.md` and `batch.md`. No bash
  block, `allowed-tools` rule, WAIT or config key changes.
- **The scripts run on Windows.** No new subprocess, `open()` or `write_text`. The paths in the
  refusal text are built with `as_posix()`, as `rel` already is.
- **One shape for the shipped docs / setup drift.** No file in `templates/`, `defaults/` or
  `guide/` changes, so `sdlc.py record` is not owed and `drift` stays clean.
- **Nothing about a project or a workspace.** Test data uses the neutral fixture register already
  in `tests/test_land.py`.

No invariant needs to change.

## Alternatives rejected

- **Retire the ids the landing review confirms the diff settled.** The intent's constraint rules
  this out: a nit is retired by what the change says it took in, never by the diff's evidence.
  It would also let a judging agent's words decide what happens to the register.
- **Give the marker a section of its own (`## Nits taken in`).** That is a new template heading
  the script reads. It is a `TEMPLATE_READS` entry and a `breaking` setup change for every host,
  for what one line already says.
- **Keep matching bare ids, but skip those near "not", "left to" or "none is taken".** Parsing
  negation in prose is fragile, and it is how the bug started. Only a positive marker is
  checkable.
- **Fall back to bare ids when a change has no marker line.** That brings back the bug for every
  change that forgets the line. The failure should be in the safe direction: a nit that stays
  open costs a manual retire, while a nit retired wrongly is lost from view.
- **Take an empty diff alone as "already made".** A builder that crashed, stalled or misread the
  ask also changes nothing. The intent asks for the builder's report with its evidence, and
  keeps today's stop for a builder that gives none.
- **Add a mend for the land-fix builder's missing evidence.** The intent doesn't ask for it, and
  a train rerun already asks the builder again.
- **Teach core `/sdlc:ship` to retire by the marker.** Ship already shows each retirement for the
  person's yes. Making it read the line would turn a judgment the person approves into a rule.

## Verification

```bash
uv run --group dev pytest -q tests/test_land.py -k "nit or fix"   # R1–R3, R5–R7, R9
uv run --group dev pytest -q tests/test_train.py -k fix           # R8
uv run --group dev pytest -q tests/test_prompts.py tests/test_skills.py   # R4, R10, skills' rules
uv run --group dev pytest -q tests/test_modules.py tests/test_windows.py  # module bounds, Windows rules
./check.sh                                                        # the full gate
```

A healthy run:
- every selected test passes, and none is skipped beyond those marked `needs_uv` on a machine
  without `uv`;
- `./check.sh` ends with `ruff check`, `ruff format --check`, `pytest -n auto` and
  `claude plugin validate --strict` all clean;
- in `test_a_nit_named_but_not_taken_in_stays`, the register after close still holds the nit
  named in prose, and `retired_nits` is the one-element list from the marker line;
- in `test_a_fix_already_made_goes_on_without_a_commit`, `git rev-parse HEAD` is the same before
  and after `--commit`, and the output has `already_made: true`.

