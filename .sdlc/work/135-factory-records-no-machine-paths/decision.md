DECISION: ESCALATE

**Why.** The build looks finished, and I'd likely call it ready once the person confirms the three choices below. Round 2's review is `VERDICT: PASS`, its gate is green (2408 passed, 13 skipped), and the review agrees with the builder that the one round-1 finding (F1) is fixed. It escalates only because `decisions.md` has three unticked defaults (D1–D3). Each answers one of the intent's open questions, and the build rests on all three without the person having confirmed any.

**Open items**
- None. F1 (from `code`: `is_read()` took `<home>` for a redirect) is marked fixed and round 2 checked it. F2 is the pre-existing item below, and the same fix covers it.

**Decisions to confirm**
- D1: the home directory is written as `<home>`, not `~`, in both `factory.py` and `sdlc.py`'s copy. This changes the text of every gate record from now on: older records keep `~`, newer ones say `<home>`.
- D2: replies are checked for paths only, not against `.sdlc/terms.local`.
- D3: the agents' prompts are unchanged; the script's path replacement is the whole fix.

**For the person at ship**
- Look first at `plugins/factory/scripts/factory.py`, in two places:
  - `cmd_agent`: there should be one `_placeholders(reply, root)` call, placed after the success check and before any write, so the plain write, the append and `_file_draft()` all get it.
  - `is_read()` (around `:1349`): the mark swap. Make sure it replaces only the exact marks and that a real redirect is still not counted as a read.
- Then check that `HOME_MARK` is the same in `scripts/sdlc.py`, `tests/test_hand_gate.py` and the hand gate paragraph in `docs/REFERENCE.md`. The round-2 reviewer left those files alone as outside that round's scope; round 1 reviewed them.
- Finally, check that `test_every_reply_is_filed_without_this_machine_s_paths` really covers the `git worktree list` case (Outcome 3).

- IMPACT: patch — factory records and hand gate records stop filing this machine's paths, so a landing no longer fails its gate on its own records. The only visible change is that the home directory is now written as `<home>` instead of `~` in records from now on.

- UNDONE: pre-existing: plugins/factory/scripts/factory.py:1348: the same tokenisation makes `git -C <path-to-clone> status` a non-read, since `CLONE_MARK` already has `<`/`>` in it. The fix above covers both marks, so it can be filed with this change or on its own. → dropped: fixed by this change: `is_read()` now swaps both `<home>` and `<path-to-clone>` before tokenising, and `test_a_read_naming_a_mark_is_still_a_read` covers both marks.

**How to recover:** the prompt names no irreversible paths. `plan.md`'s rollback is `git revert`, and records already committed keep `~`.
