DECISION: ESCALATE

**Why.** The build covers R1–R19 by all three reviewers' account. Round 1 passed in every role, and the gate is green: 2890 passed, 28 skipped. No Critical or High finding is open. The decision is ESCALATE because all three of the builder's open defaults need the person. D1 differs from R16's "their reason". D2 is a pass/fail rule that the spec states in two ways that point in opposite directions. D3 sets how much a run may spend.

**Open items**
- None. The last round was all `VERDICT: PASS`. The three NITs were left as notes: the ceiling rounding in `sdlc.py:3877` (code), D1's fixed words (code), and the chmod restore in `test_evals.py:523` (test).

**Decisions to confirm**
- ESCALATED: D1: R16 and the intent's second open question say `--skip` records the person's own reason. The build writes the fixed words "declined at landing" instead, to keep a person's words off a command line. Choosing between what the spec says and the repo's rule against command-line injection is a policy call that only the person can make. Its options are already in the ledger.
- ESCALATED: D2: The spec settles this in two ways that disagree. R7 says a single failed run "doesn't fail it", so the case passes. The Design's edge case says a case "failed the run that reached git" when its only other run is `environment`, so the case fails. The rule also decides how lenient release's measure of the skills is. That is policy, so it is the person's call. Its options are already in the ledger.
- ESCALATED: D3: This sets how much one approved paid call may spend when several cases rerun. R4's wording ("the cap less what the first run cost") could take several reruns past $5. The builder's reading keeps the whole call under $5. A default about cost is never the approver's to settle. Its options are already in the ledger.

**Every other reason I escalate for**
- ESCALATED: look: Before the paid run, check that `checks.md`'s phrases (`reruns alone, once`, ``is `environment`: never rerun``) still sit on one line each in `docs/CONTRIBUTING.md`. The behaviour reviewer saw lines 115–120 wrap in the middle of these phrases and couldn't confirm the greps match. The builder's run of the check exited 0. Ship reruns it.
- ESCALATED: look: The paid acceptance run `sdlc.py run-cases 156` (≤ $5) hasn't been run by anyone, and no automated test covers it. The rerun, keeping traces and removing workspaces against the real `claude plugin eval` are proved only with a faked `subprocess.run`.

**For the person at ship**
1. `_remove_workspace()` and `_workspace_of()` in `scripts/sdlc.py`. They are the only new code that deletes outside the repo. They make every folder writable, then run `rmtree`. Confirm the guard only allows an `e-*` folder sitting directly in the resolved temp dir or `/tmp`, and that it never follows a link.
2. The rerun ceiling in `cmd_run_cases()` (D3).
3. Step 1 of `plugins/factory/skills/land/SKILL.md`, including the decline path (D1).
4. The edit to `AGENTS.md` *Writes before a WAIT*, which now lists five exceptions.

- IMPACT: none — the cases, `run-cases`, `factory.py cases` and `full_history` act only in this plugin's own repo, since hosts have no cases. Nothing a host receives behaves differently.

**Undone items**
- UNDONE: 26 `e-*` workspaces from earlier case runs sit in `/private/tmp` (made before runs removed their own); a one-off `run-cases --prune` or a line in CONTRIBUTING could clear them, behind the same `_workspace_of()` guard → seed: Clear the eval workspaces left in /tmp by earlier case runs
