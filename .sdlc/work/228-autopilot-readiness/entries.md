# 228-autopilot-readiness — entries

Retire 2026-11-21-51: taken in by 228-autopilot-readiness
Retire 2026-11-21-53: taken in by 228-autopilot-readiness
Retire 2026-11-21-54: taken in by 228-autopilot-readiness
Retire 2026-11-22-1: taken in by 228-autopilot-readiness
Retire 2026-11-22-2: taken in by 228-autopilot-readiness
Retire 2026-11-22-11: taken in by 228-autopilot-readiness

## [2026-11-22-27] [nit] the reflowed sentence leaves one line well past the 100-column wrap the rest of the paragraph keeps ("outside a code fence), which answering would land unbuilt; a `verdicts` stop; one `land-check` excludes or the train").

Raised by the code review of 228-autopilot-readiness, round 1: plugins/factory/README.md:606: the reflowed sentence leaves one line well past the 100-column wrap the rest of the paragraph keeps ("outside a code fence), which answering would land unbuilt; a `verdicts` stop; one `land-check` excludes or the train"). Re-wrap it.

Theme: docs
Paths: plugins/factory/README.md
Cost: S
Value: low
Raised by: 228-autopilot-readiness (correctness)

## [2026-11-22-28] [nit] the end-to-end test names its assertions on `"→ decided by autopilot: keep it"`.

Raised by the code review of 228-autopilot-readiness, round 1: tests/test_autopilot.py:1576: the end-to-end test names its assertions on `"→ decided by autopilot: keep it"`. That text depends on the stand-in builder's blocking line, so a change to `BUILDER_RAISES` would break it at a distance. Reference a shared constant instead.

Theme: tests
Paths: tests/test_autopilot.py
Cost: S
Value: low
Raised by: 228-autopilot-readiness (correctness)
