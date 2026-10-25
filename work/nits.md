# Nits

> Small technical debt: findings ship approved unfixed, kept until a change fixes them or makes
> them moot. Each one is a `## NNN-n [theme] <title>` heading (the raising change's number and a
> count), then `- **raised:** YYYY-MM-DD by NNN-slug (pass)`, `- **paths:** a, b` and
> `- **cost:** S|M  **value:** med|low` lines, then a line or two on what's wrong. The process
> doc's rubric says what each cost and value means. `/sdlc:intent` and `/sdlc:spec` offer the ones
> a change touches, `/sdlc:ship` adds and retires entries, and `/sdlc:retro` counts them by theme
> and age; history keeps a retired one.

## 003-1 [tests] A deprecations status test whose patched half can't fail
- **raised:** 2026-10-24 by 003-test-lifetimes (correctness)
- **paths:** tests/test_deprecations.py
- **cost:** S  **value:** low

The half of the `status` test that runs with a patch applied can't fail, so it proves nothing.

## 003-2 [robustness] A deprecations registry that isn't UTF-8 crashes status
- **raised:** 2026-10-24 by 003-test-lifetimes (correctness)
- **paths:** scripts/sdlc.py
- **cost:** S  **value:** med

`deprecations()` catches `TOMLDecodeError` but not `UnicodeDecodeError` from `read_text`, so it
raises instead of reporting a problem.

## 005-1 [robustness] Accept's `left` builds up across checks
- **raised:** 2026-10-24 by 005-acceptance-checks (correctness)
- **paths:** scripts/sdlc.py
- **cost:** S  **value:** med

`cmd_accept` takes `before` once, so one check that leaves the tree changed fails every check
after it too.

## 005-2 [robustness] Accept keeps a timed-out check's output as bytes
- **raised:** 2026-10-24 by 005-acceptance-checks (correctness)
- **paths:** scripts/sdlc.py
- **cost:** S  **value:** med

`TimeoutExpired.stdout` is bytes even with `text=True`, so the output reads `b'…'`.

## 005-3 [robustness] Acceptance checks inherit stdin
- **raised:** 2026-10-24 by 005-acceptance-checks (correctness)
- **paths:** scripts/sdlc.py
- **cost:** S  **value:** low

A check that reads stdin waits until the timeout instead of failing at once.

## 009-1 [style] The `RECORD_CLEARS` tuple-unpacking idiom
- **raised:** 2026-10-24 by 009-drift-message (cost)
- **paths:** tests/test_defaults.py
- **cost:** S  **value:** low

The set is built from two unpacked tuples where one set literal reads plainer.

## 010-1 [robustness] Release's after-bump step misses files the command stages
- **raised:** 2026-10-24 by 010-release-lock (correctness)
- **paths:** scripts/sdlc.py
- **cost:** S  **value:** med

`git diff --name-only` sees unstaged changes only; `git diff --name-only -z HEAD` would see both.

## 010-2 [robustness] A failed after-bump leaves a changelog release created
- **raised:** 2026-10-24 by 010-release-lock (correctness)
- **paths:** scripts/sdlc.py
- **cost:** M  **value:** med

`restore()` puts back tracked files only, so a changelog file the release created stays, and a
rerun adds its section twice.

## 010-3 [style] Two release-skill lines run past 100 characters
- **raised:** 2026-10-24 by 010-release-lock (cost)
- **paths:** skills/release/SKILL.md
- **cost:** S  **value:** low

The WAIT variant and a Step 1 line added for `after_bump`.

## 012-1 [robustness] Retro's oldest nit is picked by comparing dates as text
- **raised:** 2026-10-25 by 012-nits-register (correctness)
- **paths:** scripts/sdlc.py
- **cost:** S  **value:** low

`nits_summary` compares `raised` strings, so an entry with a malformed date (which `check` already
reports) can be taken as its theme's oldest, leaving `age_days` null.
