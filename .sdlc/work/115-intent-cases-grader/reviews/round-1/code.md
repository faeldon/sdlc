VERDICT: PASS

## Notes

- **The truncation claim is stated as "always", but it holds only in the common case.** The plan says the draft and question "are always in what the judge sees", because they are the run's last messages. The `trace` focus keeps only the first and last 12 messages past 24, and the head plus last 20k characters past 100k. So a tier proposal or draft that sits earlier in a long run is cut, and that is the same flaky FAIL this change exists to remove. The 24/100k caps are the builder's figures; I could not confirm them in the CLI binary. Outcome 1 says "every message", so this is a real gap, not just wording. Settle it by counting messages in one paid intent run's `--json` trace. If runs can exceed 24 messages, the prompt should ask for the draft and question in one message, which the Approach allows.
- **Outcomes 1 and 2 are not proven by anything here.** Outcome 2 (two runs agree) needs the paid pair of runs behind ship's prompt, as the plan says. Nothing in the diff can show it. Ship should not mark it met on the gate alone.
- **`intent.md` lists "the cases' suite file" under Affected, and the plan doesn't touch one or say why not.** Nothing in `evals/` looks like a suite file, so the omission is probably right. The plan should say so.
- **`test_a_judgment_grader_reads_the_whole_reply` pins the phrase "before its final question"** as well as `focus: trace`. The phrase is wording, so a harmless rewording of the criteria would fail the test. The `focus` assertion alone carries the requirement.

## Done well

- The test was written first and went red on both graders, then green, which is the order the plan asked for.
- The criteria tell the judge to read only the agent's own text. Without that, the trace would also hand it the SKILL.md example headings (Problem, Outcome, Affected, Constraints), and it could pass a reply that has no draft. `skills/intent/SKILL.md` is untouched, as the constraints require.
- The `focus` key is real. I checked the `claude` 2.1.311 binary: an `llm` grader's `focus` accepts `trace`, `last_message`, `files`, `mock_calls` or a file, and `last_message` is the default. The plan's premise holds.

## Checks I ran

- `uv run --group dev pytest -q tests/test_evals.py -k judgment`: 7 passed. The build's round-1 record also shows the red-then-green run and `./check.sh` at 2197 passed, 9 skipped.
- I read the diff in full: the two graders, the test, and the `CONTRIBUTING.md` sentence. I found no Critical or Required finding. Every requirement has code and a test that fails without it, except Outcome 2, which the plan assigns to paid runs at ship.

I'm not sure about the trace caps or about whether runs stay under 24 messages. A paid run's `--json` output would settle both.
