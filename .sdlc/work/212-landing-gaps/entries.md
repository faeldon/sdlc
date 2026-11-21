# 212-landing-gaps — entries

## [2026-11-21-24] [idea] Let ugrep's `-O EXT` pass the read-only grep check while BSD's `-O` stays refused

Left undone by 212-landing-gaps, carried forward when it landed: pre-existing: plugins/factory/scripts/landing.py:816: `GREP_FOLLOWS` refuses `-O` (BSD's follow-links flag) for every grep, so ugrep's harmless `-O EXT` (search by file extension) is refused too. This is overly strict, not a hole.
See .sdlc/work/212-landing-gaps/notes.md in its commit.
Raised 2026-11-21.

## [2026-11-21-25] [nit] the `--filter`, `--pager` and `--view` refusals match the exact name only, not `--filter-magic-label`.

Raised by the code review of 212-landing-gaps, round 1: plugins/factory/scripts/landing.py:921: the `--filter`, `--pager` and `--view` refusals match the exact name only, not `--filter-magic-label`. That is harmless and ugrep takes no prefixes, but a comment saying so would help.

Theme: docs
Paths: plugins/factory/scripts/landing.py
Cost: S
Value: low
Raised by: 212-landing-gaps (correctness)

## [2026-11-21-26] [nit] a GNU or BSD grep refusal of `--config` or `---…` says "makes ugrep …", which may confuse a person reading it on a host without ugrep.

Raised by the security review of 212-landing-gaps, round 1: plugins/factory/scripts/landing.py:925: a GNU or BSD grep refusal of `--config` or `---…` says "makes ugrep …", which may confuse a person reading it on a host without ugrep. "makes grep (ugrep) …" would be clearer

Theme: docs
Paths: plugins/factory/scripts/landing.py
Cost: S
Value: low
Raised by: 212-landing-gaps (contract)

## [2026-11-21-27] [nit] no case checks a bare `-d dereference-recurse` word that is really a grep pattern, which D2 accepts refusing.

Raised by the test review of 212-landing-gaps, round 1: tests/test_train.py:2340: no case checks a bare `-d dereference-recurse` word that is really a grep pattern, which D2 accepts refusing. A pin would document the trade-off.

Theme: tests
Paths: tests/test_train.py
Cost: S
Value: low
Raised by: 212-landing-gaps (correctness)
