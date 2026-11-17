I've built change 115. The intent cases' `judgment` grader now reads the whole run, not just the last message, and the gate passes. Whether two paid runs of each case now agree is still unproven: that needs the runs at ship.

**What the suite allows.** The intent's open question has an answer: `claude plugin eval` (2.1.311) lets an `llm` grader set `focus:` to `trace`, `last_message`, `files`, `mock_calls` or a file, and the default is `last_message`. The CLI reads that key from a grader `.md`'s frontmatter. With `focus: trace` the judge gets every message of the run. On long runs the middle gets cut (only the first 12 and last 12 messages are kept, and at most 100k characters, always including the last 20k), but the draft and the question come at the end, so they always stay. That means `prompt.md` and `skills/intent/SKILL.md` didn't need to change.

**Slices**
1. **Test (red, then green):** `test_a_judgment_grader_reads_the_whole_reply` covers every stop case. Each `llm` grader must set `focus: trace` and keep its "before its final question" criterion. It failed on `intent` and `intent-product` because both used the default. This is what pins what the grader is given, without a paid run (Outcome 3).
2. **The graders:** `evals/intent/graders/judgment.md` and `evals/intent-product/graders/judgment.md` now have `focus: trace`. Because the trace also holds the skill's own text and tool output, the criteria tell the judge to read only the agent's own text. They also say the draft, the tier and the question may come in one message or several. A reply that skips the draft or the tier still fails, and the intent case now names "shows no drafted intent" as a FAIL outright.
3. **Docs:** one sentence in `docs/CONTRIBUTING.md`, *The skills' cases*, saying a judgment grader uses `focus: trace` and why.

**Gate:** `./check.sh` is green, 2197 passed and 9 skipped; `tests/test_evals.py` passes 34.

**Not proven here:** Outcomes 1–2 (two runs of each case give the same verdict) need the paid runs of both cases, twice, behind ship's prompt, as the Approach says. I didn't run them. One risk is left: the judge model (haiku by default) is reading a much longer input now. The criteria point it at the agent's own messages, but only those runs will show whether that makes it steady.

**`plan.md`:** written (Tier 1, but four files). The build followed it.

**`notes.md`:** nothing left there.

**Not from this change:** `sdlc.py check --strict` exits 1 on one problem, and it isn't this change's. Change 118's folder (`118-retro-spend-indicators`) has no `serves:` line. A moment earlier the gate's own run reported 0 problems, so 118 probably appeared while I was working. I left it alone.

No decisions raised.

## Evidence

$ uv run --group dev pytest -q tests/test_evals.py -k judgment   (before the grader edit)
FAILED tests/test_evals.py::test_a_judgment_grader_reads_the_whole_reply[intent]
FAILED tests/test_evals.py::test_a_judgment_grader_reads_the_whole_reply[intent-product]
2 failed, 5 passed, 27 deselected in 0.30s
exit: 1

$ uv run --group dev pytest -q tests/test_evals.py -k judgment   (after)
7 passed, 27 deselected in 0.02s
exit: 0

$ ./check.sh
2197 passed, 9 skipped in 126.30s (0:02:06)
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_evals.py
34 passed in 21.99s
exit: 0

$ uv run --quiet --script scripts/sdlc.py check --strict
■ Problems: 1
    ⚠  …/.claude/worktrees/118-retro-spend-indicators/.sdlc/work/118-retro-spend-indicators: serves: missing; name the outcomes this serves from the product doc, or none
exit: 1
