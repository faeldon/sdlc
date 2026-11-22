
**Changes from the last draft, as you asked**

- **R4** gains clause (e): `docs` joins whenever the diff touches any path outside `tests/` and the change folder. Ship's pass (R9) uses it too. Its tests, the cost note and the edge cases follow from it. "Join only by (a)–(d)" is now a rejected alternative.
- **R12** is split into six doc edits. Each gets the text it must hold, the test that fails without it, and a grep in Verification.

**Open questions resolved**

- **Join on its own, or go into the default `reviewers` lists?** On its own, like `ui` and `ux`. The intent's Outcome needs a host with its own list still checked after upgrading, and only joining outside the list does that. A host whose list names `code` alone gets `docs` whenever R4 holds (R3, R11).
- **One key or two?** Two: `[docs] context` and a new `[docs] reviewed`. `context` is read as session context by ship's Context pass (`CONFIG_KEYS`, `_context_report()`). Putting user docs in it would change what that pass weighs. With nothing set, the reviewer reads today's `context` list (R5). The key's name, `reviewed`, is a suggestion and is easy to rename before the build.
- **Which diffs call it in?** Your call: R4's (a)–(e). That means any path outside `tests/` and the change folder, plus a test-only path that a doc names or that has a `CLAUDE.md`/`AGENTS.md` above it, plus every later round of a run it already joined.
- **At ship, every diff or only deep ones?** By the same rule as the factory, at any depth (R9), which follows from your R4. Deep-only would leave a hand-built change's `docs.reviewed` docs checked by nothing.

**Open questions left for you**

- **Should it also flag a doc repeating what the code or another doc says?** As drafted, only falsity and what's missing are checked; the one exception is the context docs, where the old pass's pointer rule is kept. Adding repeats widens the bar and the number of findings, which is a cost and noise choice.
- **No nits taken in:** the intent names none.
