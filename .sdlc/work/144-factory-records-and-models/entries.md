# 144-factory-records-and-models — entries

## [2026-11-18-61] [idea] Defuse forbidden path shapes when filing gate output and builder Evidence

Left undone by 144-factory-records-and-models, carried forward when it landed: A gate record that quotes a line in a shape `test_nothing_local` refuses keeps every later gate red: `factory.py gate` files the output's tail into `build/round-<N>.gate.md`, which the next run's scan reads. Seen on this change's round 1, where the builder's report quoted a red test's output holding the fixture's `work/<number>*` glob and the gate's record quoted the scan's report of it; both copies were rewritten as `work/NNN*` by hand. Filing gate output (and a builder's Evidence) with `PATTERNS`' shapes defused would close it for any number, not only the change's own, which this change rewrites.
See .sdlc/work/144-factory-records-and-models/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-62] [nit] `work/008*x` is rewritten to `work/008-slug*x`, because the regex backtracks off the `*` and the lookahead then passes on `*`.

Raised by the code review of 144-factory-records-and-models, round 1: plugins/factory/scripts/factory.py:2822: `work/008*x` is rewritten to `work/008-slug*x`, because the regex backtracks off the `*` and the lookahead then passes on `*`. The shape is unrealistic, but `(?![\w-])` after an optional `\*?` could be made possessive or tightened

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 144-factory-records-and-models (correctness)

## [2026-11-18-63] [nit] the re-wrapped paragraph leaves one over-long line (`serve`, `shoot` and `paths` …)

Raised by the code review of 144-factory-records-and-models, round 1: plugins/factory/README.md:383: the re-wrapped paragraph leaves one over-long line (`serve`, `shoot` and `paths` …)

Theme: docs
Paths: plugins/factory/README.md
Cost: S
Value: low
Raised by: 144-factory-records-and-models (correctness)
