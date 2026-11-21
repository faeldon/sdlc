# 210-wait-previews — entries

## [2026-11-21-29] [idea] Add `update` to AGENTS.md's Skills invariant list of WAIT skills

Left undone by 210-wait-previews, carried forward when it landed: AGENTS.md's *Skills* invariant lists the skills that write and owe a WAIT, but leaves out `update`, which `tests/test_skills.py`'s `GATED` includes. Found while building 210; left as it was, since naming it is a separate edit to the list.
See .sdlc/work/210-wait-previews/notes.md in its commit.
Raised 2026-11-21.

## [2026-11-21-30] [nit] R7 says `--preview` takes the same clause flags as `--question`.

Raised by the code review of 210-wait-previews, round 1: scripts/sdlc.py:8308: R7 says `--preview` takes the same clause flags as `--question`. They parse, but `cmd_ship_preview` ignores them without saying so. Refuse them with `--preview`, as the code already refuses clause flags without `--question`, or say in the help text that they are ignored.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 210-wait-previews (correctness)

## [2026-11-21-31] [nit] the `PREVIEW_NAMES` words are checked with substring `in`, so a key word like `path` or `tag` matches any text that contains it

Raised by the test review of 210-wait-previews, round 1: tests/test_skills.py:263: the `PREVIEW_NAMES` words are checked with substring `in`, so a key word like `path` or `tag` matches any text that contains it

Theme: tests
Paths: tests/test_skills.py
Cost: S
Value: low
Raised by: 210-wait-previews (correctness)
