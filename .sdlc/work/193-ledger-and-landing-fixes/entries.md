# 193-ledger-and-landing-fixes — entries

Retire 2026-11-19-70: taken in by 193-ledger-and-landing-fixes
Retire 2026-11-19-71: taken in by 193-ledger-and-landing-fixes
Retire 2026-11-19-72: taken in by 193-ledger-and-landing-fixes
Retire 2026-11-19-74: taken in by 193-ledger-and-landing-fixes
Retire 2026-11-20-1: taken in by 193-ledger-and-landing-fixes

## [2026-11-20-7] [idea] Read-only list refuses ugrep's symlink-following long options (`--dereference-files` and its prefixes)

Left undone by 193-ledger-and-landing-fixes, carried forward when it landed: pre-existing: plugins/factory/scripts/landing.py:795: the grep refusals cover GNU grep and BSD grep only. If a host's `grep` on `PATH` is ugrep, `grep -r --dereference-files keep .` is allowed and follows links to files outside the checkout. This change didn't add or touch that gap, but it is in the same function. Fix: refuse `--dereference-files` and its prefixes too, or check every word against a list of such long options.
See .sdlc/work/193-ledger-and-landing-fixes/notes.md in its commit.
Raised 2026-11-20.

## [2026-11-20-8] [nit] `by_alts` is built from every ledger entry with options.

Raised by the code review of 193-ledger-and-landing-fixes, round 1: plugins/factory/scripts/factory.py:2018: `by_alts` is built from every ledger entry with options. The match relies on options and why being identical, so a very short shared option list could merge two real decisions. D1 already accepts this trade-off.

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 193-ledger-and-landing-fixes (correctness)

## [2026-11-20-9] [nit] the threshold `len(name) >= 5` counts the leading `--`, while the comment above `GREP_FOLLOWS_LONG` says "three or more characters after its `--`".

Raised by the security review of 193-ledger-and-landing-fixes, round 1: plugins/factory/scripts/landing.py:883: the threshold `len(name) >= 5` counts the leading `--`, while the comment above `GREP_FOLLOWS_LONG` says "three or more characters after its `--`". Writing it as `len(name) - 2 >= 3`, or naming the constant, would make the two read the same.

Theme: style
Paths: plugins/factory/scripts/landing.py
Cost: S
Value: low
Raised by: 193-ledger-and-landing-fixes (contract)

## [2026-11-20-10] [nit] the third test chains its cases in one body, so a failure in the first assertion hides the later cases

Raised by the test review of 193-ledger-and-landing-fixes, round 1: tests/test_factory.py:870: the third test chains its cases in one body, so a failure in the first assertion hides the later cases

Theme: tests
Paths: tests/test_factory.py
Cost: S
Value: low
Raised by: 193-ledger-and-landing-fixes (correctness)
