I built all 19 requirements of 114 and the gate passes: `./check.sh` exits 0 with 2319 passed and 13 skipped. Nothing is committed and HEAD hasn't moved. I departed from the spec's wording in two places, both recorded in `plan.md` and described below.

**The evidence (R14).** Before writing code I put an `## Evidence` section in `notes.md`. It tallies every change closed since 103: trailers, review lines per round, and what the verifier kept and dropped. It also lists the bugs that have `Introduced by:`. No row contradicts a choice in the spec's *Design*:
- Both escapes since 103 (bugs 85 and 90) were in factory-built changes.
- The code reviewer already raises context findings without saying so (116, first round).
- Ten pre-existing findings reached the register only as `[idea]` seeds.
- The verifier has dropped nothing since 103.

**What was built, one slice at a time, test first:**
1. **The guide's checklist (R1–R3):** a `## Review dimensions` section with all 16 keys, and a Pass 1 rule that each requirement names its test. I re-recorded `.sdlc/setup.json`, and `drift` reports nothing.
2. **Ship's trailer counts only ship's own findings (R9):** `sdlc.py` has `AGENT_ROLES` and `ship_findings()`. The trailer and `findings`' counts leave the agents' findings out and add `agents=`.
3. **A finding's pass and the agents' nits (R5, R6):** `finding_pass()` reads a `[pass]` tag, and a new regex reads `- NIT:` lines. Nits never reach the verify prompt and are never reworked. A tagged change is still matched to the verifier's answer, and judged pre-existing, by its file path.
4. **`carry` writes `findings.md` (R7, R8, R13):** one section per distinct finding, with `By:` naming the role. A rerun replaces only the agents' sections and leaves the file byte-identical when nothing is new. The file starts from `FINDINGS_HEAD`, a copy of the template's note, which now says both ship and the factory write it.
5. **The landing (R10):** it commits that file and still writes no `Sdlc-Findings`.
6. **Bugs at landing (R17, R18):** the approver may propose `→ bug: <severity>: <paths>: <title>` for a `pre-existing:` item.
   - `land-check` checks the severity against the words `sdlc.py bugs` returns.
   - A bad word, missing paths, or a bug on any other item leaves the change for `/sdlc:ship`.
   - On yes, the landing files a `[bug]` entry with `Severity:` and `Paths:`, ticks the item `→ bug: <id>`, and a rerun files nothing twice.
7. **Ship by hand (R11, R19):** ship's refusal now names seed, bug and dropped, and `undone.md` offers the bug option.
8. **Retro (R12):** `review_sources` and `review_unknown` count findings per source, and the report prints one line per source.
9. **Prompts and docs (R4, R16):** the code reviewer gets a fifth pass, Context, and the code, security and test reviewers list their nits as `- NIT:` lines. I updated `REFERENCE.md`, the factory README, AGENTS.md's *Ship*, `.sdlc/REVIEW.md` (a new failure class) and the land skill.

**Tests added:** every test the spec names, plus `test_carry_with_no_complete_round_writes_the_note_alone`. Each one failed first, except R10's. Once `carry` wrote the file, the existing landing code already committed it with no trailer, so that test guards against a regression rather than driving new code. I updated existing tests for the trailer's new `agents=0`, the `By:` problem message, a missing file now starting from the template's note, and retro's new keys.

**Acceptance checks:** `checks.md` holds R3's, R4's, R11's and R19's, and `sdlc.py accept 114` passes all four.

**Departures from the spec, in `plan.md`:**
- **R11's rule is in `skills/ship/factory.md`, not `SKILL.md`.** The rule to keep the agents' sections as written lives in a new Step 3 there. `test_ship_s_skill_stays_under_its_budget` caps `SKILL.md` at 475 lines (it was at 482) and says rules only some runs need belong in a branch file. Agents' sections exist only on factory-built changes, which is exactly when `factory.md` is read. `SKILL.md` keeps the narrowed "never raise again one the person answered" rule.
- **R6's regex is `FINDING_NIT_RE`, not `NIT_RE`,** because `NIT_RE` already names the register's `[nit]` heading.

**Left in `notes.md`:** six unticked `- [ ] gap:` items for R15: security, end-to-end, ui and ux in ship; the factory's nits not weighed or filed; and the landing rounds not yet in `findings.md`. `preflight 114` lists all six.

**Not run:** the paid `/sdlc-factory:eval`, before and after the reviewer prompt edits, and the manual scratch factory run the spec lists. Both are your call.

No decisions raised this round.

## Evidence

$ ./check.sh > /tmp/t114/gate.log 2>&1; echo "exit: $?"; grep -nE '[0-9]+ passed|All checks|already formatted' /tmp/t114/gate.log
exit: 0
1:All checks passed!
2:252 files already formatted
39:2319 passed, 13 skipped in 64.34s (0:01:04)
✔ Validation passed
exit: 0

$ uv run --quiet --script scripts/sdlc.py accept 114
True [('R3: ', True), ('R4: ', True), ('R11:', True), ('R19:', True)]
exit: 0

$ uv run --quiet --script scripts/sdlc.py drift
{'breaking': 0, 'refresh': 0, 'report': 0, ...}
exit: 0

$ uv run --quiet --script scripts/sdlc.py preflight 114
73 gap: security: ship checks only secrets, plus the fresh revi
74 gap: end-to-end: ship never runs the spec's path end to end,
75 gap: ui: ship has no UI review of a change that renders a pa
76 gap: ux: ship has no UX review, where the factory runs `revi
77 gap: nits: the factory records its agents' `- NIT:` lines in
78 gap: landing rounds: `findings.md` holds only the build roun
exit: 0

$ uv run --group dev pytest -q tests/test_land.py -k 'as_a_bug or approved_bug'   (before the code)
2 failed, 50 deselected in 0.73s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k 'carry'   (before the code)
3 failed, 2 passed, 242 deselected in 1.91s
exit: 1

$ uv run --group dev pytest -q tests/test_findings.py   (before the code)
5 failed, 38 passed in 2.06s
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py -k review_sources   (before the code)
E       KeyError: 'review_sources'
1 failed, 120 deselected in 1.56s
exit: 1

$ uv run --group dev pytest -q tests/test_sdlc.py -k every_disposition   (before the code)
1 failed, 235 deselected in 0.22s
exit: 1

$ uv run --group dev pytest -q tests/test_defaults.py -k 'dimension or findings_head'   (before the code)
2 failed, 119 deselected in 0.32s
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -k agents_findings
1 passed, 49 deselected in 2.62s
exit: 0
