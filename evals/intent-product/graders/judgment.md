---
type: llm
---
PASS if, before its final question, the reply proposes a `serves:` line for the change from the product doc's outcomes (O1, O2) without asking the person which outcome it serves, and shows where that proposal came from (the person's account, a seed, or inferred). FAIL if it asks the person which outcome the change serves, shows no `serves:` line, or shows one with no account of where it came from.
