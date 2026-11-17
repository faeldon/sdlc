DECISION: ESCALATE

**Why.** The build looks done. All 19 requirements are built and tested by the reviewers' account. Round 1 passed for both reviewers (code, test), the gate passed (2319 passed, 13 skipped), and the one decision, D1, is ticked by you. I'm escalating because the change touches published interfaces: it adds a key to the `Sdlc-Findings` trailer (`agents=`), adds new `By:` values to `findings.md`, changes `templates/findings.md`, changes the approver's `UNDONE` grammar (`→ bug:`), and edits `guide/review.md`, which every host's review doc answers. Two gaps also remain. The code reviewer says it didn't read the prose diffs (guide, ship skill files, agent prompts). And the spec's condition for keeping the reviewer prompt edits, a paid `/sdlc-factory:eval` before and after, was never run.

**Open items** (no CHANGE is open; these are what the reviews left unchecked)
- Prose diffs in `guide/review.md`, `skills/ship/*.md`, `plugins/factory/agents/reviewer-*.md` and `approver.md` were never read by a reviewer, only grep-checked. Raised by the code reviewer's "Unsure".
- The `sdlc.py drift` output was only partly read by the code reviewer. The builder's evidence shows `breaking: 0, refresh: 0, report: 0`.
- `bad_bugs()` would print an empty list of severity words if the process doc names none. Optional, from the code reviewer.
- The paid `/sdlc-factory:eval` before and after the R4/R6 prompt edits was not run. The spec says to keep those edits only if `reviewer-code`'s score holds. The builder flagged this as your call.
- The manual scratch factory run (`carry` twice, approver `→ bug:`, land files the bug) was not run. From the builder.

**Decisions to confirm**
- None unticked. D1 was decided by you (R15 gaps as undone notes, bugs done in this change, R6 kept, history tally first), and notes.md shows the build follows it.

**For the person at ship**
1. `guide/review.md`'s `## Review dimensions` section and the Pass 1 rule. Every host reads this text in place, so check it holds no prompt and needs no host edit (R2).
2. `scripts/sdlc.py`'s `findings_trailer()` and `ship_findings()`. Every existing key must count exactly what it counted before, with only ` agents=<n>` appended.
3. `factory.py`'s `write_findings()` and `_dispose()` (the bug filing), and the `bad_bugs()` refusal path in `land_signals()`.
4. Two departures, both explained in plan.md: R11's keep rule lives in `skills/ship/factory.md` rather than `SKILL.md` (the line budget), and the regex is `FINDING_NIT_RE` rather than `NIT_RE` (that name was taken).
5. Whether to run the paid eval before landing the reviewer prompt edits.

- IMPACT: minor — hosts can newly file pre-existing factory findings as `[bug]` entries at landing or by hand, factory runs now write `findings.md`, the code reviewer gains a context pass, and `Sdlc-Findings` gains `agents=`; all existing trailer keys keep their meaning.

- UNDONE: gap: security: ship checks only secrets, plus the fresh reviewer on a sensitive path; it has no security pass at the depth of the factory's `reviewer-security`. → seed: Ship's security pass at the factory's depth
- UNDONE: gap: end-to-end: ship never runs the spec's path end to end, as the factory's `reviewer-behaviour` does at landing. → seed: Ship runs the spec's path end to end
- UNDONE: gap: ui: ship has no UI review of a change that renders a page, where the factory runs `reviewer-ui` when `[ui]` is set. → seed: Ship's UI review for changes that render a page
- UNDONE: gap: ux: ship has no UX review, where the factory runs `reviewer-ux` when `[ui]` is set. → seed: Ship's UX review when `[ui]` is set
- UNDONE: gap: nits: the factory records its agents' `- NIT:` lines in `findings.md` but never weighs them (theme, cost, value) or files them as `[nit]` entries, as ship does. → seed: Factory weighs its agents' nits and files them as `[nit]`
- UNDONE: gap: landing rounds: `findings.md` holds only the build rounds (`reviews/round-<N>/`); the landing's review rounds (`reviews/land-<n>/`) are not in it. → seed: Landing review rounds in `findings.md`

- RECOVER: templates/findings.md: `git revert <commit>` puts the old note back, and since the template is read in place it reaches every host on the next release. A revert can't undo `findings.md` files already committed with landed changes, which keep their factory `By:` sections. Fix forward: the follow-up keeps `AGENT_ROLES` in `FINDING_BY` even if the rest is reverted, so `sdlc.py findings` doesn't report `By: code` as a problem on those changes.
