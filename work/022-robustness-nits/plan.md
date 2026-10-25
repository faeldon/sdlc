---
id: 022
slug: robustness-nits
kind: plan
created: 2026-10-25
updated: 2026-10-25
---

# 022 — Pay down the robustness nits in acceptance checks, release and deprecations · plan

## Context

Six `[robustness]` nits in `work/nits.md` (003-2, 005-1, 005-2, 005-3, 010-1, 010-2) are places in
`scripts/sdlc.py` where bad input or a failed step gives a wrong or confusing result. Three are on
the path of the coming 1.2.0 release. Tier 1, `serves: [O2]`: a failed release or acceptance run
should leave the tree as it found it and say what failed. Each fix gets a test written first that
fails on today's code.

## Open questions, settled here (struck in the intent)

- **010-1: files the after-bump command stages go into the release commit.** `commit()` runs a
  plain `git commit`, which commits the whole index, so staged files already land today. What's
  broken is that a failure doesn't put them back. Refusing them would be a new refusal for no gain.
- **010-2: `restore()` learns what the release created** by recording the changelog path in
  `changelog()` before writing, if it didn't exist.
- **005-1: each check is judged only on its own diff.** `accept` never writes to the person's tree,
  so it never puts anything back.

## Changes

### `scripts/sdlc.py`

- **003-2, `deprecations()`:** catch `(tomllib.TOMLDecodeError, UnicodeDecodeError)`. A registry
  that isn't UTF-8 is reported as `"{rel} won't parse: …"`, as now, never raised.
- **005-1, `cmd_accept()`:** move `before = _status_lines(checkout)` inside the loop, so each
  check's `left` is only what that check changed.
- **005-2, same function:** in the `TimeoutExpired` branch, decode `e.stdout`/`e.stderr` when they
  are bytes, with `errors="replace"`, through a local `text()` helper.
- **005-3, same function:** pass `stdin=subprocess.DEVNULL`, matching after-bump and prepare.
- **010-1, `cmd_release()`:**
  - in `after_bump()`, diff against `HEAD` (`git diff --name-only -z HEAD`), so staged changes are
    seen too;
  - in `prepare()`, make `tracked_changes()` diff against `HEAD` as well (same bug: a file prepare
    stages would otherwise slip into the release commit).
- **A new module-level helper, `_put_back(home, paths)`:** without it, the `HEAD` diff can name a
  path `HEAD` lacks (a new file the command staged). `git checkout -- <paths>` then fails the
  whole pathspec and restores nothing. The helper:
  1. runs `git reset -q HEAD -- paths`, which unstages everything;
  2. checks out only the paths `git ls-tree -r --name-only -z HEAD -- paths` lists.

  A new file is left untracked, listed in `untracked`, and never deleted.
  - `restore()` calls `_put_back(home, report["files"])`, then unlinks each path in `created`.
  - `prepare()` calls `_put_back(home, sorted(others))` instead of its bare `checkout`, which also
    unstages what prepare staged.
- **010-2, `changelog()`:** append `rel["changelog"]` to a `created` list when the file didn't
  exist before writing. `restore()` deletes only those paths: never a pre-existing file, never an
  untracked file the release didn't write.

### Tests (each written first, failing on today's code)

- `tests/test_deprecations.py`: a registry written as `b"\xff\xfe"` gives a `won't parse` problem
  and no shims.
- `tests/test_acceptance.py`:
  - **005-1:** `touch stray.txt` then `true`. The first check fails with `left == ["?? stray.txt"]`;
    the second passes with `left == []`.
  - **005-2:** with `CHECK_TIMEOUT=1`, `echo partial; exec sleep 5`. The output contains `partial`
    and no `b'`.
  - **005-3:** fd 0 is swapped for a pipe that never closes (`os.pipe` + `os.dup2`, restored in
    `finally`), and the check is `cat > /dev/null` with `CHECK_TIMEOUT=2`. It passes with exit 0,
    where today it times out.
- `tests/test_release.py`, using the existing `_locked()`, `_prepared()` and `_run()` helpers:
  - **010-1, staged and failed:** `echo x >> uv.lock; git add uv.lock; exit 1`. `HEAD` is
    unchanged, and `git status --porcelain --untracked-files=no` is empty.
  - **010-1, staged new file and failed:** `touch new.txt; git add new.txt; exit 1`. The version
    files are restored, the index is clean, and `new.txt` is untracked and listed in `untracked`.
    This guards against the pathspec failure.
  - **010-1, prepare stages a file:** prepare edits and stages a tracked `README.md`. The release
    is refused, and the index and tree are clean.
  - **010-2:** `changelog = "CHANGELOG.md"` with no such file, and a failing after-bump.
    `CHANGELOG.md` doesn't exist afterwards. Then a rerun with a passing after-bump writes the
    section exactly once.

### The change's own files

- Save this plan as `work/022-robustness-nits/plan.md`.
- In `intent.md`, strike the three open questions with these answers, and set `stage: build`.
- `work/nits.md` is left alone: `/sdlc:ship` retires the six entries.

## Not in scope

- Retro and rework code (021's ground).
- Any config key, skill text or WAIT.
- The other nits (012-1, 019-x, 018-1, 003-1, the `[style]` ones).

## Verification

- Write each new test first and run it against today's code: `uv run --group dev pytest
  tests/test_acceptance.py tests/test_release.py tests/test_deprecations.py -q`. Each new test
  fails before its fix and passes after.
- Then `./check.sh`: ruff, format, the full suite including `test_adoption`'s bare-repo
  `new`→`close`, and `validate --strict`.
- Then `/sdlc:ship 022`.
