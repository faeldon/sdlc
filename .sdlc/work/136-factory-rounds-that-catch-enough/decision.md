DECISION: READY

**Why.** Both reviewers found code and a test for each of R1–R10. The one round is all `VERDICT: PASS`, and the gate passed on `./check.sh` (2414 passed, 13 skipped, validate passed). Nothing is left but four nits and one board follow-up. The two default changes (R1 `behaviour` added to the light rounds, R2 sonnet instead of haiku) were the person's call: `intent.md` strikes that question as "Resolved: enough to change R1 and R2". Where the build went beyond `plan.md` (`skills/build/SKILL.md`, `docs/REFERENCE.md`, `read_decision()`'s message, `import re`), the plan now lists it.

**Open items.** No CHANGE is open. These nits were recorded, not fixed:
- NIT (code): `plugins/factory/skills/build/SKILL.md:416` still says `exhausted` only means "rounds ran out". It should say the approver is also told about a `stuck` or `untestable` stop.
- NIT (code): check that the word-for-word re-raise sentence in `plugins/factory/agents/reviewer-ux.md` reads the same as in the other five reviewer prompts. Its diff is 5 lines where the others are 8.
- NIT (test): no test checks R6's README table, so a person should compare it against each change's `Close` commit.
- NIT (test): the R3 test has no case where round N-1 has no `verified.md`.

**Decisions to confirm.** None. This change has no `decisions.md`, and the builder reports "No decisions raised". The spec-writer left two questions, both settled:
- The defaults question is resolved in `intent.md`.
- 129's tier question is settled by R6's table, which records 129 as Tier 2.

**For the person at ship.**
1. **What this costs every host.** R1 and R2 change what every `sdlc-factory` host gets when its `.sdlc/factory.toml` doesn't set these keys. Tier 1 light rounds now run `code, behaviour` on sonnet, which is one more agent run per round, each at sonnet's price.
   - In `factory.py`, check that `light_reviewers()` adds `behaviour` only after the `chosen` check, and only when the full depth holds it.
   - Check that `model_for()` still lets a `[models]` entry win.
2. **The early stop.** Read `early_stop()` and how `loop_state()` uses it. It should read round files only, compare only rounds at or after `first`, and set `stuck`/`untestable` only once the last round is complete and verified. A wrong stop here would escalate runs that could have converged.
3. **The README table.** Compare *Why these defaults* in `plugins/factory/README.md` with the four `Close` commits, since no test checks it.
4. **Retro's count.** Check that `_landing_catches()` in `scripts/retro.py` counts only factory-role `By:` findings, and doesn't touch ship's `Sdlc-Findings` counts.
5. **A gap in this build's own review.** It ran at the light depth (code and test only), so no `behaviour` reviewer looked at it, which is the very gap R1 closes. The landing's `behaviour` round is its second look.

- IMPACT: minor — hosts get an early escalation on a change kept twice or a requirement the builder marks untestable, a new `Landing catches` line in the retro, and a stronger default light depth (`behaviour`, sonnet). Nothing a host set changes, and a host that wants the old cost back can set `[light] reviewers` or `[models]`.

- UNDONE: The board's step track and `runs/stopped.md` don't show `stuck` or `untestable`: an early stop reads on the board as a plain `approve`. Worth a line on the card once the retro's counts show how often it happens. → seed: Show an early stop's reason (stuck/untestable) on the board's card and in runs/stopped.md
