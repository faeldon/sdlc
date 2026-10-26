---
id: 027
slug: work-path
kind: spec
created: 2026-10-26
updated: 2026-10-26
---

# 027 — Keep the change folders under .sdlc/ · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1. `.sdlc/work/` is the change folder.** `WORK = ".sdlc/work"` is the one place the path is
   written. Until 1.5.0, `work_rel(home)` resolves it: `WORK` when `.sdlc/work/` exists or there is
   no `work/`, else the old `work` (amended in planning: the old code closes a change in this repo,
   so a hard switch would deadlock 027's own ship and close). `work_dir(root)` is
   `root / work_rel(main_root(root))`. Every git path, pathspec and message is built from
   `work_rel()`: `closed_changes`, `dropped_changes`,
   `_change_base`, `measure_change`, `fix_trailers`, close's `verify` and `_close_commit`,
   `unreleased`, `cmd_drop`, `_factory_files`, `recorded_issues`, `cmd_bug_commit`,
   `cmd_retro_commit`, retro's rework filter, `work_ignored()`. Test:
   `test_no_literal_work_path_in_the_script` fails on a `"work/"` in `sdlc.py` not built from
   `WORK`, but for the old path the shim and `next_entry_ids()` name (R6, R7).
2. **R2. A change's checkout is `checkout_of(folder)`**, never `path.parent.parent`, at the six
   lookups (`load_change`, `analyze`, `cmd_nits`, `cmd_accept`, `cmd_ship`). Test: `load_change`
   on a folder under `.sdlc/work/` reads its checkout's config and register.
3. **R3. Metrics and the factory follow it.** `metrics.py`'s markers become `/.sdlc/work/{branch}/`;
   `factory.py` builds `root / ".sdlc" / "work" / branch`. Tests: an intent edit under
   `.sdlc/work/` classifies as `intent`; the factory finds a change's folder there.
4. **R4. Uninstall never removes the change folder.** `uninstall_plan` leaves everything under
   `.sdlc/work/` out of `remove` and of its uncommitted-edits refusal, and lists it under `left`.
   Test: uninstall in a repo with closed and dropped changes removes `.sdlc/config.toml` and no file
   under `.sdlc/work/`.
5. **R5. Setup moves an existing host's `work/` once.** `sdlc.py move-work`, from the main checkout
   on `git.base` with a clean tree, refuses any open change, no `work/`, an existing
   `.sdlc/work/`, an ignored `.sdlc/work/`, and any change `unreleased` still lists (`release
   first: these closed changes aren't released, and after the move release can't read them: <ids>`);
   else `git mv work .sdlc/work` and one commit, `Move work to .sdlc/work`, alone. Setup offers
   it behind its one WAIT when `readiness` reports `work/` waiting to move. Never pushes. Tests:
   each refusal; one move gives one commit whose tree has every file at its new path and none at
   the old.
6. **R6. Until a host moves, it is told, and keeps working.** With `work/` and no `.sdlc/work/`,
   `status` prints a nudge, `work/ is the old change folder: run /sdlc:setup to move it to
   .sdlc/work/`, and `readiness` an item saying so; with both, it says half-moved and names both.
   Never a `check` problem, which is a gate (amended in planning: a refusal would deadlock this
   repo, which stays on `work/` until 027 is released). `work_rel()`, the nudge and `move-work` get
   a `.sdlc/deprecations.toml` entry, `remove_in = "1.5.0"`: 1.4.0 removes the existing shims and
   ships the move, 1.5.0 makes `.sdlc/work/` the only folder. Tests: the nudge in `status` and
   `readiness`, `check --strict` still exits 0; the half-moved message names both.
7. **R7. Register ids never repeat across the move.** `next_entry_ids()` reads the register's
   history at both paths: `work/inbox.md`, `work/ideas.md` and `.sdlc/work/inbox.md`, a fixed
   pathspec, kept for good since it reads history, not a shim. Test: an id taken and deleted
   before the move isn't handed out again after it, the same day.
8. **R8. Texts say where the folder is.** Skills, the factory's agents and skills, defaults,
   templates and docs name `.sdlc/work/` where they name the folder; where a skill already says
   "`work/` in this skill is `work.dir` from `config`", that line stays and `config` prints the new
   path. `docs/REFERENCE.md` documents the folder, the move, the nudge and their removal in 1.5.0.
   Test: `test_no_text_names_the_old_folder` globs skills, factory agents and skills, defaults,
   templates and README, failing on a bare `work/` that isn't `.sdlc/work/`, but for the migration
   lines.
9. **R9. A seed for the deferred feature.** At ship, an `[idea]` "Support moving the change folder,
   once a host needs it", saying why moving was left out and what it would need (`Move work`
   commits, a history resolver, and the rule every reader of history would follow). Checked at
   ship.
