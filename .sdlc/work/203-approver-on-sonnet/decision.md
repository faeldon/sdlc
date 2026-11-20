DECISION: READY

**Why.** Both reviewers (code and behaviour) passed in round 1, and the gate passed (`./check.sh`, 3540 passed). The intent asks for one thing: `.sdlc/factory.toml` sets the approver to sonnet at both depths, with a comment naming the trial and how it will be judged. The change does exactly that, in one file, and leaves the plugin's defaults alone. The intent's check that `factory.py config` shows sonnet can't pass before landing, because `config` reads `[models]` from the base branch's copy. The builder explained this and checked the setting another way. That's a timing issue, not an error in the spec.

**Open items**
- None. Every round-1 verdict is PASS and nothing is left undone (there is no `notes.md`).

**Decisions to confirm**
- None. There is no `decisions.md` and no open default.

**For the person at ship**
- **Look first at the diff to `.sdlc/factory.toml`:**
  - the new `[models]` table, which holds only `approver = "sonnet"`;
  - its trial comment, which says the next retrospective judges the trial by READY changes that escaped and ESCALATEs found empty;
  - the reworded header line, "Only [ui] and [models] differ".
- **Read `factory.py config` again after landing.** It should show `approver` on sonnet in `models_at`. Until then it shows `"models": {}`, by design (both reviewers and the builder noted this). The check in `checks.md` reads this checkout's file through `_models()` and `model_for()` instead. It got sonnet for Tier 1 and Tier 2, at light and full depth.
- **The config you already approved:** this is the repo's own `.sdlc/factory.toml`, not a plugin default. Every later factory run's approver reads it from the base branch. The intent approves this under *Affected* (`.sdlc/factory.toml`) and *Approach* (set `[models]` for the approver at full and light depth).

- IMPACT: none — only this repo's own factory config changes; nothing in the plugin or its defaults that a host receives is different.
