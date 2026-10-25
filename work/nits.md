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

## 009-1 [style] The `RECORD_CLEARS` tuple-unpacking idiom
- **raised:** 2026-10-24 by 009-drift-message (cost)
- **paths:** tests/test_defaults.py
- **cost:** S  **value:** low

The set is built from two unpacked tuples where one set literal reads plainer.

## 010-3 [style] Two release-skill lines run past 100 characters
- **raised:** 2026-10-24 by 010-release-lock (cost)
- **paths:** skills/release/SKILL.md
- **cost:** S  **value:** low

The WAIT variant and a Step 1 line added for `after_bump`.

## 019-1 [robustness] A mistyped After: title makes a seed "next in series"

- **raised:** 2026-10-25 by 019-status-next-work (correctness)
- **paths:** scripts/sdlc.py
- **cost:** S  **value:** low

`next_up` labels a ready seed `next in series` when none of its `After:` titles is in the
register, so a title naming nothing gets that label as well as its `⚠` warning. Check it against
the titles history has shipped too.

## 019-2 [robustness] A loop through a seed's second After: title isn't reported

- **raised:** 2026-10-25 by 019-status-next-work (correctness)
- **paths:** scripts/sdlc.py
- **cost:** S  **value:** low

`_after_loops` follows only each waiting seed's first waiting `After:` title, so seeds that wait
on each other through a later title are never listed and never warned about.

## 019-3 [cost] Status can walk main's history twice

- **raised:** 2026-10-25 by 019-status-next-work (cost)
- **paths:** scripts/sdlc.py
- **cost:** S  **value:** low

With an open milestone and a dangling `After:` title, `next_up` calls `closed_changes(home, None)`
once through `_milestone_verdicts` and once for the shipped titles, reading every closed intent
both times. Walk it once and pass it in.

## 018-1 [perf] load_config runs git on every call to resolve the base branch
- **raised:** 2026-10-25 by 018-base-branch (cost)
- **paths:** scripts/sdlc.py
- **cost:** S  **value:** low

`_resolve_trunk` runs up to three `git` calls each time `load_config()` does, and some commands
call it several times; nothing is slow yet, but one resolved value could be passed down instead.

## 022-1 [robustness] A failed commit or prepare doesn't list a new file after-bump staged
- **raised:** 2026-10-25 by 022-robustness-nits (correctness)
- **paths:** scripts/sdlc.py
- **cost:** S  **value:** low

`restore()` after a later failure unstages it into an untracked file, but `untracked` was taken
at after-bump, so the report never names it.

## 023-1 [robustness] A change sized from an intent committed to main early counts others' commits
- **raised:** 2026-10-25 by 023-branch-size (correctness)
- **paths:** scripts/sdlc.py
- **cost:** S  **value:** low

`_change_base` takes the parent of the commit that first added the intent. If that commit landed
on main before other changes closed (an intent committed outside its branch), the range from it
to the change's commit spans their commits too, in `retro`'s size and in close's `_change_diff`.
A `Close` or `Drop` commit inside the range would show it.
