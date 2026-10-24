# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `work/ideas.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Where the build departs from the plan

- The M2 acceptance check first read the direction doc through `sdlc.py retro`, and failed:
  `retro` reads the main checkout's copy, which holds the old `Groups:` line until this change
  lands. The check now parses this checkout's `.sdlc/DIRECTION.md` with the script's own
  `direction_items()`. Run against `main`'s version, it fails, so it does test the edit.
- The spec's verification line (`retro`'s groups) prints nothing on this branch: `retro` counts
  from the retrospective of 2026-10-24, and nothing has closed since. Run over all six closed
  changes instead, with this branch's `metrics_summary(…, 1)`: Tier 1 target 4.5, median stops 6,
  over 1.5; Tier 2 target 6, median stops 13.5, over 7.5.
- This repo's `.sdlc/setup.json` is recorded again (`sdlc.py record`), since the process doc's
  signal and the config keys changed; `sdlc.py drift` here reports nothing.
