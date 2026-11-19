VERDICT: PASS

The change does what the intent's Approach says, and the gate record is green. I found nothing to rework.

## Notes
- There is no `spec.md`, because this is Tier 1, and the Approach names no end-to-end command. The change edits agent and skill prompt text, so the closest path is the tests that pin that text.
- I ran the targeted tests in `tests/test_skills.py` and 22 passed. They cover the approver's rule and the decide wording.
- `approver.md` now raises a look only for a published interface the person hasn't approved.
  - An interface the spec's *Contracts touched*, the intent's *Affected* contracts or the person's `→ decided:` answer already covers goes under *For the person at ship*. It gets no ledger line and no ESCALATE.
  - A Critical or High finding still open, a disagreement, a departure from the spec, a requirement with no test, a destructive operation and a secret stay looks.
  - A settled or assumed default never counts as approval, so the "when in doubt, escalate" rule holds.
- Each look's reason now starts with its target, in the form `<what to look at> — <why>`. `REASON_RE` in `factory.py` still reads the whole reason, and `factory.py` is unchanged, as the intent requires.
- The decide skill's look question now names the text before ` — ` and says what `seen` and `checked something` record. The WAIT and the two answers are unchanged.
- The README is updated to match. `plugins/factory/prompts/approve.md` is unchanged, and the intent only asked for it "if it words the rule".
- `checks.md` does not exist, so there are no acceptance checks to read.

## Evidence
$ cat .sdlc/work/182-looks-name-their-target/build/round-1.gate.md | head -5
GATE: PASS

## Attempt 1

Verdict: PASS
exit: 0

$ grep -n "exit\|passed" .sdlc/work/182-looks-name-their-target/build/round-1.gate.md | head
61:    3158 passed, 29 skipped in 160.75s (0:02:40)
79:    ✔ Validation passed
93:    ✔ Validation passed
exit: 0

$ git diff $(git merge-base HEAD main) --stat | tail
 plugins/factory/README.md              |  4 +++-
 plugins/factory/agents/approver.md     | 23 ++++++++++++++++++-----
 plugins/factory/skills/decide/SKILL.md |  9 ++++++---
 tests/test_skills.py                   | 27 ++++++++++++++++++++++++++-
 4 files changed, 53 insertions(+), 10 deletions(-)
exit: 0

$ grep -n "REASON_RE" plugins/factory/scripts/*.py | head -3
plugins/factory/scripts/factory.py:380:REASON_RE = re.compile(r"^\s*- ESCALATED:\s*([^\s:]+):\s*(.+?)\s*$")
plugins/factory/scripts/factory.py:1871:        m = REASON_RE.match(line)
exit: 0

$ uv run --group dev pytest tests/test_skills.py -q -k "look or approver or decide"
......................                                                   [100%]
22 passed, 396 deselected in 0.11s
exit: 0
