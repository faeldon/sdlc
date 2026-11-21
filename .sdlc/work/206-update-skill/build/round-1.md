The change is built, and the gate is green: 3660 passed and 29 skipped, with ruff, the format check and `claude plugin validate --strict` all clean. Everything is left uncommitted. One thing needs your eye: I fixed a test outside this change's scope (see `D1`).

**What I recorded first.** On Claude Code 2.1.311, `claude plugin list --json` exists.
- Each row has `id`, `version` and `scope`. A project- or local-scope row also has `projectPath`, and an install from a folder marketplace has `readFromFolder`.
- Claude Code keeps a separate row for every worktree a project-scope install was made in.
- The cached copy under `~/.claude/plugins/cache/` has no `.git`. This repo's clone does, so `update` reports `in_place` here.

Two things I couldn't check from a non-interactive build: that a SessionStart `systemMessage` reaches the person, and that `--scope project` acts on the folder it runs in. Both are listed as manual checks in `notes.md`.

**Slices built**
1. **The pure parts** in `sdlc.py`: `parse_installs()`, `most_specific()` and `update_line()`, which gives the line in both R3 forms.
2. **The check and its cache:** `latest_release()` runs `git ls-remote` with `GIT_TERMINAL_PROMPT=0` and a timeout. `plugin_installs()` finds `claude` with `shutil.which`. `check_update()` keeps `sdlc-update.json` in the git common dir, re-checks after 24 hours, and caches a failed check as `latest: null`.
3. **The command** `update` with `--hook`, `--installed` and no flag; it is not in `READ_ONLY`.
4. **The hook:** `hooks/hooks.json` holds one SessionStart hook (matcher `startup`, timeout 30 s). The pin in `test_sdlc_loads_nothing_from_plugins` now allows exactly this one hook.
5. **Status** prints `■ Update: …` from the cache alone.
6. **Readiness and setup:** readiness gains `uncommitted`. Setup's Step 0 runs `update --installed` and stops with `restart first: …`, and its report gives the commit.
7. **The skill:** `/sdlc:update` has one WAIT and a rule per `claude plugin …` command. `retro.py` lists it as run outside a change.
8. **Docs:** README *Updating* (plus a row in its skill table), REFERENCE.md *After an update*, FEATURES.md, PROCESS.md and an AGENTS.md paragraph.

**Tests added**
- **`tests/test_update.py`**, 23 tests (11 portable):
  - The recorded rows parse correctly, and project paths are compared resolved (R6).
  - Both forms of the line, character for character, and silence whenever it can't tell (R3).
  - A second run the same day makes no network call; a day-old cache is checked again; a failed check is cached as null (R4).
  - The hook is silent without `claude`, with `ls-remote` failing, outside a repo, and when the check raises (R2).
  - A plugin read in place gets no line, no step and no network call (R5).
  - The steps come in order, another repo's install goes in `elsewhere`, and this repo's worktrees appear in neither (R8).
  - `--installed` gives `true` over a newer project install and `null` without `claude` (R9).
  - Status reads the cache and runs neither `claude` nor `ls-remote` (R7).
  - The hook end to end: a fake `claude`, a bare repo tagged as releases, and a copied plugin root (R13).
  - The docs list the five steps in order (R15).
- **`tests/fixtures/plugin-list.json`:** the recorded rows, with neutral paths and the Claude Code version that printed them (R14).
- **`tests/test_skills.py`:** the new skill added to the gated, config and found lists, the changed hook pin (R1), and tests for setup's restart stop and commit (R12) and for the update skill's WAIT and commands (R11).
- **`tests/test_readiness.py`:** `uncommitted` lists a modified `setup.json` and `settings.json`, and is empty on a clean repo (R12).

The code went in before its tests, so I checked the tests by mutation instead: I broke the cache, the "applies here" rule, the hook's in-place check, the worktree filter, the status line and `uncommitted` one at a time. A test failed each time.

**What changed in `plan.md`:** I wrote it first, with the recorded facts. Its new *Where the build departed* section says:
- `setup_uncommitted()` sits above `cmd_readiness`, because `test_registry` keeps each command's adapter right after its handler.
- The hook carries a `description` and a 30-second timeout.
- `tests/test_archive.py` was fixed (`D1`).
- `checks.md` has two acceptance checks: the AGENTS.md paragraph (R10) and the README table row.

**Left in `notes.md`**
- Other recorded outputs may read `plugin_version()` and break on each release the same way.
- The manual check from the spec's Verification still needs running: the line in a real session, the steps, and `--scope project` acting on the folder it runs in.

