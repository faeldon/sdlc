---
id: 209
slug: upstream-bugs
kind: plan
created: 2026-11-21
updated: 2026-11-21
---

# 209 — A host's /sdlc:bug files a bug in the plugin upstream · plan

> Written by the builder after reading the code; read by the reviewers against `spec.md`.

## Files to change

- `scripts/sdlc.py`: a new *Filing upstream* section beside the update check:
  - constants `UPSTREAM_RECORD` (`sdlc-upstream.json`), `UPSTREAM_INPUT`
    (`sdlc-upstream-input.md`), `UPSTREAM_FIELDS`, `UPSTREAM_MARKER`, `UPSTREAM_TAIL = 40`,
    `LEFT_OUT_NOTE`;
  - `upstream_tracker(home)`: the GitHub tracker, by path, whatever `archive.target` says. It
    reuses the loader `tracker()` has, split out as `_tracker_module(name)`;
  - `upstream_info(home)`: `{available, why, own_repo, repo, login, input, new_issue_url}`;
  - `parse_upstream_input(text)`: the allowlisted sections and `left_out`;
  - `host_specifics(home, cfg)`: what the cutter replaces, each with its placeholder;
  - `_cut_host(text, specifics, home)`: paths, then specifics, then the final check;
  - `upstream_diagnostics(home)`: versions, scope, OS, `uv`, the config's key names;
  - `upstream_render(home)`: `{title, body, key, left_out, already}`;
  - `upstream_send(home, key)`: the record, then the tracker;
  - `@command("upstream", …)` with `--render` / `--send` and `--key`;
  - `cmd_intake()`: `from_host` on each issue;
  - `_config_data(root)`: the one read of `.sdlc/config.toml`, split out of `load_config()`, so
    the diagnostics name the keys the host set from the same parse.

  Reused rather than re-derived: `release_source()`, `_own_repo()`, `main_root()`, `worktrees()`,
  `change_dirs()` and `load_change()`, `inbox_entries()`, `load_config()`, `plugin_version()`,
  `in_place()`, `plugin_installs()` and `most_specific()`, `_ledger_dir()`, `closing._main_lock()`.
- `scripts/trackers/github.py`: `repo_of(url)`, `new_issue_url(repo)`, `upstream_unavailable()`,
  `login()`, `find_issue(repo, marker)` and `file_issue(repo, title, body)`. Core may not name
  `github.com` or run `gh` (`test_core_never_calls_gh_itself`), so the URL is parsed and `gh` is
  found here.
- `skills/bug/SKILL.md`: Step 0 runs `upstream`; Step 1 asks which kind of bug it is, in a host;
  a plugin bug's own path through Steps 3–6; one new `Bash(...)` rule; the WAIT's fifth question.
- `skills/triage/SKILL.md`: an entry filed from a `from_host` issue carries `Origin: host`.
- `tests/conftest.py`: the fake `gh` answers `auth token`, `api user` and `issue list --state all`.
- `tests/test_upstream.py` (new): R1, R2, R4–R7, R9–R11, R13, R14.
- `tests/test_archive.py`: R12's `test_intake_flags_an_issue_from_a_host`, beside the other
  `cmd_intake` tests and their fake-`gh` helpers.
- `tests/test_skills.py`: R3's and R8's skill-text tests.
- Docs: `docs/REFERENCE.md` *Trackers* and *Issues people file*, `README.md`'s `/sdlc:bug` line,
  `docs/FEATURES.md` (an `upstream bug` entry), `AGENTS.md`'s *Trackers* and *Writes before a
  WAIT* paragraphs.

## Work order

1. **The repo and the readiness.** `upstream` with no flag: the repo from the manifest, own repo,
   no `gh`, no login (R1, R2, R11's report). Tracker: `repo_of`, `new_issue_url`,
   `upstream_unavailable`, `login`.
2. **The render.** Input parse, the cutter, diagnostics, `--render` (R4, R5, R6, R7's key, R14).
3. **The send.** Tracker `find_issue` and `file_issue`; `--send` with the key check, the record
   and the rerun (R7, R9, R10, R11's send, R13).
4. **Intake.** `from_host` (R12), and triage's text.
5. **The skill.** Bug's text, rule and WAIT (R3, R8).
6. **Docs** (R15).

## Tests

- R1 `test_upstream_repo_comes_from_the_manifest`: a fixture manifest's `repository`, changed,
  and one not on GitHub.
- R2 `test_upstream_is_unavailable_in_the_plugins_own_repo`: a fixture repo holding the manifest
  and `scripts/sdlc.py`.
- R3 `test_bug_asks_which_kind_before_filing_upstream` (skill text).
- R4 `test_upstream_body_holds_only_the_allowlist`: the sentinel host.
- R5 `test_upstream_diagnostics_name_keys_never_values`, with `claude` and `uv` missing.
- R6 `test_upstream_cut_leaves_out_what_it_cannot_make_safe`, and the tail of a long output.
- R7 `test_upstream_send_refuses_a_body_not_previewed`.
- R8 `test_bug_shows_the_upstream_body_before_its_wait` (skill text), and the existing WAIT tests.
- R9 `test_github_file_issue_names_the_repo_and_sets_nothing_else` (fake `gh`).
- R10 `test_upstream_send_never_files_twice`,
  `test_upstream_send_after_a_stopped_send_finds_the_issue_first`.
- R11 `test_upstream_without_gh_files_nothing`.
- R12 `test_intake_flags_an_issue_from_a_host`.
- R13 `test_an_upstream_send_changes_nothing_recorded_issues_reads`.
- R14: `test_upstream.py`'s render and cut tests are marked `portable`; the existing
  `tests/test_windows.py` scans the new code's `subprocess.run` and `write_text` calls.
- R15: `tests/test_feature_map.py` and `tests/test_skills.py` as they stand.

## As built

- The cutter holds each placeholder as an opaque private-use character while it runs, so a later
  pass never matches inside one (`<repo>` holding a folder named `repo`).
- Beyond `.sdlc/` and `.claude/worktrees/`, a relative path that exists in the running plugin's
  own copy (`scripts/sdlc.py`) is kept: it names the plugin, not the host.
- A path is cut after a `:` too (`host:/home/x`), and any `user@host:path` remote becomes
  `<remote>`, configured or not (round 1).
- An `@name` in the prose sections is put in backticks, so filing the issue notifies no one
  (round 1).
- Every URL becomes `<url>`; names every host has (the base default, `master`, `origin`, and a
  config value equal to the plugin's default) are not cut.
- The diagnostics name the config keys the plugin knows and count the rest, unnamed.
- An acceptance check (`checks.md`) holds R15's doc lines.

## Rollback

`git revert` undoes the code and docs. It does not undo an issue already filed upstream: close it
on GitHub by hand (`gh issue close <n> --repo <owner/name>`). Each host keeps
`sdlc-upstream.json` (and, after a stopped run, `sdlc-upstream-input.md`) in its git common dir;
both are inert without this code and can be deleted (`rm "$(git rev-parse --git-common-dir)"/sdlc-upstream*`).
