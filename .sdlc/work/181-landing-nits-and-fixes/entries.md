# 181-landing-nits-and-fixes — entries

## [2026-11-19-45] [idea] Board drawer focus test is flaky under a loaded gate

Left undone by 181-landing-nits-and-fixes, carried forward when it landed: `tests/test_board_browser.py::test_the_drawer_holds_focus_and_returns_it_to_its_card` failed in 181's round-1 gate with no error in the record's tail, and passed when rerun alone: likely flaky under a loaded gate. Not this change's code.
See .sdlc/work/181-landing-nits-and-fixes/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-46] [idea] Adoption tests fail the gate when offline; skip or cache uv's deps

Left undone by 181-landing-nits-and-fixes, carried forward when it landed: `tests/test_adoption.py` needs network (uv fetches PyPI deps for `uv run --script`); a gate with no DNS fails two of its tests. A skip or cache when offline would keep the gate about the code.
See .sdlc/work/181-landing-nits-and-fixes/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-47] [nit] the refusal message is long and repeats `FIX: ALREADY MADE`

Raised by the code review of 181-landing-nits-and-fixes, round 1: plugins/factory/scripts/landing.py:1420: the refusal message is long and repeats `FIX: ALREADY MADE`

Theme: style
Paths: plugins/factory/scripts/landing.py
Cost: S
Value: low
Raised by: 181-landing-nits-and-fixes (correctness)

## [2026-11-19-48] [nit] `taken_lines()` counts every indented line after a `Nits taken in:` line as part of it, so an indented sub-bullet that names an id to say it's left out would retire that nit.

Raised by the security review of 181-landing-nits-and-fixes, round 1: plugins/factory/scripts/factory.py:4699: `taken_lines()` counts every indented line after a `Nits taken in:` line as part of it, so an indented sub-bullet that names an id to say it's left out would retire that nit. Only the change's own author can write this, and the intent asked for an explicit marker, so the risk is low. Stopping continuation at a line that starts a new `-` bullet would tighten it

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 181-landing-nits-and-fixes (contract)

## [2026-11-19-49] [nit] the `_already_made` helper and `test_a_fix_commit_needs_an_ask` write `MADE` and `ALREADY` module constants in the middle of the file, and `tests/test_train.py` defines a second `MADE`; hoist them or rename them to avoid confusion

Raised by the test review of 181-landing-nits-and-fixes, round 1: tests/test_land.py: the `_already_made` helper and `test_a_fix_commit_needs_an_ask` write `MADE` and `ALREADY` module constants in the middle of the file, and `tests/test_train.py` defines a second `MADE`; hoist them or rename them to avoid confusion

Theme: tests
Paths: tests/test_land.py
Cost: S
Value: low
Raised by: 181-landing-nits-and-fixes (correctness)
