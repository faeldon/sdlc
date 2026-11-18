## Builder report: 149, round 1

I built R1–R14 test first. The gate is green: 2838 passed, 28 skipped. Nothing is committed and `HEAD` is still `7128522`. The spec changed while I was building: the person folded bug 2026-11-18-73 in as R14 (`decisions.md` D1). It is built and tested like the rest.

### Slices
1. **The role (R1–R3, R7, R12).** `ROLES` gains `resolver`, with `FIXED_MODELS["resolver"] = "sonnet"` and `TASK_ROLE["train-resolve"] = "resolver"`. `RESOLVE_RECORDS` gains `runs/resolver.sessions`. The new `plugins/factory/agents/resolver.md` has tools `Read, Grep, Glob, Edit, Bash` and model sonnet. It covers merging only: keep every change's intent, never re-implement either side, never run a `checks.md` section, and end with `## Evidence`. Nothing in `scripts/` needed changing for the role, as the spec said.
2. **Only the resolver runs `train-resolve` (R4).** `cmd_agent` refuses `train-resolve` with any `--role` other than `resolver` before it writes anything. Argparse's `--role` choices gain `resolver`.
3. **The fence (R8, R9).** `resolve --continue` now reads `git status --porcelain -z` once, after the conflict-marker check, through a new `_status_entries()`; `_dirty()` now reads that too. A new `_stray()` lists every other entry whose worktree column isn't blank, plus untracked files, leaving out the conflicted files and the change's landing records. Any stray path is refused through `_land_refused()`: the refusal names the paths and says how to undo them, then continue or eject. Nothing is staged, no marker is written, and the rebase stays under way.
4. **Non-ASCII conflicted paths (R14, bug -73).** `factory.py`'s `_conflicted()` and `sdlc.py`'s `_unmerged()` now read `git diff --name-only --diff-filter=U -z` directly. A path like `docs/café.md` now comes back as named, not quoted.
5. **The docs (R5, R6, R13).**
   - `builder.md` loses *A conflict, while landing*.
   - The README gains a `resolver` row. Its editor line now reads "Only the builder and the resolver edit", and the landing and model paragraphs name the resolver.
   - AGENTS.md (*The factory*), the land skill's `resolve` step and the build skill's `models_at` line are updated.
   - Comments, docstrings and `land-review`'s prompt now say "resolved while landing" instead of "by the builder". So do `board.py`'s comments.
   - The landing question's "one landing agent" is unchanged: it is still true.

### Tests and what they prove
- `test_a_train_conflict_goes_to_the_resolver_with_every_change` (renamed from `…_goes_to_one_agent_…`) covers:
  - R1: the run uses `--agent sdlc-factory:resolver` with `--session-id`.
  - R7: its model is `sonnet`.
  - R2: the session and cost row are under `resolver`, and `builder.sessions` is unchanged byte for byte.
  - R3: `resolver.sessions` is committed in `HEAD` and the worktree is clean.
  - R9 and R10: a second file the commit staged cleanly passes the fence and is left untouched.
- `test_train_resolve_runs_no_role_but_the_resolver` (R4): the builder, code and verifier roles are each refused, with no session started and no `.sessions` file written.
- `test_a_resolution_outside_its_files_is_refused` (R8): a stray untracked file and a stray tracked edit are each refused with everything left in place; once undone, the resolution goes through.
- `test_the_resolver_has_a_model_of_its_own` (R7): `models_at` lists it, `[models] resolver` is honoured, and the builder's model never reaches it.
- `test_a_resolver_session_is_its_own_role` (R12). It passed on its first run because nothing in `scripts/` needed changing; it guards that from now on.
- `AGENT_TOOLS["resolver"]` and `NEVER_RUNS_CHECKS["resolver"]` (R5, R6). Both failed until `resolver.md` existed.
- R11: the land-fix test now also asserts `role == "builder"`. I checked that it fails if `land-fix` is moved to the resolver.
- R14: `test_a_train_conflict_in_a_non_ascii_path_resolves` for `factory.py` and `test_a_conflict_in_a_non_ascii_path_is_resolved` for `sdlc.py`. Both reproduced the quoted path first.
- `test_train_run_starts_a_rounds_reviewers_together`: its stand-in plan now goes to `resolver`, since the conflict now goes there.
- `checks.md` holds one acceptance check for R13's wording, which only a revert could break. It exits 0.

### plan.md
I wrote it before the code and updated it for R14, `sdlc.py`, `board.py`'s comments, the stand-in test's plan, checks.md and the R11 assertion. The rollback section says that `resolver.sessions` and `Sdlc-Role: resolver` lines already in history stay as they are.

### Left over
- There is no `notes.md`.
- `sdlc.py check` warns that `fixes: '2026-11-18-73' isn't a [bug] in .sdlc/work/inbox.md`. The entry is on the base branch, which gained it after this branch was made; my copy of the register predates it. It's not this change's to fix, and moving the branch (`fresh` or `base`) would clear it.

No decisions raised.

## Evidence

$ ./check.sh
All checks passed!
284 files already formatted
2838 passed, 28 skipped in 207.46s (0:03:27)
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_train.py tests/test_resolve.py tests/test_factory.py tests/test_skills.py tests/test_land.py -k "resolver or outside_its_files or non_ascii or agents_have_their_tools or runs_checks or starts_a_rounds_reviewers_together or fix_asked_at_landing_is_built"
13 passed, 847 deselected in 37.39s
exit: 0

$ uv run --group dev pytest -q tests/test_land.py -k "fix_asked_at_landing_is_built"   (with `land-fix` moved to `resolver` by hand, then restored)
E       AssertionError: 149 R11: a fix stays the builder's, never the resolver's
exit: 1

$ uv run --group dev pytest -q tests/test_train.py tests/test_resolve.py -k "non_ascii"   (before the -z fix)
E       assert ['"docs/caf\\303\\251.md"'] == ['docs/café.md']
exit: 1

$ ! grep -rnE "landing agent, the builder|Only the builder edits" plugins AGENTS.md && ! grep -q "## A conflict, while landing" plugins/factory/agents/builder.md && grep -q "only the builder and the resolver edit" AGENTS.md && grep -q "Only the builder and the resolver edit" plugins/factory/README.md && grep -q '^| `resolver` |' plugins/factory/README.md
exit: 0

$ git log --oneline -1
7128522 Close 147-landing-runs-unattended
