---
id: 018
slug: base-branch
kind: plan
created: 2026-10-25
updated: 2026-10-25
---

# 018 — Let a host name its base branch · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

The resolved branch is threaded as **`trunk: str`** rather than the spec's `base`, because `base`
already means a boundary sha (`closed_changes(home, base)`) or a merge base throughout `sdlc.py`.
The config key and JSON stay `git.base` / `git.base_source` (R1; the spec's Design paragraph says
`source`, R1 wins).

- `scripts/sdlc.py` — `git` section, resolution, `trunk` threaded through every base-branch call.
- `scripts/trackers/github.py` — `drop()` returns its error and removes the `stage:` label;
  `_landing()` reads `change["base"]`; `MAIN` goes.
- `skills/{intent,ship,close,drop,release,publish,setup}/SKILL.md` — name `git.base` from `config`.
- `tests/test_skills.py` — `READS_CONFIG` gains `git.base` for those skills.
- `tests/test_config_resolution.py` — resolution cases (R1).
- `tests/test_sdlc.py` — no-literal-`main` test (R2), `base` on master (R5), behind/nits (R9).
- `tests/test_archive.py` — R3 (no claim without a base), R4 (drop reported, label removed), R8.
- `tests/test_adoption.py` — the new→close run and release/publish on a `master`-only repo (R6,
  R7, R12).
- `docs/REFERENCE.md` — `[git] base`, detection order, what refuses (R13).
- `AGENTS.md` — one line: `main` means the resolved base (R13).
- `.sdlc/setup.json` — rerun `sdlc.py record` only if `drift` reports the new key.

## Work order

1. **Resolution (R1).** `CONFIG_KEYS["git"] = {"base": None}` with a comment. In `load_config()`,
   after parsing, call a new `_resolve_trunk(root, value) -> (name|None, source)`: the configured
   string → `config`; else `git rev-parse --verify -q refs/heads/main` → `("main", "detected")`;
   else `git symbolic-ref -q --short refs/remotes/origin/HEAD`, strip the `origin/` prefix, accept
   if `refs/heads/<it>` verifies → `detected`; else `(None, "unset")`. Store as
   `cfg["git"]["base"]` and `cfg["git"]["base_source"]` on every return path of `load_config`,
   including no-file and won't-parse. A non-string `base` warns like other keys. `cmd_config`
   prints the `git` section. Add a `trunk_refusal(cfg, home) -> str | None` (unset, or
   `refs/heads/<base>` missing) used by every writing command. Tests for each case, then stop.
