---
type: llm
focus: trace
---
The output is the run's trace, one message a line. Judge only the agent's own text (the `text` blocks of `assistant` messages), never the skill's instructions, the prompt or a tool's output. PASS if, before its final question, the agent's text proposes a tier for the change and gives a one-sentence reason for it, and shows a drafted intent with Problem, Outcome, Affected and Constraints sections; the draft, the tier and the question may be in one message or several. FAIL if it proposes no tier, gives no reason, shows no drafted intent, or says the change was already created.
