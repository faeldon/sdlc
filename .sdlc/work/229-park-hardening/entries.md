# 229-park-hardening — entries

Retire 2026-11-22-13: taken in by 229-park-hardening
Retire 2026-11-22-14: taken in by 229-park-hardening
Retire 2026-11-22-15: taken in by 229-park-hardening
Retire 2026-11-22-16: taken in by 229-park-hardening
Retire 2026-11-22-17: taken in by 229-park-hardening

## [2026-11-22-21] [idea] Strip control characters in read_park() on the reader side

Left undone by 229-park-hardening, carried forward when it landed: `factory_records.read_park()` (and `factory.py`'s) take `RESOURCE:` and `HOLDER:` as written, so a hand-edited `runs/parked.md` with an ESC in it still reaches `status` and the board: `busy_of()` now cleans what the gate writes, but a reader-side strip would cover a forged record too. Out of 229's scope (the busy answer only).
See .sdlc/work/229-park-hardening/notes.md in its commit.
Raised 2026-11-22.

## [2026-11-22-22] [nit] the line "holder is `unknown`, and an `UNTIL` that won't read is noted and ignored.

Raised by the code review of 229-park-hardening, round 1: docs/REFERENCE.md:249: the line "holder is `unknown`, and an `UNTIL` that won't read is noted and ignored. The factory then parks the change: its gate records no" is now well past the wrap used in the rest of the paragraph. Rewrap it.

Theme: docs
Paths: docs/REFERENCE.md
Cost: S
Value: low
Raised by: 229-park-hardening (correctness)

## [2026-11-22-23] [nit] `_park_deadline_at()` runs a `git show` for each build-stage change inside the status loop.

Raised by the code review of 229-park-hardening, round 1: scripts/sdlc.py:11036: `_park_deadline_at()` runs a `git show` for each build-stage change inside the status loop. Read it once before the loop, as `_gate_jobs_at()` is.

Theme: refactor
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 229-park-hardening (correctness)