- DECISION: [default] Pin `plugin_version()` at 1.10.0 in `tests/test_archive.py`'s `_close_scenario()`. `Release 1.11.0` left the base branch red on `test_close_output_is_unchanged`: its fixture records `Sdlc-Runtime: plugin=1.10.0`. No gate could pass otherwise. Going ahead unless told otherwise.
  - OPTION: pin it in the test — the gate goes green, and the fixture stops breaking at every release; it is a fix outside this change's scope
  - OPTION: re-record the fixture at 1.11.0 — the test is untouched; it breaks again at the next release
  - OPTION: leave it to its own change — this change stays in scope; its gate stays red until that change lands
  - WHY: the gate runs the base branch's check, and this is the smallest fix that holds across releases
- DECISION: [default] Install rows read from a folder (`readFromFolder`) are never stale and never a step. When the sdlc install that applies here is one, the hook and `status` say nothing. Going ahead unless told otherwise.
  - OPTION: never stale — matches the intent's "silent for a local-path marketplace"; a folder's version is whatever it holds
  - OPTION: treat them like cache installs — one rule for every row; it tells a folder install to update from a release, which is meaningless
  - WHY: the intent's constraint names a local-path marketplace as a case to stay silent in
- DECISION: [default] A row whose `projectPath` is a worktree of this repo is neither a step nor `elsewhere`. Going ahead unless told otherwise.
  - OPTION: leave them out — `elsewhere` names only other repos; worktree rows linger after their worktree is gone
  - OPTION: list them in `elsewhere` — every row is shown; this repo alone would list over a hundred worktree rows
  - WHY: Claude Code keeps one row per worktree an install was made in, and those are this repo's, not another's
- DECISION: [default] With no `claude` on PATH, the hook and `status` are silent even when `ls-remote` found a newer tag. Going ahead unless told otherwise.
  - OPTION: silent — the intent's "no `claude` on PATH" case, and the line can't name the stale installs; a host without `claude` on PATH never hears
  - OPTION: print the first form from the tag alone — that host hears of the release; the line may be wrong about what to update
  - WHY: the intent's constraint lists no `claude` on PATH among the cases to stay silent in
- DECISION: [default] Setup's `complete` stop points at Step 6's refresh commit rather than spelling out `git commit`, because `test_setup_drafts_from_readiness_and_never_commits` forbids that text before Step 6. Going ahead unless told otherwise.
  - OPTION: point at Step 6 — the existing test is kept; the command is one step further away
  - OPTION: relax that test — the stop holds the command itself; it loosens a pin that keeps setup from committing
  - WHY: the existing pin is the safety; the pointer gives the same commit

- UNTESTABLE: none

## Evidence

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 206
All checks passed!
334 files already formatted
3660 passed, 29 skipped in 315.74s (0:05:15)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_update.py
23 passed in 4.69s
exit: 0

$ uv run --group dev pytest -q -m portable tests/test_update.py
11 passed, 12 deselected in 0.04s
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py tests/test_feature_map.py tests/test_readiness.py tests/test_registry.py "tests/test_archive.py::test_close_output_is_unchanged"
505 passed in 8.60s
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py::test_sdlc_loads_nothing_from_plugins   (before hooks/hooks.json existed)
FAILED tests/test_skills.py::test_sdlc_loads_nothing_from_plugins - FileNotFo...
1 failed in 0.28s
exit: 1

$ uv run --group dev pytest -q tests/test_skills.py   (before the update skill and setup's edits)
7 failed, 427 passed in 1.05s
exit: 1

$ uv run --group dev pytest -q tests/test_update.py tests/test_feature_map.py   (before the docs)
5 failed, 27 passed in 4.69s
exit: 1

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 206   (before the test_archive pin and the move of setup_uncommitted)
FAILED tests/test_archive.py::test_close_output_is_unchanged[shipped] - asser...
FAILED tests/test_registry.py::test_each_command_sits_beside_its_handler[sdlc]
5 failed, 3655 passed, 29 skipped in 229.90s (0:03:49)
exit: 1

$ uv run --quiet --script scripts/sdlc.py update
  "in_place": true,
  "steps": [],
  "reason": "the plugin is read in place from a clone: its version is whatever the checkout holds"
exit: 0

$ uv run --quiet --script scripts/sdlc.py update --hook
exit: 0

$ uv run --quiet --script scripts/sdlc.py vet --strict
■ Problems: 0
    none ✅
exit: 0

$ claude plugin validate --strict <tmp>/p   (a scratch plugin whose hooks.json has a malformed SessionStart)
  ❯ hooks/hooks.json has a hook event (SessionStart) whose value is not a list. The directory refuses a plugin with such a file (HOOKS_SCHEMA_INVALID). Give that event a list of matchers.
✘ Validation failed (--strict treats warnings as errors)
exit: 1

$ sh /tmp/chk1.sh; sh /tmp/chk2.sh   (checks.md's two blocks)
check 1 exit 0
check 2 exit 0
exit: 0
