I built the change, and the gate passes: 2009 tests, ruff clean, plugin validation passes. Everything is left uncommitted, and `HEAD` is still `070171f`. I reran every command below so each one shows its exit code.

**What changed for a host:** `/sdlc:intent` no longer edits the register on a change's branch. The change's `idea:` line (or `fixes:` for a bug) is now the only thing that marks a seed as taken.

### Slices
1. **R1 – intent stops editing the register.** In `skills/intent/SKILL.md`, Step 5 now sets `idea:` and stops; the `Edit` of each entry, the `[building]` retag and the `Building in …` line are gone. `batch.md` Step 5.3 writes only the intent and its frontmatter. Removing those lines also removed the skill's only mention of `work.register`, which the skills tests require, so Step 0 now names it where intent reads the register.
2. **R3 – status shows what's being built.** `next_up()` now returns a `building` list: id, title, kind, and the change that holds each entry. An entry carrying only an old `[building]` tag shows `change: None`. Plain `status` prints `N being built`. `status --all` lists each one as `<id> <title> — NNN-slug`, or `— tagged [building]` for an old tag.
3. **R4 – bugs and nits name their change.** `bugs` and `nits` (and so `preflight`) give every entry a `building` key: the change's folder name, or null. A small new helper, `_claimed_by()`, finds that change; `inbox-commit`'s refusal now uses it too.
4. **R5–R8 – tests for behaviour that already held.** These cover `groups` refusing a seed an open change names, ship deleting an untagged seed, a dropped change giving its seed back, and `check` accepting an untagged named entry. Each test passed on the first run, so I broke the four lines they pin, watched all five tests fail, and put the code back.
5. **R2 – the rebase test.** It is in `tests/test_resolve.py` and marked portable. With no tag edit, `base` succeeds after an inbox commit on main and the registers match. The control repeats the old tag edit, and there `base` refuses with `resolvable: true`, so the test can't pass on nothing.
6. **R9 – docs.** I updated `guide/process.md`, `templates/inbox.md`, `docs/REFERENCE.md`, the idea and status skills, and the comment above `ENTRY_RE` in `scripts/sdlc.py`, then ran `sdlc.py record`; `drift` now reports nothing.

**This branch's own register:** when intent opened this change, it tagged seed 2026-11-17-41 `[building]` on this branch, which is exactly the edit this change removes. I set that entry back to main's text, so the register here is unchanged until ship deletes the seed.

### Tests added
- **R1:** `test_intent_never_edits_the_register`. I also dropped the `Edit` check from `test_intent_takes_a_theme_s_seeds_as_one_change`.
- **R2:** `test_an_inbox_commit_on_the_base_never_stops_an_open_change_s_rebase`
- **R3:** `test_next_up_lists_what_open_changes_build`, `test_status_counts_and_lists_what_is_being_built`. The expected output in `test_next_up_is_empty_without_registers` gained `building: []`.
- **R4:** `test_bugs_names_the_change_that_fixes_each`, `test_nits_names_the_change_that_takes_each`
- **R5:** `test_an_untagged_seed_an_open_change_names_is_taken`
- **R6:** `test_ship_deletes_an_untagged_seed_its_idea_line_names`, run once by id and once by title
- **R7:** `test_a_dropped_change_gives_its_seed_back`
- **R8:** `test_check_is_quiet_on_an_untagged_seed_a_change_names`. The existing tests for the old tag pass unchanged.

### `plan.md`
I wrote it before any code and updated it as the build went:
- The R7 test went in `test_bugs.py` rather than `test_next_up.py`, and the R4 nits test name changed.
- It records the new `_claimed_by()` helper and the Step 0 `work.register` change.
- One departure from the spec's design: `next_up` gets the claiming change's name from the open-change records it is already given, not by calling `_open_claims()` again. The data is the same.

### Left in `notes.md`
- [ ] `/sdlc:idea --themes` skips seeds with the old tag but not seeds an open change names.
- [ ] The `■ Next up` section is hidden when it has no candidates, so `N being built` doesn't show when every seed is being built.

### Other checks
- `check --strict` now passes. On the first run it flagged another change's worktree (106's unfilled `plan.md`); that problem is gone now.
- `status` on this repo shows 25 being built, with 2026-11-17-41 named against `100-seeds-marked-by-changes`.

No decisions raised: both open questions were already settled in the intent.

## Evidence

$ ./check.sh
All checks passed!
2009 passed in 40.44s
exit: 0

$ uv run --group dev pytest -q tests/test_bugs.py tests/test_groups.py -k "untagged or dropped_change_gives"   (with the four pinned lines temporarily broken)
5 failed, 65 deselected in 4.71s
exit: 1

$ uv run --group dev pytest -q tests/test_bugs.py tests/test_groups.py -k "untagged or dropped_change_gives"   (code restored)
5 passed, 65 deselected in 0.80s
exit: 0

$ uv run --group dev pytest -q tests/test_resolve.py
2 passed in 2.31s
exit: 0

$ uv run --group dev pytest -q -m portable
218 passed, 1791 deselected in 151.53s (0:02:31)
exit: 0

$ uv run --quiet --script scripts/sdlc.py drift   (its breaking, refresh, report)
[] [] []
exit: 0

$ uv run --quiet --script scripts/sdlc.py status | grep "being built"
    25 being built
exit: 0

$ uv run --quiet --script scripts/sdlc.py status --all | grep 2026-11-17-41
      2026-11-17-41 Open changes mark their seeds without editing the register — 100-seeds-marked-by-changes
exit: 0

$ uv run --quiet --script scripts/sdlc.py check --strict
■ Problems: 0
    none ✅
exit: 0
