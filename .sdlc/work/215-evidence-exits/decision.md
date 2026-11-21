DECISION: ESCALATE

**Why:** The build does what the intent's Outcome asks. The three prompts, the mend text and its goldens, and the README now ask for `exit:` on every command. `is_read()` is unchanged. Both reviewers PASS, the gate is green, and no Critical or High finding is open. The intent's Approach said to take in nit 2026-11-20-47, and the build left it out. That is a scope call, so only the person can decide D1.

**Open items**
- None. Both reviewers PASS. Code's only note is a low docs NIT: AGENTS.md's wording is left alone, and notes.md explains why.

**Decisions to confirm**
- ESCALATED: D1: The build left nit 2026-11-20-47 (`intent_closes()` read from the fork point) out, although the intent's Approach said to take it in. Dropping an item from the approved scope is the person's call. The default is to leave it out and keep the follow-up in notes.md. The fork point holds no `intent.md` in a factory run, so reading `closes:` there would let every change carry a `- CONFIRM:` default its intent forbids.
  - OPTION: leave it out, keep the follow-up in notes.md — the bar stays as it is, but a build can still remove its own `closes:` line.
  - OPTION: read the fork point and the working copy together — nothing is loosened, but in a factory run the fork point never holds `intent.md`, so it does nothing.
  - OPTION: record the approved `closes:` in the records ledger at `start` — this actually fixes it, but it adds a new mechanism, more than an S nit.
  - WHY: The change's folder is untracked until ship commits it, so a fork-point read finds no `closes:`. That read alone would loosen the bar.

**For the person at ship**
- First look at `cmd_accept()` in `plugins/factory/scripts/factory.py`. It now re-checks that its record is still vouched, and `test_a_record_forged_while_accept_ran_is_never_appended_to` covers it.
- Then look at the wording test and the `read_evidence()` test in `tests/test_factory_depth.py`.
- Then look at the three agent prompts, `prompts/mend.md` and its goldens.
- No published interface is touched. `read_evidence()` and `is_read()` are unchanged in behaviour.

- IMPACT: patch — the factory's agents are asked for an `exit:` on every command, so there are fewer mend stops. Nothing a holder of the previous release has to do changes.

- UNDONE: Record the intent's `closes:` at `start` in the records ledger, and have `intent_closes()` read the union of it and the working copy (nit 2026-11-20-47, done right). → seed: Record an intent's `closes:` in the records ledger at `start`
