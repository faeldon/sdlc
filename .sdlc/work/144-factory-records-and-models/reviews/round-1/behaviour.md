VERDICT: PASS

I found no failures. The change has no `spec.md` and no `checks.md`, so I ran the closest path, which is the change's own tests. I also drove the new rewrite by hand on sample paths and read the diff against the intent's Outcome.

## Notes
- **`checks.md`:** none exists, so there is nothing to read or run.
- **`[models]` from the base branch:** `load_config()` now reads `[models]` through `_base_factory()`. Because `start`'s `models_at` and `agent` take their model from `cfg["models"]`, a base-branch entry reaches a change whose worktree predates it. I traced this in the diff and did not run it end to end. A different `[models]` in the change's own checkout only produces a warning, which matches `mode` and answers D1 in `decisions.md` the way the builder defaulted. The README text changed accordingly.
- **Citing the change's own folder:** `_own_folder()` runs in `cmd_agent` after `_placeholders()`. By hand it rewrote `work/144*/build`, `work/144/` and bare `work/144` to `work/144-x…`. It left `work/144-x/`, `work/1440` and `work/145*` unchanged.
- **Minor case:** `work/144*-x` becomes `work/144-x*-x`. That is a malformed citation and doesn't realistically occur, so I'm not raising it.
- **Gate record:** `build/round-1.gate.md` is green.
- **Tests:** 9 selected tests in `tests/test_factory.py` pass (`-k "models or bare or number or placeholder"`).

## Evidence
$ ls .sdlc/work/144-factory-records-and-models; head of intent.md; cat checks.md; head of decisions.md
(listed build, decisions.md, intent.md, notes.md, runs; intent read; checks.md: No such file or directory)
exit: 0

$ tail -15 .sdlc/work/144*/build/round-1.gate.md; git diff --stat; git status --short
(plugin validation passed; 3 files changed: README.md, factory.py, test_factory.py)
exit: 0

$ git diff plugins/factory/scripts/factory.py; uv run --group dev pytest tests/test_factory.py -q -n auto -k "models or bare or number or placeholder"
(diff as reviewed) 9 passed in 1.71s
exit: 0

$ python3 -I - (re.sub from `_own_folder` applied to sample paths)
.sdlc/work/144*/build -> .sdlc/work/144-x/build
.sdlc/work/144/ -> .sdlc/work/144-x/
work/144 -> work/144-x
work/144-x/ -> work/144-x/
work/1440 -> work/1440
work/145* -> work/145*
work/144*-x -> work/144-x*-x
exit: 0
