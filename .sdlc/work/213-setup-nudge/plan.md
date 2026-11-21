---
id: 213
slug: setup-nudge
kind: plan
created: 2026-11-21
updated: 2026-11-21
---

# 213 — The setup nudge reaches the person and clears when setup has nothing to do · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: add `drift_pending(found)` beside `drift()`; `cmd_readiness()`'s `complete`
  uses it in place of its inline clause; `setup_nudge()` calls `drift()` only when the record is
  older (reusing `read_manifest()`, `plugin_version()`, `_older()`), `OSError`/`ValueError` keeping
  the line; `hook_line()` falls back to `f"sdlc setup: {setup_nudge(root)}"` in its own `try` when
  `update_line()` gives None. Docstrings of the three say so.
- `tests/test_setup_lifecycle.py`: R1–R5, R9 tests, using the existing `plugin`/`repo` fixtures,
  `_record()` and `_default()`; `test_status_nudges_on_old_manifest` is replaced by the R2 test.
- `tests/test_update.py`: R6–R8 tests, using `host`, `plugin`, `claude`, `_hook()`; a set-up host
  is the `host` fixture plus `.sdlc/config.toml` and `cmd_record()`, and "no release line" is a
  fresh update cache written with `latest: null`.
- `tests/test_skills.py`: R10's test that `status` and `intent` `SKILL.md` name `■ Setup`.
- `skills/status/SKILL.md` (Step 3), `skills/intent/SKILL.md` (Step 0): prose only, no new command.
- `docs/REFERENCE.md` *After an update*, `AGENTS.md` (*Updates*, *Setup*), `docs/FEATURES.md`
  (the update check), `hooks/hooks.json`'s `description`: R11. A test in `tests/test_update.py`
  pins REFERENCE.md's sentence.

## Work order

1. **The nudge asks drift (R1–R5, R9).** `drift_pending()`, readiness on it, `setup_nudge()`
   reworked; tests in `test_setup_lifecycle.py` red, then green.
2. **The hook carries setup's line (R6–R8).** `hook_line()` fallback; tests in `test_update.py`.
3. **The skills pass it on (R10).** Two `SKILL.md` edits and the `test_skills.py` test.
4. **The docs (R11).** REFERENCE.md, AGENTS.md, FEATURES.md, hooks.json, and the REFERENCE test;
   `tests/test_feature_map.py` run since it checks FEATURES.md against the code.

## Tests

- R1: `test_a_release_that_changed_nothing_leaves_no_nudge`: record at 1.1.0, run at 1.2.0,
  readiness `complete`, nudge None, `cli_status` output has no `■ Setup`. Built on the setup eval
  case's `set-up` fixture (`evals/scaffold.sh set-up`) against the real plugin, since the lifecycle
  tests' fake-plugin repo is never `complete` (no process doc, permissions, attribution).
- R2: `test_a_release_that_changed_a_default_nudges_until_setup_records`: the line under a changed
  default, None after `cmd_record()`; also the no-config, no-record and unreadable-record cases.
- R3: `test_a_report_only_drift_keeps_the_nudge`: a key taken out of `config_keys`; nudge shown,
  `complete` false.
- R4: `test_a_current_record_runs_no_drift`: `drift` swapped for one that raises; None.
- R5: `test_a_doc_drift_cannot_read_keeps_the_nudge`: invalid UTF-8 in the review doc; the line,
  and `status` exits 0.
- R6: `test_hook_says_setup_is_behind` (setup behind by a config key new since the record, the
  report-only drift R3 uses, rather than a changed default: the hook tests run the real plugin's
  defaults); R7: `test_hook_prefers_the_release_line`; R8:
  `test_hook_setup_half_never_fails_the_session` (plus the existing in-place and can't-tell tests).
- R9: `test_check_strict_ignores_drift`, given a stale record.
- R10: `test_status_and_intent_pass_the_setup_nudge_on`.
- R11: `test_reference_says_the_hook_carries_setup_s_line`.

## Rollback

`git revert` undoes all of it: the change writes no file, state or record anywhere a revert
doesn't reach. Nothing to undo beyond the revert.
