DECISION: ESCALATE

**Why.** The build looks complete. The one round's code reviewer passed R1–R18 with no Critical or Required findings, the gate is green (2008 tests, both validations), and D1 was decided by the person and followed. I'm escalating because of what the change is: it loosens a gate on what reaches `main` without a person. The spec says so itself in *Contracts touched*: "a builder's edit made during landing can reach `main` without a person". It also rewrites the factory's own amend-before-rebase step and its `by=auto` close guard. Only the `code` reviewer looked at a change to the factory's own auto-landing rules, so a person should read those paths before they decide when the factory asks them.

**Open items** (minor, none blocking; there is no `notes.md`):
- README: the rewritten `/sdlc-factory:land` bullet has a line well over 100 columns and needs re-wrapping. Raised by `code`, Optional.
- `_amend_record()`: the "HEAD isn't the landing's commit" guard only runs when the tree is dirty. It's harmless because nothing is amended then, but it isn't a full check of R4's wording. Raised by `code`, Optional.

**Decisions to confirm**
- None. D1 is ticked (promote to Tier 2, with a spec for 34), and the build follows it.

**For the person at ship**
1. **`cmd_land_close()`'s R15 guard.** Check that it reads `Sdlc-Landed: by=auto` from `HEAD` before `_amend_record()` moves `HEAD`. Check that it refuses whenever `resolution_signals()` reports the landing resolution. This guard is now the only thing between a builder's resolution and `main` in a batch that passed itself (R16 removed the skill's stop).
2. **`land_verdict(..., settled=True)`.** This is a departure from R12's signature. `plan.md` explains it, and the builder showed a test failing without it. Confirm that it only keeps a round's last gate verdict standing after the landing's own amend moves `HEAD`. It must not count a round with no gate attempt as a pass.
3. **`_amend_record()`.** It runs `git commit --amend` on a branch. Check that it refuses any path outside the folder (R2) and that it only amends a commit carrying `Sdlc-Landed:` (R4).
4. **`retire_nits()` and `named_nits()`.** Check that they read only intent's `## Approach` and spec's `## Requirements`, and that they write only after ship succeeds (R6, R7).
5. **The skill cases' scope.** `preflight 097` reported an empty cases scope even though `plugins/factory/skills/land/SKILL.md` changed. Confirm that the factory's skill cases are meant to be out of scope, rather than that preflight doesn't see them.

- IMPACT: patch — it fixes four landing bugs. Nobody holding the previous release has anything new to do: a marker in the old format still asks, as before, and the new asking rules only drop a stop that was wrong or add one that was missing.
