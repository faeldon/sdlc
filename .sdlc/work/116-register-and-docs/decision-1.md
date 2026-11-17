DECISION: ESCALATE

**Why.** The build looks finished. Round 2's code review is `VERDICT: PASS`, round 1's one kept CHANGE (CONTRIBUTING.md's intake paragraph wrongly said close never calls `mark()` without `intake()`) was fixed and checked against the code, and the recorded gate (`./check.sh`, 2191 passed, 9 skipped) and the acceptance checks pass. It escalates on one thing only: decision D1 is still an unticked default. The CONTRIBUTING.md text rests on it, so you need to confirm it before landing.

**Open items**
- None. Round 2 kept no CHANGE. The code reviewer left two optional suggestions in the round-2 notes:
  - Close's `mark()` step runs only once the change has landed cleanly, which the paragraph's "whenever the tracker has `mark()`" leaves out.
  - `sync`'s mirroring isn't gated, only its marking.

**Decisions to confirm**
- D1: CONTRIBUTING.md's *Writing a tracker* names `unmark()` as GitHub's own method, which core doesn't call yet. It is not documented as part of core's interface and not wired into core. The intent's Outcome listed `unmark()` among the intake methods core calls, so this departs from the intent. `plan.md` explains it, and the code reviewer accepted it in round 1.

**For the person at ship**
- Read `docs/CONTRIBUTING.md` around line 193 first: the intake-methods paragraph and its list, especially how it words `unmark()` (D1) and close's exception.
- Then read `skills/idea/SKILL.md`'s `--themes` paragraph and its new `allowed-tools` rule for `sdlc.py status`. This is the one change in behaviour, pinned by `test_idea_themes_leave_out_what_status_lists_as_being_built`.
- The `scripts/sdlc.py` edits should all be `#` comments. Line 7144 (`recorded_issues()`'s docstring) still names `unmark()`, and that is the undone item below.

- IMPACT: patch — `/sdlc:idea --themes` no longer proposes a theme for a seed an open change is already building. Everything else is comments and contributor docs, and nobody has to do anything differently.

**Undone items**
- UNDONE: `recorded_issues()`'s docstring names the tracker's `unmark()` among what sets its records, but core never calls `unmark()` (only GitHub's tracker has it, and its test calls it directly): either wire it in where a record is withdrawn (a drop, a change no longer closing an issue) or take it out of the docstring. → seed: Wire up or unname the tracker's unmark() in recorded_issues()
