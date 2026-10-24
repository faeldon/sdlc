---
id: 003
slug: test-lifetimes
kind: plan
created: 2026-10-24
updated: 2026-10-24
---

# 003 — Enforce shim deadlines, and sweep acceptance-only tests · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Context

Change 003 (Tier 2, `work/003-test-lifetimes/spec.md`, R1–R8) puts the test-triage rule's
"compatibility test lives as long as its shim" into code. It adds a TOML registry of shims
(`release.deprecations`) that `release` refuses on and `status` warns about, dogfoods the registry
in this repo with a gate test, and sweeps `tests/` for assertions only a revert can fail. The
change depends on 002 (setup-lifecycle). 002 rewrites `test_defaults.py`'s own-copy tests, adds
`plugin_version()` and a `■ Setup` line to `status`, and touches `test_readiness.py`'s allowlist
test. **Building starts only once 002 has closed** (see step 0). The plan is approved and saved
now.

002 has landed (`5d71dd2`), and this branch was fast-forwarded onto it. From 002 the plan reuses
`plugin_version()` and `_older()`. `RETIRED_KEYS` and the no-manifest path are not shims (spec,
*Contracts touched*), so the registry starts empty.

## Files to change

- `scripts/sdlc.py`:
  - `CONFIG_KEYS["release"]["deprecations"] = ".sdlc/deprecations.toml"`;
  - `SHIM_KEYS`, `deprecations()` beside `read_versions()`;
  - `shims_due()`;
  - `unreleased()` gains a `deprecations` key;
  - a `cmd_release` refusal;
  - `print_status` lines in the Unreleased block.
- `.sdlc/deprecations.toml` (new): a header comment, no entries.
- `tests/test_deprecations.py` (new): R1–R6.
- `tests/test_config_resolution.py`: the new key's default resolves and is printed by `config`.
- R8's sweep: `tests/test_retro.py`, `tests/test_sdlc.py`, `tests/test_adoption.py`,
  `tests/test_skills.py`, `tests/test_readiness.py`, `tests/test_archive.py`,
  `tests/test_playbook.py`.
- `docs/REFERENCE.md`: the key in the config sample (beside `version_files`), and a paragraph in
  `## Releases`.
- `defaults/SDLC.md` and `.sdlc/SDLC.md`: the Stage 4 Compatibility line, identical in both.
- `AGENTS.md`: one sentence in the **Releasing** paragraph.
- `work/003-test-lifetimes/notes.md`: the sweep record and the acceptance check;
  `intent.md` `stage: build`.

## Work order

0. **Base.** Done: fast-forwarded onto `main` at `5d71dd2` (002 closed). `./check.sh` green before
   any edit; set `stage: build`.
1. **Parse (R1, R2).**
   - Add the key. It is a plain string, so `load_config()` needs no change, and `config` prints it
     with the rest of `release`.
   - `deprecations(home, cfg) -> {"path", "exists", "shims", "problems"}`:
     - `tomllib` over `home / cfg["release"]["deprecations"]`; a missing file is
       `exists: False`, no shims and no problems;
     - `SHIM_KEYS = ("name", "remove_in", "where", "test")`, the first three required;
     - each problem is a string naming the entry (`shim 2 (old-flag): remove_in must be a quoted
       X.Y.Z`) for: a parse error, the top level not being only `shim = [...]`, a non-table
       entry, a missing, unknown or non-string key, a duplicate name, and `remove_in` not
       matching `SEMVER_RE`;
     - entries with problems are dropped from `shims`.
   - Tests: one per problem, a missing file, an empty file, `remove_in = 1.10` refused.
2. **Compare (R3).**
   - `shims_due(shims, current, nxt) -> (overdue, due)` with 002's `_older()`:
     - overdue: `remove_in` ≤ `current`;
     - due: the rest with `remove_in` ≤ `nxt` (none when `nxt` is None).
   - In `unreleased()`, call `deprecations(home, cfg)` once.
     - Its problems are added to `out["problems"]` **before** the bump is computed, so a bad
       registry blocks `next`, as a bad intent does.
     - After `next_version()`, set `out["deprecations"] = {"overdue", "due", "unversioned"}`.
       `unversioned` lists every shim when `version_files` is unset or the version is unknown.
   - Tests: `1.10.0` > `1.9.0`, overdue against current, due against next, nothing due when
     nothing is releasable, unversioned with no `version_files`.
3. **Refuse (R4).**
   - In `cmd_release`, after `new` is settled (the `--version` handling included) and before
     `if refusals: return emit(1)`, add one refusal per shim with `remove_in` ≤ `new`:
     `shim <name> is due by <new>: remove it (<where>; its test: <test>)`.
   - Tests reuse `test_release.py`'s `_repo`/`_close` shapes, copied as small helpers:
     - a due shim refuses, with `_state()` unchanged;
     - `--check` refuses too;
     - `--version` jumping past `remove_in` refuses;
     - a shim due later doesn't refuse.
4. **Warn (R5, as amended).**
   - In `print_status`'s Unreleased block, after the bump/problems line and before the change
     lines:
     - `⚠  shim <name> is overdue: remove in <v> (<where>)` for each overdue shim;
     - `⚠  shim <name>: remove in <v> (<where>)` for each due one.
   - The block's guard also shows when shims are listed, so a configured repo with nothing landed
     still prints them.
   - Tests:
     - status output for a bare repo is identical with and without the code path (capture both,
       with no file, and compare);
     - due and overdue lines appear;
     - `check --strict` exits 0 with an overdue shim.
