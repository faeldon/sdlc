DECISION: READY

**Why:** Every requirement R1–R13 has a test, by the test reviewer's account, and all four round-1 reviewers returned PASS. The gate record shows `./check.sh` green (4044 passed, 29 skipped). The code reviewer found no Critical or Required findings, and the security reviewer found none Critical or High. The build follows the approved spec. The builder's one fix, the unused fixture, is covered by that green gate. I did not run any tests myself.

**Open items:** none. These NITs are not blocking:
- code: `cited_paths` accepts a directory as a cited path.
- code: `preview` can list one alternative short when `--goal` is explicit.
- code: `## Left for you` has no pointer to the off-goal seeds.
- test: no empty-reason case for WAVE or LEAVE lines.
- test: no case for a LEAVE before any group.
- security: the skill's Step 1 should say to single-quote a goal given in the person's own words.

**Decisions to confirm:** none. There is no `decisions.md` for this change, so there are no blocking decisions and no open defaults.

**For the person at ship:**
- `plugins/factory/scripts/autopilot.py` is `[review] sensitive`, so ship's review goes to full depth. Start with these functions:
  - `candidates()`: the goal filter must only narrow.
  - `begin_goal()`: it re-resolves `--goal` and refuses rather than re-proposing.
  - `read_plan()`: it checks the planner's reply.
  - `cited_paths()`: it refuses absolute paths and `..`.
- In the diff, check that nothing writes `inbox.md` or the direction doc (R9).
- Also check `scripts/sdlc.py` (`direction_open()`, `status --json`) and the skill's single WAIT, whose question now names the goal.
- The person approved these in the spec's *Contracts touched*, and the build follows them as written:
  - the WAIT now also approves a goal;
  - `status --json` carries `direction`.
- The behaviour reviewer could not run `--begin`, because the harness denied a command that writes run state. R6, R9, R11 and R12 were checked through the tests only.
- The skill still says "in rank order" in a sentence about the candidate pool, and `prompts/autopilot.md` says "candidates in rank order". Both are accurate, since candidates are still ranked and then narrowed.

- IMPACT: minor — an autopilot run can now be given a goal and the report shows what it did toward it. Nothing a holder of the previous release already does has to change, and a state begun before this change still resumes.

**Undone items:** `notes.md` doesn't exist, and the builder says nothing was left in it. There are no unticked `- [ ]` items, so no dispositions to propose.
