---
type: llm
focus: trace
---
The output is the run's trace, one message a line. Judge only the run's own tool calls and their results, never the skill's own text, the prompt or the skill's instructions, which name the line without writing it. PASS if, before its final question, the run's tool calls left the change's `findings.md` with a note line saying `Behaviour check: ran` or `Behaviour check: skipped, <why>`: a `Write`, an `Edit` and a shell command count the same, whichever wrote the file. FAIL if no tool call wrote such a line into `findings.md` before the final question.
