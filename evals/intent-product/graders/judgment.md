---
type: llm
focus: trace
---
The output is the run's trace, one message a line. Judge only the agent's own text (the `text` blocks of `assistant` messages), never the skill's instructions, the prompt or a tool's output. PASS if, before its final question, the agent's text proposes a `serves:` line for the change from the product doc's outcomes (O1, O2) without asking the person which outcome it serves, and shows where that proposal came from (the person's account, a seed, or inferred); the draft and the question may be in one message or several. FAIL if it asks the person which outcome the change serves, shows no `serves:` line, or shows one with no account of where it came from.
