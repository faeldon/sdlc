# Decisions

- [x] D1 (builder round 1, default): Set this repo's `retro.test_paths` to `["tests/"]` alone, leaving `evals/` out? Going ahead with `["tests/"]` unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: `["tests/"]` — fixes the `spec` misread; `evals/` files count as they do today (code or docs, by suffix); evals' drift goes unreported
  - OPTION: `["tests/", "evals/"]` — the skills' cases count as tests too; it shifts retro's totals and file counts by kind well beyond fixing the misread
  - WHY: the smallest setting that fixes the misread, leaving every other path counted as it is now
