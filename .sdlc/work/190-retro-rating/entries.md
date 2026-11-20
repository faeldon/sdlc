# 190-retro-rating — entries

Retire 2026-11-19-18: taken in by 190-retro-rating

## [2026-11-20-31] [idea] Confirm a real two-question retro transcript lists the approval first

Left undone by 190-retro-rating, carried forward when it landed: Before ship (spec, *Contracts touched*): read one real `/sdlc:retro` transcript with the two-question dialog and confirm `toolUseResult.answers` lists the approval first, so `metrics._answers()[0]` is the approval. R11 pins the shape `_answers()` reads, not the harness.
See .sdlc/work/190-retro-rating/notes.md in its commit.
Raised 2026-11-20.

## [2026-11-20-32] [nit] `_experience_text` does `table = _table(..., [[..., rating, before, ...]])`.

Raised by the code review of 190-retro-rating, round 1: scripts/retro.py:2425: `_experience_text` does `table = _table(..., [[..., rating, before, ...]])`. A `None` rating relies on `_table` rendering it as `—`. A test pins this, but the `—` spelling is implicit.

Theme: tests
Paths: scripts/retro.py
Cost: S
Value: low
Raised by: 190-retro-rating (correctness)

## [2026-11-20-33] [nit] `_last_experience` does `int(rating)` on the table cell.

Raised by the code review of 190-retro-rating, round 1: scripts/retro.py:2467: `_last_experience` does `int(rating)` on the table cell. A hand-edited report with a non-numeric cell would raise instead of reading back as no rating. Guard it, or catch `ValueError`.

Theme: robustness
Paths: scripts/retro.py
Cost: S
Value: low
Raised by: 190-retro-rating (correctness)

## [2026-11-20-34] [nit] `test_a_rating_with_no_line_says_so` takes a `tmp_path` fixture it never uses

Raised by the test review of 190-retro-rating, round 1: tests/test_retro.py: `test_a_rating_with_no_line_says_so` takes a `tmp_path` fixture it never uses

Theme: tests
Paths: tests/test_retro.py
Cost: S
Value: low
Raised by: 190-retro-rating (correctness)