10. **R10. Resolve the base branch once (nit 2026-10-25-16).** `load_config()` caches
    `_resolve_trunk()` per main checkout per process. Test: a command calling `load_config` many
    times runs `git rev-parse --verify` once.

## Design

**The path.** `WORK` is a fixed relative constant; `work_dir()` and `checkout_of()` are its on-disk
side. `checkout_of(folder)` walks up to the checkout root, the directory holding `.sdlc/`.

**History.** Read at `WORK` only, but for `next_entry_ids()`'s fixed pathspec. Changes closed before
a host's move aren't found by release, retro or `bugs --introduced`: accepted, and contained by
`move-work` refusing while any change is unreleased, and by running retro before the move.

**`move-work`.** A writer in `bug-commit`'s shape: every refusal first, then `git mv` and one
commit.

**The nudge.** One function, `old_folder(home)`, returning the nudge or None; `status` and
`readiness` print it, as `setup_nudge` is printed. A host not yet moved reads and writes at `work/`,
history included, exactly as before.

**Edge cases.** A worktree from before the move holds its folder under `work/`: the move refuses
while any change is open, so none exists. `.sdlc/` is already the plugin's lock directory; `flock`
on it is unaffected. `_change_diff` already skips `.sdlc/` for code size, which now leaves out the
change folder too; it was never code.

## Contracts touched

- **The change folder committed, one per branch, found by `change_dirs()`.** Kept, at the new path.
- **Never hand out a number twice.** Change ids come from the counter, `Close`/`Drop` subjects and
  GitHub, none of them path-dependent; register ids by R7.
- **History never migrates.** Nothing is rewritten; readers stop seeing intents from before a
  host's move. **A conscious change to what the plugin reads from history**, accepted for the
  author's own projects, and contained by refusing to move with anything unreleased.
- **Uninstall removes only what setup wrote.** Tightened (R4).
- **A shim has a removal version, and release refuses one still carrying it.** `work_rel()`'s old
  path, the nudge and `move-work`, `remove_in = "1.5.0"`.
- **The nudge in `status` is never a problem: `check --strict` is a gate.** Kept: the old-folder
  nudge is a nudge.
- **Only publish pushes.** `move-work` commits, locally.
- **Confirm before writing.** The move only behind setup's WAIT.

## Alternatives rejected

- **A configurable path with recorded moves.** About 250–350 lines and tests, and a rule every future
  reader of history follows, for no current need; addable later at no extra cost (R9).
- **Reading both paths everywhere.** The backwards compatibility chosen not to pay for.
- **A hard switch with a guard that refuses every write until moved.** An updated host could do
  nothing until it moved, and in this repo it deadlocks: the old code closes 027, and the guard
  would refuse 027's own ship. A resolver until 1.5.0 keeps an unmoved host working.
- **Removing the move in 1.4.0.** 027 ships in 1.4.0, and release refuses a version still carrying
  a shim due then, so no release would carry the move.

## Verification

- `./check.sh` green, with the R1–R10 tests.
- A scratch repo with `work/`: `status` names the nudge, a change still runs new → close at
  `work/`, `move-work` refuses while a change is unreleased, moves once released, and a new → close
  then runs under `.sdlc/work/`.
- This repo keeps `work/` until 027 is closed and released (after the 1.4.0 shim removal), then
  moves through `/sdlc:setup`.
