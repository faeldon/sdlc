DECISION: ESCALATE

**Why:** The build does what the intent's Approach says. `ask --answered` gives `rebuild` for a confirmed reviewer or approver default with no later `- BUILT:` line, and a builder's own default still goes to `ship`. Both reviewers passed it, and the gate is green with 3952 tests passed. It escalates only because D2 is a scope default, which can't be settled or confirmed on my word.

**Open items**
- None. The code and behaviour reviewers each raised nits only. They are a wrap-width line in the README and a comment for `source` values that don't match `round N` at `factory.py:2325`.

**Decisions to confirm**
- SETTLED: D1: the intent's Approach and open question call for the script to decide from the files alone. `unbuilt_defaults()` and `BUILT_RE` do that with a `- BUILT: D<n>` line from a later round. The code and behaviour reviews of round 1 checked the same-round and wrong-id cases and raised nothing against it.
- ESCALATED: D2: whether autopilot should hold a change carrying an unbuilt reviewer default is a scope and policy call, and `autopilot.py` never calls `cmd_ask`. Until the person decides, autopilot can still land a reviewer's default nobody built, which is the 216 gap.
  - OPTION: leave it for a later change (the default) — keeps 218 at the size its Approach sets, but the autopilot gap stays open
  - OPTION: autopilot holds such a change — closes the gap, but widens 218 into autopilot's hold rules, which the Approach doesn't cover
  - WHY: the default keeps the change small, and the intent itself leaves the autopilot question open.

**For the person at ship**
- Read `unbuilt_defaults()` and `cmd_ask()` in `plugins/factory/scripts/factory.py` first. Then read the `- BUILT:` instruction in `plugins/factory/agents/builder.md`, which is the new contract the builder must follow.
- `ask`'s `next` values are unchanged, only when each is given. No published interface the person hasn't approved is touched.

- IMPACT: patch — `ask` now catches an unbuilt confirmed reviewer default, and nothing anyone receives has to be done differently.

`notes.md` does not exist, so no `- [ ]` items need a disposition.
