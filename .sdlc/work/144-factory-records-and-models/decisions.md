# Decisions

- [x] D1 (builder round 1, default): Should a `[models]` table in the change's own checkout that differs from the base branch's give a warning? Going ahead with a warning, as `mode`, `gate_jobs` and `[ui]` already do, unless told otherwise. → settled by the approver: the intent's Approach asks for "the warning `mode` already gives" when the checkout's value differs, which answers its own open question. `_models()` does exactly that. `test_models_are_the_base_branch_s_even_for_an_older_worktree` covers the warning and shows it clears once the two tables match, and both reviewers checked it against the intent (code.md, behaviour.md).
  - OPTION: warn — same as the other base-branch settings; a person who edits it in a change learns why it has no effect
  - OPTION: ignore silently — less noise; the edit seems to do nothing, with no reason given
  - WHY: the intent's Approach asks for the warning `mode` gives, and it answers the intent's open question the same way the other settings do
- [x] D2 (builder round 1, default): Keep the hand edit of attempt 1's quoted output in `build/round-1.gate.md`? Going ahead with it unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: keep the edit — the gate can pass again; one quoted citation in the record differs from what the gate printed
  - OPTION: restore the original line — the record is exactly as the gate wrote it; every gate run on this change stays red until the scan or the filing changes
  - WHY: without the edit no build of this change can pass, and the intent shows the person fixed records the same way by hand on 2026-11-18
