DECISION: READY

**Why:** Both reviewers passed round 1, and the gate is green (`./check.sh`: 3055 passed, 28 skipped, exit 0). The regex change is identical in `factory.py:276` and `factory_records.py:90`, so the pin test holds. The tests cover every empty spelling and confirm that real gaps still stop the run, including `R3 needs a live GitHub` and `none of R3 can be tested`. The wait-without-sleep paragraph is in both `builder.md` and `reviewer-behaviour.md`, with a test. `plan.md` settles the intent's two open questions and says why: the regex rather than a filter, and the agent files rather than `common.md`. Because the guidance went into the agent files, no recorded prompt copy needed re-recording.

**Open items**
- None. The only finding is NIT F1 from `code`: `plugins/factory/README.md:203` runs to 136 characters and needs re-wrapping. It is recorded in `findings.md` and doesn't block.

**Decisions to confirm**
- None. There is no `decisions.md`, no open default and no unticked blocking line.

**For the person at ship**
- Look first at the regex at `plugins/factory/scripts/factory.py:276`: `(?!\s*(?i:none|n/?a)\.?\s*$)`. Check that the scoped `(?i:…)` behaves on the project's Python version. Also note that a whitespace-only `- UNTESTABLE:` line still counts as untestable, which is the old behaviour and outside the intent, as the behaviour reviewer said.
- Then read the bounded-loop example in `builder.md:65–69` and `reviewer-behaviour.md:36–40`.
- You may want to re-wrap README line 203 before committing.

- IMPACT: patch — a factory run no longer stops when a builder writes "none" or "n/a" as its untestable answer, and agents get better instructions for waiting. Nobody gains a new capability or has to change anything.

**Each undone item's disposition**
- None. There is no `notes.md` and no unticked items. The builder reports leaving nothing behind.

**How to recover**
- The prompt names no irreversible paths. `plan.md`'s rollback is a plain `git revert`.
