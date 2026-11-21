---
id: 213
slug: setup-nudge
kind: spec
created: 2026-11-21
updated: 2026-11-21
---

# 213 — The setup nudge reaches the person and clears when setup has nothing to do · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Nits taken in: none.

1. **R1. A release that changed nothing leaves no nudge.** If `.sdlc/setup.json` records an older version than the running plugin, and `drift()` has nothing in `breaking`, `refresh` or `report`, then `setup_nudge()` returns None and `sdlc.py status` prints no `■ Setup` line. `test_a_release_that_changed_nothing_leaves_no_nudge` (`tests/test_setup_lifecycle.py`) follows the bug's steps. It records at 1.1.0, then runs the plugin at 1.2.0 with every default unchanged. It asserts that `readiness` says `complete: true`, that `setup_nudge()` is None, and that status's output has no `■ Setup`. It fails on today's code, which returns `set up with 1.1.0, the plugin is 1.2.0  /sdlc:setup`.
2. **R2. A release that changed a default nudges until setup records.** If the recorded version is older and `drift()` has something pending, the nudge reads as it does today: `set up with <recorded>, the plugin is <running>  /sdlc:setup`. It stays until `record` writes the running version, and then it is None. `test_a_release_that_changed_a_default_nudges_until_setup_records` changes a default under a 1.1.0 record and runs at 1.2.0. It asserts the line, then runs `cmd_record()` and asserts None. This test replaces `test_status_nudges_on_old_manifest`, which currently pins the bug: it expects the line for a release that changed nothing.
3. **R3. The nudge and `readiness` share one rule.** `readiness`'s `complete` and `setup_nudge()` read the same function, `drift_pending(found)`: true when any of `breaking`, `refresh` or `report` is non-empty. That way setup can never say `complete` while status still sends the person to `/sdlc:setup`. `test_a_report_only_drift_keeps_the_nudge` builds a stale record whose drift is only a `report` item: a `new` config key, made by taking one key out of the record's `config_keys`. It asserts that the nudge is shown and that `complete` is false.
4. **R4. A current record runs no drift.** When the recorded version is the same as the running plugin's or newer, `setup_nudge()` returns None without calling `drift()`. So in the usual case the nudge is still one file read. `test_a_current_record_runs_no_drift` swaps in a `drift` that raises and asserts None for a current record. The cases that exist today keep their text: no `config.toml` gives None, no record gives the `no record of the plugin version…` line, and an unreadable record gives its reason. These stay asserted in the R2 test.
5. **R5. When drift can't be read, the nudge stays and nothing crashes.** If `drift()` raises `OSError` or `ValueError` (a host doc that isn't UTF-8 included), `setup_nudge()` returns the version line instead of raising. On an error it shows the line rather than hiding it. `test_a_doc_drift_cannot_read_keeps_the_nudge` writes invalid UTF-8 into the review doc of a stale repo. It asserts the version line, and that `sdlc.py status` exits 0 with no traceback.
6. **R6. The startup hook passes the setup nudge on.** If `update --hook` has no release line to print, it prints `{"systemMessage": "sdlc setup: <setup_nudge() text>"}` for a set-up repo whose nudge isn't None. `test_hook_says_setup_is_behind` (`tests/test_update.py`) uses a repo with a stale record and a changed default, plus an update cache with no newer release. It asserts that exact line.
7. **R7. The hook still prints one line at most.** If a release line exists, the hook prints only that line, because the steps `/sdlc:update` lists already end with `/sdlc:setup` (`update_report()`). `test_hook_prefers_the_release_line` sets up both conditions and asserts `{"systemMessage": LINE}` alone.
8. **R8. The setup part never fails a session.** The hook works out the release line first, and the setup line only when there is no release line. A failure in the setup part prints nothing and exits 0. The hook prints nothing when the plugin is read in place, outside a git repo, and in a repo that isn't set up. `test_hook_setup_half_never_fails_the_session` swaps in a `setup_nudge` that raises and asserts exit 0 with empty output. `test_in_place_is_never_told` and `test_hook_is_silent_when_it_can_t_tell` still pass unchanged.
9. **R9. The nudge is never a problem.** With a stale record and drift pending, `analyze()` reports no problem, so `vet --strict` refuses nothing. `test_check_strict_ignores_drift` gets a stale record and asserts `problems == []`.
10. **R10. `/sdlc:status` and `/sdlc:intent` pass the nudge on.** If `status` prints `■ Setup`, `/sdlc:status`'s report ends with that line as printed. Intent's Step 0 says it once, before Step 1, and goes on: the nudge never stops the skill. `test_status_and_intent_pass_the_setup_nudge_on` (`tests/test_skills.py`) fails if either `SKILL.md` stops naming `■ Setup`.
11. **R11. The docs say what the code now does.** These are updated:
    - *After an update* in `docs/REFERENCE.md`: the `setup.json` paragraph says status names the record only when it is older and drift finds something, or when it is missing; the paragraph on how a release is noticed says the hook prints setup's line when there is no release line.
    - The *Updates* and *Setup* entries in `AGENTS.md`.
    - The update check in `docs/FEATURES.md`.
    - The `description` in `hooks/hooks.json`.
    - The docstrings of `setup_nudge()`, `hook_line()` and `cmd_readiness()`.

    `test_reference_says_the_hook_carries_setup_s_line` fails if REFERENCE.md's *After an update* section stops saying the hook prints `/sdlc:setup` when there is no release line.

