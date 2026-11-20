# 195-designing-while-specified — entries

## [2026-11-20-11] [idea] Show a spec step and its elapsed time on a Designing card

Left undone by 195-designing-while-specified, carried forward when it landed: The board's step track (`_progress()`) shows nothing for a first spec draft, which records no `runs/step.md`; a card under Designing could show a `spec` step with its elapsed time.
See .sdlc/work/195-designing-while-specified/notes.md in its commit.
Raised 2026-11-20.

## [2026-11-20-12] [nit] the edited line is now about 110 characters, while its neighbours wrap near 100.

Raised by the code review of 195-designing-while-specified, round 1: docs/REFERENCE.md:575: the edited line is now about 110 characters, while its neighbours wrap near 100. Rewrap the paragraph.

Theme: style
Paths: docs/REFERENCE.md
Cost: S
Value: low
Raised by: 195-designing-while-specified (correctness)

## [2026-11-20-13] [nit] `specifying()` has a lot of branching and repeats the read-text-if-file pattern three times.

Raised by the code review of 195-designing-while-specified, round 1: scripts/factory_records.py:300: `specifying()` has a lot of branching and repeats the read-text-if-file pattern three times. A small helper would shorten it.

Theme: refactor
Paths: scripts/factory_records.py
Cost: S
Value: low
Raised by: 195-designing-while-specified (correctness)
