I resolved both conflicts and the full gate passes on the result: 2307 tests passed, 13 skipped. I edited only the two conflicted files and ran no git command.

**`.sdlc/work/inbox.md`:** neither side's entries stay.
- **Base branch's side:** it still held seeds 2026-11-17-81 to 84. You said those stay deleted, so I removed them.
- **This change's side:** it still held 2026-11-17-63 (the hand gate sharing the factory's `gate_jobs` slots) and 2026-11-17-76 (moving a change to Tier 2 mid-run). The base branch had already removed both, and both features are now on it (the hand gate's slot and `upgrade` in AGENTS.md). I left them deleted rather than bring them back from this change's older copy of the register.
- I also removed the `Raised 2026-11-17.` line after the conflict, since it belonged to whichever of those entries came last. Seed 2026-11-17-59 is now followed directly by 2026-11-17-86, both unchanged.

**`plugins/factory/scripts/factory.py`:** both sides kept.
- **Base branch's side:** its new `PAUSES` constant and the comment above it are in place, as the base has them.
- **This change's side:** the longer comment above `WAYS` is kept, the one saying `NEXT:` is the command plus a few words so it fits two lines of a card at phone width.
- `WAYS`, `WAYS_WHY` and `stop_text()` were outside the conflict and are as this change built them.

## Evidence

$ grep -rn '^<<<<<<<\|^=======$\|^>>>>>>>' .sdlc/work/inbox.md plugins/factory/scripts/factory.py
exit: 1

$ ./check.sh
All checks passed!
271 files already formatted
2307 passed, 13 skipped in 113.77s (0:01:53)
✔ Validation passed
exit: 0