## Design

### Assumptions checked in the code

- `setup_nudge()` (`scripts/sdlc.py`) compares only `setup.json`'s `version` with `plugin_version()`. It never reads `drift()`. That is the bug.
- `readiness`'s `complete` is false whenever `drift()` has anything in `breaking`, `refresh` or `report` (`cmd_readiness()`). When it is true, setup's Step 0 stops and writes nothing (`skills/setup/SKILL.md`), so `record` never runs.
- `drift()` compares against the hashes the last `record` wrote. If the record is left at an older version, each later drift is still measured against what setup last offered. So a record not rewritten after a release that changed nothing loses nothing: the next release that does change something is still found.
- `drift()` reads only local files: the host docs, the plugin's defaults, guides and templates, and the config. Its only subprocess is the git call `load_config()` makes to resolve the base branch, cached per checkout. It never reaches the network.
- `hook_line()` returns None in place and outside a repo. Otherwise it returns `update_line()` over the day's cache. `cmd_update("hook")` wraps it in `except Exception` and exits 0.
- `update_report()`'s steps end with `/sdlc:setup`, so a release line already sends the person through setup.
- The skills that run `status` are `status`, `intent`, `spec`, `ship` and `idea`. None of them names `■ Setup` today.

### The nudge asks drift, and only when the version is behind

```python
def drift_pending(found: dict) -> bool:
    return bool(found["breaking"] or found["refresh"] or found["report"])
```

`cmd_readiness()`'s `complete` uses `drift_pending(found)` in place of the inline clause, and behaves as before.

`setup_nudge(root)` keeps its order:

1. No `config.toml` gives None.
2. An unreadable record gives its reason.
3. No record gives the `no record…` line.
4. A record that is not older than the running plugin gives None. This is the only step reached in the usual case, and it runs no drift.
5. A record that is older calls `drift(root)`. If it raises `OSError` or `ValueError`, the nudge returns the version line. If `drift_pending()` is false, it returns None. Otherwise it returns the version line, worded as today.

So the nudge says exactly what `/sdlc:setup` would do: it shows when setup has something to draft from the update, and it is gone when setup would stop at `complete`. Setup's own text needs no change. On a repo where the release changed nothing, the nudge is already gone before setup runs.

The record's `version` now means "the version setup last wrote at". It can stay behind the plugin across releases that changed nothing, and REFERENCE.md says so.

### The hook carries it when no release line is shown

`hook_line(root, home)`:

1. In place, or outside a repo: return None, as today.
2. Work out `update_line(...)` from `check_update(..., fresh=False)`. If there is a line, return it.
3. Otherwise, in its own `try`, return `f"sdlc setup: {nudge}"` when `setup_nudge(root)` gives a line. A raise or None gives None.

`cmd_update("hook")` keeps its outer `except` and its JSON shape. The release line always wins, so a session never sees two lines. Nothing is lost: running `/sdlc:update`'s steps includes running `/sdlc:setup`. The setup part costs one file read unless the record is behind. When it is behind, it costs drift's local reads, the same work `status` now does.

### The skills

- `skills/status/SKILL.md`, Step 3: one rule. When `status` printed `■ Setup`, the report's last line is that line, as printed. It is not a recommendation and doesn't change the precedence list.
- `skills/intent/SKILL.md`, Step 0: when `status` printed `■ Setup`, say that line once and go on. Neither skill gets a new bash command or a new `allowed-tools` rule.

### Boundaries

- **Always:** the hook prints one line at most and exits 0. The nudge shows when setup has something to draft from the update, and when it can't tell.
- **Ask first:** nothing new. Setup still writes only after its one WAIT, and `record` runs only in its Step 5.
- **Never:**
  - no new write anywhere: no record on the `complete` stop and no state file for drift;
  - no hook line in place;
  - no change to `drift()`'s classes or to what makes `complete` true;
  - the nudge is never a `vet` problem.

## Contracts touched

