---
id: 027
slug: work-path
kind: plan
created: 2026-10-26
updated: 2026-10-26
---

# 027 — Keep the change folders under .sdlc/ · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`:
  - `WORK`, `OLD_WORK`, `work_rel()` (cached per main checkout), `work_dir()` and
    `checkout_of()`;
  - every `work/` git path and message built from `work_rel()`;
  - `_resolve_trunk()` cached;
  - `uninstall_plan` and `MENTIONS_RE`;
  - `next_entry_ids()`'s pathspec at both paths;
  - `cmd_move_work` and its argparse entry;
  - `old_folder()` for the nudge in `status` and `readiness`.
- `scripts/metrics.py`: `artifact()` and stage detection take the work path.
- `plugins/factory/scripts/factory.py`: the same rule for finding the folder.
- `.sdlc/deprecations.toml`: the `work-folder-move` shim, `remove_in = "1.5.0"`.
- `skills/setup/SKILL.md`: the move, behind its WAIT, with a new allowed-tools rule.
- Skills, factory agents and skills, `defaults/`, `templates/`, `README.md`: name `.sdlc/work/`.
- `.sdlc/SDLC.md`: mirrors `defaults/SDLC.md`.
- `docs/REFERENCE.md`, AGENTS.md, `docs/CONTRIBUTING.md`.
- Tests: `tests/test_work_folder.py` (new); `tests/test_skills.py`, `tests/test_metrics.py`,
  `tests/test_factory.py`, `tests/test_setup_lifecycle.py`; and the existing tests that build
  `root / "work"`, where a test writes a folder before the code makes one.
- `.sdlc/setup.json`: re-recorded.

## Work order

1. **Resolver and paths (R1, R2, R3, R10).** `work_rel`, `work_dir`, `checkout_of`, every git
   path, metrics, the factory, the cached base branch. Test fixtures move to
   `sdlc.work_dir(root)`.
2. **Uninstall and register ids (R4, R7).**
3. **The move, the nudge, setup (R5, R6).** `cmd_move_work`, `old_folder`, the readiness item,
   the deprecations entry, setup's text.
4. **Texts and docs (R8).** Then `scripts/sdlc.py record`.
5. **At ship (R9).** File the seed "Support moving the change folder, once a host needs it".

Each step ends with `./check.sh` green and a commit on the branch.

## Tests

- **R1:** `test_no_literal_work_path_in_the_script`; a bare repo resolves `.sdlc/work`, and a repo
  with `work/` resolves `work`.
- **R2:** `load_change` under `.sdlc/work/` reads its checkout.
- **R3:** metrics classifies an intent under either path; the factory and `sdlc.py` agree in
  three repos.
- **R4:** uninstall in a `.sdlc/work/` repo keeps every file under it.
- **R5:** each `move-work` refusal, unreleased changes included; one move gives one commit with
  every file at the new path.
- **R6:** the nudge in `status` and `readiness`; `check --strict` still exits 0; the half-moved
  message names both folders.
- **R7:** an id taken and deleted at `work/` isn't handed out again after the move.
- **R8:** `test_no_text_names_the_old_folder`.
- **R10:** `load_config` called many times runs `rev-parse --verify` once.
- **Manual:** a scratch repo going through new → close at `work/`, then `move-work`, then
  new → close at `.sdlc/work/`.

## Rollback

`git revert` of the change's commits covers the code, the texts and the tests. It does not cover a
host that has already run `move-work`. To undo that move, revert its `Move work to .sdlc/work`
commit there with `git revert <sha>`: the old code reads `work/` again, and nothing else changed.
