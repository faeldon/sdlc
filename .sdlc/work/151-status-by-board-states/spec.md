---
id: 151
slug: status-by-board-states
kind: spec
created: 2026-11-18
updated: 2026-11-18
---

# 151 — status groups its sections by the board's columns · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

What this takes as given, checked in the code at this branch:

- 145's columns are already in the code. `board.py`'s `column()` returns `planned`, `designing`, `building`, `ready`, `landing` or `needs-you`. `board.html`'s `COLUMNS` orders and labels them Planned, Designing, Building, Ready, Landing, Needs you. REFERENCE.md describes them.
- Today `print_status()` prints *Open changes*, *Shipped*, *Ready to close*, *Unreleased*, *Bugs*, *Next up*, the nudges (*Setup*, *Unpushed*, *Skill evals*, *Release due*, *Retro due*), *Problems*, and last *What needs me*. Nothing prints *Ready to ship*, though the intent mentions it.
- `status` already reads most of what `column()` needs, for every open change: `needs_of()` and `answered()` on a reading made from `factory_reading()`, `factory_stop()` and `factory_land_stop()`, plus `hand_gate()` for hand-built changes and at `test`. Two things it doesn't read:
  - how far a hand-built change has got (board.py's `_seen()`, which uses `_touched()`);
  - whether a factory landing is in flight (board.py's `_progress()` and `_land_progress()`).

1. **R1.** The column rule lives in `sdlc.py` alone, as `column()` and `BY_STAGE`, moved from `board.py` without changing them. `board.py`'s `_entry()` sets `entry["column"] = sdlc.column(entry)`, and `board.py` has no `def column` or `BY_STAGE`. `test_the_column_rule_is_sdlcs_alone` fails if `board.py` defines either one again.
2. **R2.** `_seen()` and `_touched()` move from `board.py` to `sdlc.py` as `seen_stage()` and `touched_paths()`, unchanged. The board calls `sdlc.seen_stage()`, and `_plan_hint()` calls `sdlc.touched_paths()`. Every existing test in `tests/test_board.py` about Building and Ready for a hand-built change passes, with only the function names changed.
3. **R3.** A new `sdlc.factory_landing(folder, stage)` says whether a factory landing is in flight. It is in flight when:
   - the stage is `test` or `shipped`;
   - `runs/land-step.md` opens with a `STEP:` line;
   - that step is in `FACTORY_LAND_STEPS`;
   - and the step is not in `FACTORY_LAND_STOPS`.

   A record that doesn't open with `STEP:` gives the board's problem text (`runs/land-step.md doesn't open with STEP:`). `FACTORY_LAND_STEPS` is a copy of the keys of `board.py`'s `LAND_AT`, which are pinned to `factory.py`'s steps. `test_factory_land_steps_match_the_boards_track` fails if the two sets differ.
4. **R4.** `column()` decides "a landing in flight" from `entry["in_flight"]`, which `factory_landing()` sets on both sides: in the board's `_entry()` and in `status`'s reading. It no longer reads that from `entry["progress"]`. `test_the_board_and_status_read_a_landing_in_flight_alike` fails if a landing at `ship`, `gate` or `wait` lands in two different columns, or if one stopped at `stop` or `eject` is Landing on either side.
5. **R5.** Every open change in `status`, and every shipped or dropped change still waiting on close, gets `rec["column"]` from `sdlc.column()`. It is read from the same fields the board uses: `stage`, `tier`, `mode` (`factory` when `runs/` exists), `seen`, `in_flight`, `decision`, `needs`, `problems`. An unreadable `runs/land-step.md` at `test` adds its problem, so the change's `needs` start with `fix: …`. `test_status_records_only_gain_keys` still passes.
6. **R6.** `status` prints five headings in the board's order, right after its first line: `■ Planned: N`, `■ Designing: N`, `■ Building: N`, `■ Ready: N`, `■ Landing: N`. They replace *Open changes*, *Shipped* and *Ready to close*. Each lists its changes with today's open-change line, its `~`, `· stopped`/`quiet`, `gate green`/`red` marks and its `⚠`/`→` lines. A heading with no changes prints alone, with its count of 0. `test_status_prints_the_board_states_in_order` fails on any other order, or if any of the three old headings is printed.
7. **R7.** Under Landing, a shipped or dropped change prints as *Ready to close* did: `NNN  slug  → /sdlc:close NNN`, marked `(dropped)` or `(behind …)`. This covers each one `ready_to_close()` lists, and each a stopped rebase holds (`sdlc.rebasing_branches()`, moved from board.py's `_rebasing()`, which the board's `_on_board()` then calls). An open factory change landing in flight prints its change line. `test_status_lists_a_change_closing_or_rebasing_under_landing` fails if a shipped change stopped mid-rebase is missing.
8. **R8.** `■ Needs you: N` is the last section. It replaces `■ What needs me` and is still printed after *Problems*. Each change in it gets its change line (or its close line, for a shipped one whose landing stopped). Under that comes `needs you: <its needs, comma-separated>`, followed by `/sdlc-factory:decide NNN` where `decide_step()` names it. A change placed there with no needs (a stage no column takes) shows `needs you: stage <stage or ?>`. With nothing in it, the section reads `    nothing`. `test_status_ends_with_what_needs_me` becomes `test_status_ends_with_needs_you`. It fails on any other last heading, or on any other text for the 004, 013 and 041 fixtures.
9. **R9.** This is the matching test the intent asks for. It sets up one hand-built and one factory change for each of the six states:
   - **hand-built:** Tier 1 at `plan` untouched; Tier 2 at `design` untouched; `src/` touched; `findings.md` written; shipped with its worktree standing; Tier 2 at `plan` with a written spec.
   - **factory:** at `plan`; at `design`; at `build` with rounds; READY at `test`; at `test` with a `runs/land-step.md` at `gate`; stopped at `build`.

   `test_status_places_each_change_under_its_board_column` fails if a change's `status` heading differs from its board `column` label.
10. **R10.** `status` never loads `board.py`. `test_status_never_loads_the_board` swaps `sdlc._load_board` for a function that raises, runs `status`, and fails if it raises.
11. **R11.** *Unreleased*, *Bugs*, *Next up* (with or without `--all`), the nudges, *Release due* and *Problems* print exactly as before. `tests/test_next_up.py`, `tests/test_release.py` and `tests/test_push.py` pass unchanged.
12. **R12.** Every reader of the old section names changes with them:
    - `skills/status/SKILL.md`: *Needs you* is the last section; precedence step 2 becomes "a `→ /sdlc:close` line under Landing";
    - `skills/close/SKILL.md`;
    - `plugins/factory/skills/decide/SKILL.md`;
    - `docs/REFERENCE.md`: `status`'s sections, and the line that says `status` reads only what it already reads;
    - `AGENTS.md`'s *The board* paragraph, which names `_seen()` and `column()` as board.py's.

    `test_nothing_names_a_retired_status_section` fails if `■ What needs me`, `Ready to close` or `■ Open changes` appears in `skills/`, `plugins/`, `docs/` or `scripts/`.

## Design

**One rule, in `sdlc.py`.** `column()`, `BY_STAGE`, `seen_stage()`, `touched_paths()` and `rebasing_branches()` move from `board.py` into `sdlc.py` next to `needs_of()` and `answered()`. Those two are already shared the same way: the board calls them as `sdlc.<name>`, so `board.py` still loads only when `board` runs. `column()` stays a pure function of a dict. It reads `problems`, `needs`, `stage`, `mode`, `decision` (through `answered()`), `seen` and `in_flight`. The board's other uses of `progress` (its tracks, timings and `next_action()`) don't change.

**`status`'s reading.** In `main()`'s status branch, for each record in `a["open"]`:
- the `reading` it already builds for `needs_of()` also gets `mode`, plus `in_flight` and any problem from `factory_landing(folder, stage)`;
- the problem joins `reading["problems"]` before `needs_of()` runs;
- then `rec["seen"] = seen_stage(reading, folder, home, trunk)`, and `rec["column"] = column(reading | {"seen": rec["seen"]})`.

`seen_stage()` costs one `git diff -z --name-only` per hand-built change at `plan` or `design`, the same as the board does per request. `status` already runs a `git log` and a `git status` per change in `last_touched()`, so it stays quick.

For `a["ready"]`, each shipped or dropped record gets `column` from `{"stage": kind, "problems": [], "needs": rec["needs"], "mode": …}`. That comes out Landing, or Needs you when its landing stopped. Shipped and dropped changes held by a stopped rebase (`rebasing_branches()`) are added to the Landing list with the same close line.

**Printing.** `print_status()` keeps its header line and groups records by `rec["column"]`, in the order of `STATUS_STATES = (("planned", "Planned"), …, ("landing", "Landing"))`. Needs you is printed last, as described in R8. The change line is today's, factored into a helper both sections use. The `~` legend stays after the last state that showed a `~`. The *Shipped* section goes: every shipped folder on the board is under Landing. Every section keeps its `■` marker. Within a state, changes keep `analyze()`'s order.

**Where Needs you goes.** The intent says it "stays first". In the code it is last (`print_status()`'s comment "the line the eye ends on", `test_status_ends_with_what_needs_me`, and the status skill). The board's order puts it sixth too. So it stays last, which is both the board's order and its current place.

**The gap left on purpose.** Some problems only the board reads: a review with no `VERDICT:`, a `decision.md` with no `DECISION:`, a `runs/step.md` or a findings file that won't read. A change with one of those is in Needs you on the board and under its stage's state in `status`. REFERENCE.md already says this. This change narrows the gap by one, an unreadable `runs/land-step.md` (R3), and leaves the rest. Whether `status` should read them all is in the open questions.

**Boundaries.** It always:
- leaves `status` writing nothing;
- prints all six headings;
- keeps *Next up*, *Problems* and *Release due* exactly as they are.

It asks first before closing the gap above, or moving Needs you anywhere but last. It never:
- loads `board.py` from `status`;
- copies the column rule;
- changes a column's meaning on the board;
- touches `check`, which returns before any of this runs.

## Contracts touched

- **Modules loaded by path (AGENTS.md).** `board.py` loads only when `board` runs, and calls what it shares as `sdlc.<name>`. The moved functions are exactly such shared readers, so the board calls `sdlc.column()`, `sdlc.seen_stage()`, `sdlc.touched_paths()` and `sdlc.rebasing_branches()`. R10 pins that `status` never loads the board.
- **The board writes nothing (AGENTS.md, *The board*).** Unchanged: the moved functions read git and files only. That paragraph names `_seen()` and `column()` as board.py's, so its pointers are updated to `sdlc.py` (R12). That is the map catching up with the code, not a change to an invariant.
- **The factory's files are read with pinned copies.** `FACTORY_LAND_STEPS` is a new copy, pinned to `board.LAND_AT`, which is pinned to `factory.py`'s steps (R3). `sdlc.py` still never imports or runs `factory.py`.
- **`status` reads read-only (REVIEW.md: bad input raised in a host repo).** Unparseable frontmatter is still a problem and never a traceback. Such a change has stage `None`, so `column()` places it in Needs you, as the board does. Every new reader catches `OSError`, as `factory_land_stop()` does.
- **The scripts run on Windows.** `touched_paths()` keeps `-z` and compares as text with `_dirty_paths()`, exactly as now. New tests that use no shebang fakes are marked `portable`, like the status tests beside them.
- **Skills.** Only prose changes: no new command, so no `allowed-tools` rule is added or removed. No WAIT is touched.
- **Nothing local.** Test changes use neutral slugs (`reopen-drafts`, `keep-drafts`).
- **No change to `defaults/` or `guide/`**, so no `sdlc.py record` is needed.

No invariant needs to change.

## Alternatives rejected

- **`status` loads `board.py` and calls `_entry()` for each change.** That breaks the intent's constraint. It would also make `status` read factory timing history (`typical_times()`, a walk over closed changes) and every card field it never prints.
- **A copy of `column()` in `sdlc.py`, pinned by a test.** This is the copy that can drift, which the intent rules out. A pin catches drift only after someone writes the copy wrong.
- **Keep `status`'s sections and add a column tag to each line.** Two vocabularies in one screen is the problem itself.
- **Leave `in_flight` coming from `progress` on the board and from a separate reader in `status`.** That is two derivations of one fact. Setting it from `factory_landing()` on both sides makes it one.
- **Hide empty states.** That saves up to five lines. But the order would then be the board's only when everything is full, and the status skill would lose a stable anchor for each state. It is a taste call, raised in the open questions.
- **Keep a *Shipped* section for shipped folders `ready_to_close()` can't see.** The board doesn't show them either. Today such a folder is in the main checkout or orphaned, which is rare, and keeping the section would keep a seventh word.
- **Move *Needs you* to the top.** That reads the intent's "stays first" literally, against the code, the test and the skill that put it last. Deciding that is the person's call, not a side effect.

## Verification

    ./check.sh

Healthy output: ruff clean, `ruff format --check` clean, pytest all passed (the new tests from R1 to R12 among them), and `claude plugin validate --strict` passes.

    uv run --group dev pytest -q tests/test_board.py -k "status or column or landing"
    uv run --group dev pytest -q -m portable

Healthy output: all pass, including `test_status_places_each_change_under_its_board_column` with all twelve fixture changes placed.

    uv run --quiet --script scripts/sdlc.py status

Run from this worktree. Healthy output:
- after the header, `■ Planned: N`, `■ Designing: N`, `■ Building: N`, `■ Ready: N`, `■ Landing: N`, in that order;
- this change (151) under Designing;
- *Unreleased*, *Next up* and *Problems* as before;
- `■ Needs you: N` as the last section;
- no `■ Open changes`, `■ Shipped`, `■ Ready to close` or `■ What needs me` anywhere.

With `sdlc.py board` running, each card's column on the page matches the heading its change is under in `status`.
```

---

**Resolved from the code:**
- **Does the rule move into `sdlc.py`, with the board calling it?** Yes. `column()`, `seen_stage()` (was `_seen()`), `touched_paths()` (was `_touched()`) and `rebasing_branches()` (was `_rebasing()`) move. The board already calls `needs_of()` and `answered()` this way, so `board.py` still loads only for `board`. To know about a landing in flight, `status` uses a new `factory_landing()` reader, which the board uses too.
- **Do the `■` markers stay?** Yes. Every section uses them, and the tests and the status skill split the output on `■ `.
- **Has 145 landed?** Yes. `column()` already has Ready and Landing, and `answered()` already moves an answered escalation to Ready.

**Left for you:**
- **Do empty states print a heading?** The spec prints all six, empty ones as a heading with a count of 0. That keeps the board's order stable and gives the skills an anchor for each state. Hiding them saves up to five lines but makes the order depend on what's full. Needs you prints `nothing` either way.
- **"Stays first" for Needs you.** The intent says first, but the code prints it last and the board's order puts it sixth. The spec keeps it last. Moving it to the top would mean rewriting `test_status_ends_with_what_needs_me` and the status skill's guidance around it.
- **Should `status` read the problems only the board reads** (a review with no VERDICT, a findings or step file that won't read)? Yes would close the last gap between the two, but `status` would read every review per change. No keeps the gap REFERENCE.md already documents, and the matching test only uses changes whose files all read.
