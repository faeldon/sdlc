# 155-agent-test-runs-share-the-slot — entries

## [2026-11-18-96] [nit] the rewrapped "One gate at a time" bullet leaves one line over the wrap width

Raised by the code review of 155-agent-test-runs-share-the-slot, round 1: plugins/factory/README.md:170: the rewrapped "One gate at a time" bullet leaves one line over the wrap width

Theme: style
Paths: plugins/factory/README.md
Cost: S
Value: low
Raised by: 155-agent-test-runs-share-the-slot (correctness)

## [2026-11-18-97] [nit] `FACTORY_CHECK_RE` accepts an optional quote after `.py`, so a quoted path matches, which the test covers.

Raised by the code review of 155-agent-test-runs-share-the-slot, round 1: scripts/metrics.py:132: `FACTORY_CHECK_RE` accepts an optional quote after `.py`, so a quoted path matches, which the test covers. The same quote case isn't handled for `HAND_GATE_RE`, so the two regexes treat quoted paths differently

Theme: robustness
Paths: scripts/metrics.py
Cost: S
Value: low
Raised by: 155-agent-test-runs-share-the-slot (correctness)

## [2026-11-18-98] [nit] the new R3 and R4 tests carry no `@pytest.mark.portable` even though the spec says "marked `portable` where they use no shebang fakes".

Raised by the test review of 155-agent-test-runs-share-the-slot, round 1: tests/test_factory.py:4900: the new R3 and R4 tests carry no `@pytest.mark.portable` even though the spec says "marked `portable` where they use no shebang fakes". The two-checks test uses `sleep` and `sh`, so leaving them unmarked is probably right, but the spec's intent is unclear.

Theme: tests
Paths: tests/test_factory.py
Cost: S
Value: low
Raised by: 155-agent-test-runs-share-the-slot (correctness)
