# Notes

- [x] `scripts/sdlc.py`'s `EVIDENCE_EXIT_RE` (`^exit:\s*(-?\d+)\s*$`), which reads ship's own → seed: 2026-11-22-35
  behaviour check in `findings.md`, is as strict as `EXIT_RE` was: an `exit: 2 (note)` there is
  not read as evidence. Out of this change's scope (the factory's reading); widen it the same way
  in a change of its own if ship's check meets it.
