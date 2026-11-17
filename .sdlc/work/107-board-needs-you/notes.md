# Notes

- [x] A stop record that won't read reads differently in the two places: the board makes it a problem (`fix: runs/stopped.md doesn't open …`, card `stopped: None`, as 086 pinned), while `status`'s `factory_stop()` keeps it a stop (`stopped: read runs/stopped.md`). Both put it in front of the person; aligning them means changing one of the two pinned behaviours. → seed: 2026-11-17-69
- [x] `next_action()` is unchanged, as the spec says: an escalation that still needs `decide D2` names `/sdlc:ship, or /sdlc-factory:land …` as its next step, beside its `needs you:` line. A next step that follows the needs would read better. → seed: 2026-11-17-70
