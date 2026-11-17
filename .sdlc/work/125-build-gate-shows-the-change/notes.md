# Notes

> What the build left for later: each unticked line is something noticed on the way and kept out
> of this change.

## Left for later

- [x] `/sdlc-factory:spec`'s WAIT still words its question in the skill (`Write this as .sdlc/work/NNN-<slug>/spec.md and advance the change to stage: design?`), but its only placeholder is the folder name, so there is nothing a model could get wrong in it; left out of this change, per the intent's scope. → seed: 2026-11-18-10
- [x] `build_question()` writes `1 round` where the old template would have read `1 rounds`; only a host setting `rounds = 1` or `[light] rounds = 1` sees it. → dropped: already done in this change on purpose (it fixes the grammar), and it is shown at ship as F2
