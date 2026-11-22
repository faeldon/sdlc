# 232-exit-notes — entries

## [2026-11-22-35] [idea] Widen `EVIDENCE_EXIT_RE` in sdlc.py to accept a note after the exit code

Left undone by 232-exit-notes, carried forward when it landed: `scripts/sdlc.py`'s `EVIDENCE_EXIT_RE` (`^exit:\s*(-?\d+)\s*$`), which reads ship's own behaviour check in `findings.md`, is as strict as `EXIT_RE` was: an `exit: 2 (note)` there is not read as evidence. Out of this change's scope (the factory's reading); widen it the same way in a change of its own if ship's check meets it.
See .sdlc/work/232-exit-notes/notes.md in its commit.
Raised 2026-11-22.

## [2026-11-22-36] [nit] the resolver's *Evidence* paragraph has the same `exit: <n>` wording and no hook-refusal sentence, so it will meet the same stop

Raised by the code review of 232-exit-notes, round 1: plugins/factory/agents/resolver.md:58: the resolver's *Evidence* paragraph has the same `exit: <n>` wording and no hook-refusal sentence, so it will meet the same stop

Theme: docs
Paths: plugins/factory/agents/resolver.md
Cost: S
Value: med
Raised by: 232-exit-notes (correctness)