- ***Setup: `drift()` and `readiness`.***
  - `record` still writes `setup.json` each time setup writes, and only then. This design adds no write, so the record is never written where setup now writes nothing.
  - `complete` still errs towards false. Its rule doesn't change, it just moves into `drift_pending()`.
  - The nudge leans the same way: no record, an unreadable record, or a drift it can't read all keep the line.
  - "A nudge in `status` is never a problem" stays true, pinned by R9.
- ***Writes before a WAIT.*** Untouched. There are still five writes before a WAIT, plus the update cache, and this change adds none. Constraint 1 ("setup still writes nothing before its question") holds without an exception.
- ***Updates: the one hook.***
  - It still only advises: one line or nothing, exit 0 always, never an update.
  - `hooks/hooks.json` is still the plugin's only hook, so `test_sdlc_loads_nothing_from_plugins` is untouched.
  - A copy read in place is still never checked or told anything: the in-place return stays first.
  - What changes is which line the hook may print. AGENTS.md's *Updates* entry gets one clause: the line is the release's, else setup's (`setup_nudge()`). That updates the map; the rule stays the same.
  - The intent's constraint says the hook stays cheap, a file read. That holds unless the record is behind. When it is, the hook runs drift's local reads and one git call per session until setup next records. **This goes beyond "a file read", so it's for the person to accept.** The other way is to write the record (see Alternatives).
- ***The scripts run on Windows.*** No new subprocess, no new write and no new platform module.
- ***Skills.*** Two `SKILL.md` edits, prose only. No new bash commands and no change to `allowed-tools`, so the rule tests are untouched. No WAIT is added or moved.
- ***A doc's claim the change made false*** (REVIEW.md). R11 lists every doc that names `setup_nudge()`, the hook's line, or when status names `setup.json`.

## Alternatives rejected

- **Have setup re-record the version on its `complete` stop.** This would be a write where setup now writes nothing. It would need either:
  - its own question (a WAIT to approve a one-field version bump), or
  - a sixth named exception to confirm-before-writing, for a committed file. That would be a bigger change to the rule than the update cache, which lives in no checkout.

  Either way it leaves `.sdlc/setup.json` uncommitted. So every host would have a commit to make for every release that changed nothing, and setup could not stop with nothing to do. Asking drift needs no write and no commit, and says exactly what setup would find.
- **Have the nudge run all of `readiness`.** The nudge would then also fire for gaps that have nothing to do with the update, like an unset doc or a missing permission rule. Also, `readiness` asks the tracker for its own readiness, which can mean running `gh`, a network call in every `status` and at every session start.
- **Two hook lines, or one joined line, when there is both a release and a setup nudge.** Two lines breaks the hook's one-line rule. A joined line repeats what the release line already leads to, because `/sdlc:update`'s steps run `/sdlc:setup`.
- **Tell the setup nudge in place too.** That would loosen "a copy read in place is never checked or told", which is a contract, not a side effect. In this repo, the only usual place a copy is read in place, the gate already fails while `drift` reports anything, so the line would almost never show.
- **Caching drift's answer between sessions.** It would add a state file to keep fresh against every doc edit, to save local reads made only while the record is behind.
- **Every skill that runs `status` passes it on.** `spec`, `ship` and `idea` run `status` as plumbing, mid-task. The hook now reaches every session, and status and intent are where the person asks what needs them and where new work starts. A line in every ship report would be noise. This is still the person's call; see the questions below.

## Verification

```bash
uv run --group dev pytest -q tests/test_setup_lifecycle.py tests/test_update.py tests/test_skills.py
./check.sh
uv run --quiet --script scripts/sdlc.py status | grep -c '■ Setup'
uv run --quiet --script scripts/sdlc.py update --hook
```

What healthy output looks like:

- **First command:** every test passes, the new R1–R11 tests included. The rewritten `test_status_nudges_on_old_manifest` (now the R2 test) passes.
- **`./check.sh`:** ruff check, ruff format and pytest all pass, and `claude plugin validate --strict` passes. `sdlc.py drift` reports nothing in this repo, since no default or guide changes.
- **`grep -c`:** `0` in this repo, whose drift is clean. Before this change it printed `1` whenever `setup.json` lagged `plugin.json`.
- **`update --hook`:** prints nothing here, because the copy is read in place.

To see the bug's steps fixed end to end, in a scratch repo set up at an older version under a release that changed no default:

1. `status` shows no `■ Setup`.
2. `readiness` says `complete: true`.
3. `update --hook`, with no newer release, prints nothing.

Change one default block and rerun:

1. `status` shows `■ Setup: set up with …`.
2. `update --hook` prints `{"systemMessage": "sdlc setup: set up with …  /sdlc:setup"}`.
3. After `/sdlc:setup` and its yes, both are gone.