5. **Dogfood (R6).**
   - Write `.sdlc/deprecations.toml`: a comment saying what it is, with one example entry
     commented out.
   - `test_this_repos_shims_are_well_formed_and_not_overdue` loads this repo's config via
     `sdlc.load_config(ROOT)`, then `deprecations()`, and compares against `plugin_version()`,
     asserting:
     - no problems;
     - nothing overdue;
     - each `test` resolves to an existing `tests/<file>` containing `def <function>`.
   - A fixture copy proves the test's logic fails on an overdue shim and on a missing test.
6. **Sweep (R8).** Find each site by its content, since 002 moved lines:
   - remove:
     - `"tokens" not in out` (`test_retro.py`);
     - `not (… "work" / ".last-id")` (`test_sdlc.py`);
     - the two `<git-dir>/sdlc` absence asserts (`test_sdlc.py`, `test_adoption.py`);
     - `"sdlc.py archive" not in text` (keep `"rm -" not in text`) (`test_skills.py`);
     - `"archive"` from the writer tuple (`test_readiness.py`);
     - the `.sdlc/ids` allowance (`test_archive.py`).
     - `"claude plugin uninstall sdlc@sdlc"` in
       `test_uninstall_plans_before_its_gate_and_removes_after` (`test_skills.py`).
   - rewrite:
     - `len(_bash_rules(skill)) == 8` → no rule runs `git log` or `gh` (`test_skills.py`);
     - `test_the_shipped_defaults_have_one_block_per_key` asserts its glob matched
       (`test_setup_lifecycle.py`).
   - add: `test_uninstall_without_a_manifest_leaves_the_ignore_line` (`test_setup_lifecycle.py`).
   - Then judge each of the five medium sites by reading the skill or doc each one pins:
     - remove a site when the phrase is one past edit;
     - keep it when the wording is what a skill's model must follow, or another reader depends
       on it.

     The default for each:
     - `test_readiness.py` `"### Stage 4 — Test"`/`"/sdlc:setup"`: remove (test_playbook pins
       the headings);
     - `test_skills.py` "Since the last retrospective": judge;
     - `O1 (Unaided setup)`: keep, rewritten to check that the id-with-name form
       (`O\d \(`) appears rather than the literal example. That's a regression check on the rule,
       not a removal;
     - the three retro phrases: judge;
     - `test_playbook.py` loop phrases: judge.
   - Each outcome gets one line in `notes.md` under `## Sweep`.
   - Run `./check.sh` after the sweep alone.
7. **Docs.**
   - REFERENCE: the config sample line
     `deprecations = ".sdlc/deprecations.toml"   # the default: shims and the version that removes each; off while absent`,
     and a `## Releases` paragraph with the `[[shim]]` format, due versus overdue, the release
     refusal and the status lines.
   - Stage 4's Compatibility line, in both SDLC docs: "…which names the version that removes it,
     in `release.deprecations` when the repo keeps one, else in a comment; the test goes with the
     shim."
   - AGENTS.md Releasing: "A shim in `sdlc.py` gets an entry in `.sdlc/deprecations.toml`, and
     `cmd_release` refuses a version that would still carry it."
8. **Acceptance and gate.**
   - Add a scratch `[[shim]]` with `remove_in = "1.0.1"` to `.sdlc/deprecations.toml` in the
     worktree.
   - Run `sdlc.py release --check` from a scratch clone. Release refuses from a worktree, so the
     check is the refusal message naming the shim; `sdlc.py unreleased` shows it in `due`.
   - Remove the scratch shim and record both outputs in `notes.md`.
   - Run `./check.sh`.

## Tests

- **R1:** `test_without_a_registry_nothing_changes`, `test_config_prints_the_deprecations_key`
- **R2:** `test_registry_problem_<case>` (parse, top level, not a table, missing key, unknown key,
  non-string, duplicate, bad version, unquoted `1.10`), `test_an_empty_registry_has_no_shims`
- **R3:** `test_overdue_and_due_compare_as_versions`, `test_nothing_is_due_with_nothing_to_release`,
  `test_without_version_files_shims_are_unversioned`, `test_a_bad_registry_blocks_the_bump`
- **R4:** `test_release_refuses_a_due_shim_before_writing`, `test_check_refuses_it_too`,
  `test_a_version_past_remove_in_refuses`, `test_a_later_shim_does_not_refuse`
- **R5:** `test_status_is_unchanged_without_a_registry`, `test_status_lists_due_and_overdue_shims`,
  `test_check_strict_ignores_shims`
- **R6:** `test_this_repos_shims_are_well_formed_and_not_overdue`, plus its fixture proof
- **R7:** `test_defaults.py` own-copy tests (the edit is identical in both), `test_nothing_local.py`
- **R8:** `./check.sh` green after step 6; `notes.md`'s list
- **Gate:** `./check.sh`

## Rollback

`git revert` the change's commit restores everything, this repo's `.sdlc/deprecations.toml`
included. It doesn't cover:
- **A host that wrote a registry:** its `.sdlc/deprecations.toml` stays, and the old code ignores
  it. An unknown `release.deprecations` key in its config becomes a warning; the host deletes the
  line.
- **Issue #3's body:** it stays as last synced.
