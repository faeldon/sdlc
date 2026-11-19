DECISION: ESCALATE

**Why.** The change does what the intent asks, and both round-1 reviewers returned `VERDICT: PASS`. `plugins/factory/agents/spec-writer.md` (lines 42–45) and `plugins/factory/prompts/spec.md` (line 10) now tell the spec-writer to put each nit it takes in on the `Nits taken in: <id>, <id>` line, using the wording `skills/spec/SKILL.md:76-79` uses. 181's `test_every_place_that_takes_a_nit_in_names_the_marker` now covers both files, and the full `./check.sh` gate passed (3250 passed, `GATE: PASS`). I am escalating for one reason only: D1 is a scope call (whether the spec-writer should also be given the open nits on the change's paths), and only you can confirm it.

**Open items**
- None. The only finding is a nit from the code reviewer: F1, `tests/test_skills.py:1939`, the `# 183` comments are redundant. It is recorded in `findings.md` as `recorded`, not as a requested change.

**Decisions to confirm**
- ESCALATED: D1: This is a scope question: should the factory's spec prompt list the open nits on the change's paths, as `sdlc.py nits --touching` does for `/sdlc:spec`? The intent's Constraints ("Wording only", "only those the intent's Problem or the person names") point to the default. But the open question in `intent.md` was struck by the builder, not by you, so only you can confirm that the factory's spec-writer should not get the same offer as the core skill.

**For the person at ship**
- Read the new bullet in `plugins/factory/agents/spec-writer.md:42-45` and the one-line `draft` text in `plugins/factory/prompts/spec.md:10` first. The re-recorded `tests/prompts/spec.txt` and `spec-upgraded.txt` should differ from the old ones only by that sentence.
- No published interface changes. `factory.py`'s `TAKEN_RE`, `NIT_SECTIONS` and `named_nits()` are untouched, and the marker keeps the form 181 gave it (`intent.md` *Affected → Contracts*).
- There is no `plan.md`. That is consistent with Tier 1, and `intent.md`'s Approach covers the work.

- IMPACT: patch — factory-drafted specs now put taken-in nits on the line the landing reads, so those nits are retired, which is a fix to existing behaviour. No interface or command changes.

There is no `notes.md`, so there are no undone items to dispose of. The prompt names no irreversible paths, so no recovery lines are needed.
