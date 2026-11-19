VERDICT: CHANGES

- CHANGE: [context] docs/REFERENCE.md:544: it gives the look line as `- ESCALATED: look: <why>`, but the approver now writes `- ESCALATED: look: <what to look at> — <why>`. Update the line to the new form, and say that the decide question quotes the target.

## Notes
- NIT: plugins/factory/agents/approver.md:44: "a published interface the person hasn't approved" could be read as the qualifier covering "destructive operation" and "secret" too. The next paragraph says those stay looks whatever the spec says, but the sentence itself is ambiguous. Reword it, e.g. "a destructive operation, a secret, or a published interface the person hasn't approved". {docs S med}
- Done well: the `- ESCALATED: look:` form still matches `REASON_RE`, which takes everything after the kind colon, so the em dash and a colon inside the target both parse. `look` and `gate` stay the only kinds, so `factory.py` is untouched. The carve-out is narrow: only the person's approval covers an interface, never a settled or assumed default. The Critical/High, disagreement, spec-departure, missing-test, destructive and secret cases stay looks.
- Tests: `test_the_approver_raises_a_look_only_for_what_no_one_approved` and `test_decide_names_what_a_look_asks_to_see` pin the two wordings. These are string-presence checks on the prompt text, so they show the wording is there, not that the approver follows it.
- Not run: the gate record (`build/round-1.gate.md`) shows PASS, and I ran no tests myself. `plugins/factory/prompts/approve.md` is unchanged, and `prompts/common.md` still says never to settle a default about a published interface, which is consistent with this change.
