# Decisions

- [x] D1 (builder round 1, default): When the person declines the paid run at landing, the skill runs `--skip "declined at landing"` with its own fixed words, not the person's. Going ahead with that unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: fixed words in the skill — keeps the rule that a person's words never go on a command line (`test_the_land_skill_passes_a_fixs_id_never_its_words`); the note doesn't say why the person declined
  - OPTION: the person's own words on `--skip` — the note says their reason; a quote or `$(` in it breaks or runs on the command line
  - OPTION: a ticked `(person, skip)` line in `decisions.md`, with `--skip R<n>` — their words without that risk; a new ledger line kind for the ledger reader to handle
  - WHY: R16 says "their reason", but the harness prompt they decline carries no words, and the repo's rule keeps a person's words off command lines
- [x] D2 (builder round 1, default): In a full run, a case with 2 environment runs and 1 failed run counts as `passed`. That follows R7's rule literally (it fails on two or more failures that aren't the sandbox's), and the one failure is still shown in its verdict. Going ahead unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: passed, failure shown — R7 as written; a case can pass with no clean run
  - OPTION: failed when no run counts — never passes on a single failed run; adds a rule R7 doesn't state
  - WHY: R7 names this test case without giving its result, so I applied its rule as written
- [x] D3 (builder round 1, default): When several cases fail in one run, each rerun's ceiling is the $5 cap minus everything spent so far, reruns included, not just minus the first run's cost. Going ahead unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: cap minus all spent — the whole call stays under $5, as the constraints require
  - OPTION: cap minus the first run only — R4's wording; several reruns together could go past $5
  - WHY: the intent's constraint that the rerun stays "under its cap"
- [x] D4 (approver round 1, look): Before the paid run, check that `checks.md`'s phrases (`reruns alone, once`, ``is `environment`: never rerun``) still sit on one line each in `docs/CONTRIBUTING.md`. The behaviour reviewer saw lines 115–120 wrap in the middle of these phrases and couldn't confirm the greps match. The builder's run of the check exited 0. Ship reruns it. → decided: seen
- [x] D5 (approver round 1, look): The paid acceptance run `sdlc.py run-cases 156` (≤ $5) hasn't been run by anyone, and no automated test covers it. The rerun, keeping traces and removing workspaces against the real `claude plugin eval` are proved only with a faked `subprocess.run`. → decided: seen