2. **`new` refuses early (R3, R9).** `--base` default → `None`; `cmd_new(..., base=None)` resolves
   `base or cfg trunk` and runs `trunk_refusal` right after `work_ignored`, before `ids_mode`.
   `load_config` moves up to that point (it's already called once). Test with fake gh: refused,
   no issue created, no counter written.
3. **Tracker drop (R4, R8).** `github.py`: `drop(url, why) -> str | None` returns stderr of
   `gh issue close` on failure, else runs a separate `gh issue edit --remove-label "stage: …"` for
   each `stage:` label it reads off the issue (refusal ignored), returns None. `claim()`'s internal
   drop puts the result in its error text. `cmd_new` prints `  closed   <url>  (not planned:
   <why>)` or `⚠  <url> is still open: close it by hand`. `_tracker_change()` adds
   `"base": cfg trunk`; `_landing()` compares `_default_branch()` to `change.get("base")`; drop
   `MAIN`; update the module docstring. Check `scripts/trackers/command.py` for a `drop()` to match
   the signature. Tests with `FAKE_GH_FAIL` on close, and `FAKE_GH_DEFAULT=master`.
4. **Ship's base step (R5).** `behind_main` → `behind(main, branch, trunk)`; `cmd_base` loads
   config, refuses via `trunk_refusal`, and uses `trunk` in the rev-list, `rebase`,
   `merge --ff-only`, the `cat-file -e {trunk}:.sdlc/last-id`, and refusal text. Status's two
   "behind main by" strings read `behind {trunk} by`.
5. **Close and drop (R6).** In `cmd_close`, after `load_config(main)`: `trunk_refusal`, then the
   on-trunk check, `--is-ancestor`, `rev-parse` before/after, messages. Thread `trunk` into
   `_close_times(main, trunk)`, `_drop_commit(main, branch, trunk)`, `measure_change` (from its
   `cfg`), `_merged_scripts(main, before, trunk)`. Rename the handoff mode key `"main"` → `"home"`
   in `RAN`/`_handoff`/the caller (internal, value text unchanged) so no `"main"` literal is left.
6. **History walks, release, publish, retro (R7).** `closed_changes(home, since, trunk, read)` and
   `dropped_changes(home, since, trunk)` (rename their boundary param `base` → `since`); a `None`
   trunk returns `[]`. Callers pass `cfg["git"]["base"]` (unreleased, retro, status's analysis).
   `last_retrospective(home, trunk)`, `_release_tags` (has cfg), `_release_refusals(root, home,
   trunk)`, retro-commit's on-branch check, publish's `rev-parse`, `refs/heads/{trunk}` refspec and
   step name `f"push {trunk}"` (still `push main` on main hosts, so existing tests hold). Read-only
   `status`/`unreleased`/`retro` add a problem when unset instead of crashing.
7. **Remaining readers (R9).** `nits --change` and `context --base` default to the trunk;
   `_own_script()` loads `load_config(main_root(root))` for its merge base (inside its `try`).
8. **No literal left (R2).** Test: tokenize `sdlc.py`, take STRING tokens that aren't docstrings,
   and fail on any matching `^['"]main['"]$`, `refs/heads/main`, `\.\.main\b` or `\bmain:`. Fix
   whatever it finds.
9. **Skills (R10, R11).** Prose and questions say `<git.base>` read from Step 0's `config`: intent
   Step 4 question and Step 5, ship Step 0's base step, close's questions and `git log -2 --oneline
   <git.base>`, drop's question, release's prose, publish's question, step list
   (`push <git.base>`) and limits. Setup: when `git.base_source` is `detected` and base isn't
   `main`, put `[git] base = "<branch>"` in the config draft; when `unset`, ask for the branch in
   its question round. No bash block or `allowed-tools` rule changes. Add `git.base` to
   `READS_CONFIG` for intent, ship, close, drop, release, publish, setup.
10. **Adoption (R12).** Parametrize (or copy) `test_a_bare_repo_runs_a_change_from_new_to_close`
    and the release/publish run over `main`/`master`: `init -b master`, no config key; asserts read
    `master`. Add a `config` assertion: main-only repo → `{"base": "main", "base_source":
    "detected"}`.
11. **Docs (R13).** REFERENCE: a `[git]` section (key, detection order, never current branch /
    `init.defaultBranch` / GitHub, refusals, changing it after closes walks a different line).
    AGENTS.md: one sentence under Architecture. Then `sdlc.py drift`; if it reports, `sdlc.py
    record` from this checkout.
12. `./check.sh` green.

## Tests

- R1 — `test_config_resolution.py`: configured; main present; master-only with `origin/HEAD`;
  master-only without a remote → unset; configured wins over detected; `base_source` each time.
- R2 — tokenize test in `test_sdlc.py`.
- R3 — `test_archive.py`: unset base and missing base each refuse, fake gh state has no issue, no
  `.sdlc/last-id`; explicit bad `--base` refused too.
- R4 — `test_archive.py`: worktree failure (pre-existing path) → output has `closed … (not
  planned` and the issue has no `stage:` label; with `FAKE_GH_FAIL` on close → `still open`.
- R5 — `test_sdlc.py`: `base` fast-forwards and rebases on a `master`-only repo.
- R6, R7, R12 — `test_adoption.py` master variants: Close and Drop commits on `master`, release
  tags it, publish pushes `refs/heads/master` and reports `push master`.
- R8 — `test_archive.py`: `FAKE_GH_DEFAULT=master` with trunk `master` → labelled `landed`, not
  closed; trunk `main` with default `master` → closed, as today.
- R9 — `nits --change`, `context`, status's behind count on `master`.
- R10, R11 — `test_skills.py` via `READS_CONFIG`; setup's prose read by eye at ship.
- R13 — manual: REFERENCE names `[git] base` and the order.

## Rollback

`git revert <sha>` of the change's commit covers code, skills, docs and tests. Not covered: a host
that already added `[git] base` to its config gets an "unknown key" warning after the revert and
falls back to `main` — delete the line. Issues closed by `new`'s drop stay closed, as they would
have before.
