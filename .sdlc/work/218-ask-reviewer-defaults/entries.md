# 218-ask-reviewer-defaults — entries

## [2026-11-22-11] [nit] `BUILT_RE` matches a `- BUILT:` line anywhere in a builder report, including one quoted inside a code fence; skipping fenced blocks would stop a quoted line from counting as built

Raised by the security review of 218-ask-reviewer-defaults, round 2: plugins/factory/scripts/factory.py:2296: `BUILT_RE` matches a `- BUILT:` line anywhere in a builder report, including one quoted inside a code fence; skipping fenced blocks would stop a quoted line from counting as built

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 218-ask-reviewer-defaults (contract)

## [2026-11-22-12] [nit] the `cmd_ask()` docstring wraps short, leaving a line that ends at "while a".

Raised by the test review of 218-ask-reviewer-defaults, round 2: `plugins/factory/scripts/factory.py:2282`: the `cmd_ask()` docstring wraps short, leaving a line that ends at "while a". Reflowing it would read better.

Theme: style
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 218-ask-reviewer-defaults (correctness)
