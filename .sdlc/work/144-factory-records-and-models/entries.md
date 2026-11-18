# 144-factory-records-and-models — entries

## [2026-11-18-62] [nit] `work/<008>*x` is rewritten to `work/008-slug*x`, because the regex backtracks off the `*` and the lookahead then passes on `*`.

Raised by the code review of 144-factory-records-and-models, round 1: plugins/factory/scripts/factory.py:2822: `work/<008>*x` is rewritten to `work/008-slug*x`, because the regex backtracks off the `*` and the lookahead then passes on `*`. The shape is unrealistic, but `(?![\w-])` after an optional `\*?` could be made possessive or tightened

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

## [2026-11-18-72] [nit] A record quoting a term from .sdlc/terms.local is still filed as written

DEFUSE covers the scan's PATTERNS only; the scan also refuses each regex in the main checkout's gitignored terms file, so a reply quoting one still reaches a landing's gate as written.
Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: M
Value: low
Raised by: 144-factory-records-and-models (correctness)
