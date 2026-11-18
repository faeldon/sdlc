
Resolved:

- **Which closes the gap at least cost?** Two of the options:
  - `sonnet` for the scaled reviewers at the light depth. 124's ui and ux reviewers already ran there on haiku (`ui_review()` joins them at either depth), so only the model can close that gap.
  - `behaviour` added to the light depth (125). The landing runs it on every rebase anyway.
  - A third round was rejected because those rounds passed rather than ran out. Choosing reviewers by what the diff touches was rejected because it needs a new path list a host must keep.
- **What counts as "the same error"?** The same `(role, change)` the verifier kept in two rounds in a row of one run, and nothing else. R4 makes reviewers repeat an undone change word for word so the match holds. Comparing red gates was rejected: a host's gate output can't be parsed into test names, and `GATE_FIXES` already caps red gates.
- **Who says a requirement can't be tested?** The builder, with `- UNTESTABLE:` in its report. The run ends rework after that round and must ESCALATE, so a wrong claim can only cost an escalation.
- **Should the early escalation name a next step?** Yes, under the existing `## Reconsider the approach` section, in the approver's words (R7). No new section or file.

Left for you:

- **Is today's evidence enough to change a default?** If yes, R1 and R2 stand as written. Tier 1 light runs then cost about one more agent run a round, and their reviews cost more per run because they run on sonnet instead of haiku. If no, drop R1 and R2: the change ships the early stop and the retro's landing-catch count (R8), and a later change sets the defaults from a window of data. R6 then records why the defaults are kept.
- **Does 129's miss call for `test` at the Tier 1 light depth?** That turns on 129's tier, which R6's table records. If it was a Tier 1, adding `test` there is a separate choice: it costs another run per light round, and with no numbered requirements the reviewer reads tests against the intent's Approach alone.
