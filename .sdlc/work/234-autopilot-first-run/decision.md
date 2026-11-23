DECISION: ESCALATE

**Why:** The diff is `.sdlc/factory.toml` alone, as the intent scoped it. `gate_jobs` goes from 2 to 1 and `[autopilot] enabled = true` is added, with `guards` left unset. All three reviewers PASS, the gate is green, and nothing in the reviews suggests the spec was wrong. D1 is still open. It decides whether an unattended mode stays enabled after the run, which is a policy call, so I can't settle or confirm it.

**Open items:**
- NIT (code reviewer): the `factory.toml` header comment is seven lines of history. A shorter one would age better. This is minor, and no `notes.md` exists to carry it.
- Unsure (docs reviewer): the comment cites "M24's 2026-11-22-38", and nobody checked that the seed exists in `.sdlc/work/inbox.md`.
- The behaviour reviewer couldn't run the base-branch checks (`factory.py config`, `autopilot --preview`) from the worktree. The intent defers them to the main checkout after close.

**Decisions to confirm:**
- ESCALATED: D1: Whether autopilot stays enabled between runs is a policy call about an unattended mode. The intent's first open question left it to the person, so only they can choose.
  - Leaving it on starts nothing, because `--begin` still needs the person's WAIT approval. The person should still pick consciously. The options are in `decisions.md`.

**For the person at ship:**
- Look first at `.sdlc/factory.toml`: the `gate_jobs = 1` line and the `[autopilot]` section.
- After close, from the main checkout, run `factory.py config` and `factory.py autopilot --preview --seeds 2026-11-22-49 2026-11-22-50 2026-11-22-51`. They should show `gate_jobs` 1 and `"enabled": true`.
- The intent's second open question is still unanswered: -50 and -51 are in "decide", which autopilot never takes. Settle that before `--begin`.
- No published interface is touched. The intent lists its contracts as none.

- IMPACT: none — an internal factory setting in this repo's own file. Nothing anyone holding the previous release receives has changed.

**Undone items:** `notes.md` doesn't exist, so there are none.
