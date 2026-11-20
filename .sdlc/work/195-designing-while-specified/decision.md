DECISION: ESCALATE

**Why:** The build does what the intent asks. Both reviewers passed round 1, `./check.sh` passed on build `7e6c663c0c3aea8c`, and the new test covers all five cases on both the board and `status` without changing any `stage:` line. One thing is left for you: D1 is the open question in your own intent ("Should it show under Needs you instead?"), which was never struck. The builder took a default for it, and I'm not settling it for you. D2 is a technical reading of the run records, and `plan.md` explains it.

**Open items**
- None. The two code-review NITs (F1 line wrap in REFERENCE.md:575, F2 `specifying()` refactor) are recorded in `findings.md` as minor. No CHANGE is unresolved.

**Decisions to confirm**
- ESCALATED: D1: Whether a draft waiting for your yes shows under Designing or Needs you is the open question in your intent's *Open questions*, and it was never struck. The Outcome's wording leans to Designing. But asking the question means you hadn't decided, and what Needs you means on the board is your product call, not something the spec settles.
- SETTLED: D2: `plan.md`'s *What the code says* shows that a first spec draft runs `factory.py agent --task spec` and writes no `runs/step.md`. The newest `runs/spec-writer.sessions` id with no `runs/costs.jsonl` row is the only record that meets the Outcome's "while its spec-writer runs" without touching the factory, which is outside *Affected*. `specifying()` at `scripts/factory_records.py:300` does this, `test_a_plan_change_being_specified_is_designing` covers a running session and a returned one, and the code reviewer called it a sound default. The one known cost: a session that crashes leaves the card under Designing. That only affects the display, and the ledger says so.

**For the person at ship**
- Look first at `column()` in `scripts/sdlc.py:5092`, the new `plan` + `specifying` branch, and `specifying()` in `scripts/factory_records.py:300`.
- One difference from the Approach: the Approach counts a draft only while `spec.md` is still its scaffold, but `specifying()` only checks that `runs/spec-draft.md` exists. The behaviour reviewer found it makes no difference, because a yes moves the change to `design`, and `column()` applies the rule only at `plan`.
- Interface already approved: `card_reading()` and `reading()` gain a `specifying` field, which feeds the board and `status`. The intent's *Affected* covers this ("`scripts/board.py` if the entry needs a new field", `factory_records.py`, `column()`).

- IMPACT: patch — the board and `/sdlc:status` now put a factory change being specified under Designing instead of Planned. Nobody has to do anything differently.

**Undone items**
- UNDONE: The board's step track (`_progress()`) shows nothing for a first spec draft, which records no `runs/step.md`; a card under Designing could show a `spec` step with its elapsed time. → seed: Show a spec step and its elapsed time on a Designing card
