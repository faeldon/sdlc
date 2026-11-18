
Open questions I resolved:
- **First or last reply that holds the verdict?** The **last** one. If a wake-up reply changes
  or restates the verdict, that is the agent's latest judgment, and picking the first would file
  a verdict the agent replaced. When the last reply holds none (136's case), the one before it
  is filed. See *First or last* in Design. You can overturn this; the code doesn't decide it.
- **Should a missing `exit:` on a read-only command still need a mend?** No change is needed,
  and the code answers it. `read_evidence()` already judges a read by `is_read()` alone: a read
  that printed a line owes no `exit:` (`factory.py`, `read_evidence()`'s `close()`). A command
  that isn't a read, like a test run, gate or script, still owes one, and the intent's
  constraint keeps `is_read()` as it is.

Left for you:
- **The AGENTS.md policy edit.** The first-line rule from 2026-11-17-18 ("The first-line rule
  stands: the reply is never read as it was") is overturned. A verdict after prose is read, and
  only disagreeing answer lines are mended. Approving this spec approves that edit.
- **The stream's shape.** Not yet confirmed: whether a background notice in print mode adds a
  second `result` event or only `assistant` events. The design reads both. The plan's first step
  records one paid session to settle it (R3).
- **Evidence mend prompt.** It could name the commands that lack `exit:`, as `VERIFY_MEND`
  names its problems, so the mend succeeds the first time. That would help 125's, 131's and
  135's cases, but the intent's outcome doesn't ask for it, so it is out of scope unless you add
  it.
- **The verifier.** It gets the same "the gate is the script's, nothing in the background"
  lines as the reviewers (R9), because it can also run tests and so has the same failure. Say if
  you want it limited to the `reviewer-*` agents.
