I've built round 3: the spec gate's question no longer offers "rethink the design", in either skill. The gate passes (2410 tests), and nothing is committed (`HEAD` is still `d6a44d9`).

**Slice built (R1, which answers D4).** The spec gate's question now ends `(yes / revise a requirement)` in three places:
- `spec_question()` in `plugins/factory/scripts/factory.py`
- the sample question in Step 2 of `plugins/factory/skills/spec/SKILL.md`
- the question in Step 4 of `skills/spec/SKILL.md`

The dialog still has two answers, which is within the 2–4 the skills' tests allow, and `test_skills.py` passes.

**Tests.**
- **Changed test:** `test_start_words_the_spec_question` now expects `(yes / revise a requirement)`. Before the code change it failed because the old option was still there; after it, it passes. It is the test that pins the factory's wording.
- **New acceptance check** in `checks.md`, called "Neither spec gate offers "rethink the design"": the factory script and both skills must not contain the option, and both skills must still ask the two-answer question. This covers the core skill's wording, which only someone putting the option back could break. `sdlc.py accept 138` passes all three checks.

**`plan.md`.** Round 3 is added to "Files to change", "Work order" and "Tests". Nothing else in the approach changed.

**Left as it is.** The word "rethink" is still in two places, and neither is a gate answer:
- `scripts/metrics.py`'s `REVISE_RE` still counts "rethink" as a revising word, because it reads what a person types.
- `tests/test_metrics.py:591` has "no, rethink the design" as a person's typed reply.

**`notes.md`.** Nothing new.

**Decisions.** None raised this round. D4 is settled by R1. D1–D3 are still unticked defaults for you to confirm.

## Evidence

$ uv run --group dev pytest tests/test_factory.py::test_start_words_the_spec_question -q
FAILED tests/test_factory.py::test_start_words_the_spec_question - AssertionE...
1 failed in 7.29s
exit: 1

$ uv run --group dev pytest tests/test_factory.py::test_start_words_the_spec_question tests/test_skills.py -q
358 passed in 5.93s
exit: 0

$ uv run --quiet --script scripts/sdlc.py accept 138
  "passed": true,
  "problems": []
}
exit: 0

$ ./check.sh
All checks passed!
264 files already formatted
2410 passed, 13 skipped in 92.31s (0:01:32)
✔ Validation passed
exit: 0

$ git rev-parse --short HEAD
d6a44d9
