VERDICT: CHANGES

- CHANGE: plugins/factory/scripts/factory.py:942: when the base branch can't be resolved, `start` reports no refusal and `build_question()` words the gate as "with no gate configured" and drops the `[review] sensitive` parenthesis. Nothing read the base's config, so that claim is unverified, and `fresh` returns `held` with no refusal, so the person is asked it. The spec's gate clause is "taken from what `start` already reads", and here it reads nothing. Fix: refuse like `cmd_land`'s "no base branch" when `base` is None, or leave the gate clause out and say the base is unknown.
- DECISION: [blocking] plugins/factory/skills/build/SKILL.md:231 ("the text before its parentheses as the question") cuts the dialog question short. The full question's first parenthesis is the gate's "(up to 2 fixes a round)", so the AskUserQuestion text stops at "...before any reviewer". The reviewers, rounds, UI clause, run budget, mode and "stage: test?" never reach the dialog, which the intent's "approved for its purpose" depends on. The rule is shared by every factory WAIT, so it predates this change, but Step 2 now says "ask `start`'s `question` literally". Options: (a) build's WAIT asks the whole question, with `test_skills.py` pinning it; (b) keep the rule, read as the answers' parenthesis at the end only, for all factory WAITs. Recommendation: (a), scoped to build, since spec, land, eval and review keep their wording and the decision is the person's.

## Notes

- Scope: Tier 1, so there is no spec.md; the Approach in intent.md is the contract. The gate record `build/round-1.gate.md` is GATE: PASS (2350 passed, `ruff`, `claude plugin validate` passed). I did not run the gate.
- Step 1 and Step 2 text: the Step 1 and Step 2 wording in SKILL.md matches the Outcome. Forms checked in memory: plain, spec draft, restart, upgraded, and the UI clause each render as the old templates did, word for word. The no-sensitive case drops the parenthesis; the no-gate case reads "with no gate configured".
- Real path: `start 125 --for build` in a scratch clone with `stage: build` and `main` present prints the question shown above, with `./check.sh`, the sensitive parenthesis and no UI clause (the base `[ui]` is not set in `main`'s config — `ui` shows defaults, `serve` set, but `paths` relevant only if all three). `start` refuses at the real `stage: shipped`, as it should.
- checks.md, read, not run. Check 1 (Step 1 opens with the change): expect PASS. Each phrase it greps is in SKILL.md's Step 1 paragraph, and the flattened text contains the four phrases. Check 2 (Step 2 asks the question, forms gone): expect PASS. `Ask \`start\`'s \`question\` literally, as printed; never word your own.` is on one line; `Send NNN-<slug> back`, `Write this spec and carry on NNN-<slug>` and `Leave out the parenthesis` are absent from SKILL.md and the rest of the repo.
- `decisions.md` D1–D5 are answered and settled; not raised again.
- The worktree has uncommitted landing-run files (`build/land-1.gate.md`, `reviews/land-1/`, `runs/reviewer-behaviour.sessions`, `runs/costs.jsonl`). I didn't write them.
- Not run: `tests/test_factory.py` (the gate's run covers it), and `checks.md`'s `sh` blocks.

## Evidence

$ git log --oneline -5 && git diff --stat e26da2f9880b866386029fe360eba7ef05013696...HEAD
  4ff2ea3 The factory's build gate shows what the change is for ...
  ...
  22 files changed, 687 insertions(+), 30 deletions(-)
exit: 0

$ Read .sdlc/work/125-build-gate-shows-the-change/spec.md
  File does not exist. (Tier 1: no spec; the Approach is the spec.)
exit: 1

$ Read .sdlc/work/125-build-gate-shows-the-change/intent.md
  (read; Approach at lines 81-86: "build_question(cfg, start, spec, restart) ... Step 2 to ask start's question literally")
exit: 0

$ Read .sdlc/work/125-build-gate-shows-the-change/checks.md
  (read; two `## ` sections: Step 1 opens with the change; Step 2 asks the script's question)
exit: 0

$ Read .sdlc/work/125-build-gate-shows-the-change/decisions.md
  (read; D1–D5 all [x] decided)
exit: 0

$ Read .sdlc/work/125-build-gate-shows-the-change/build/round-1.gate.md
  GATE: PASS ... 2350 passed, 13 skipped ... Validation passed
exit: 0

$ git diff e26da2f9880b866386029fe360eba7ef05013696...HEAD -- plugins/factory/scripts/factory.py plugins/factory/skills/build/SKILL.md tests/test_skills.py
  (diff shown: build_question(), cmd_start's question block at factory.py:940-943, SKILL.md Steps 1–2, test_skills.py)
exit: 0

$ sed -n 1,30p plugins/factory/scripts/factory.py; sed -n cmd_start...; grep -n 'def _base_check\|def _sensitive\|...' factory.py
  (header: stdlib only, `dependencies = []`; cmd_start as in the diff; _base_check reads base's config via git show)
exit: 0

$ git clone -q --no-hardlinks <worktree> /tmp/s125.Chp9/repo && sed -i '' 's/^stage: shipped/stage: build/' .sdlc/work/125-build-gate-shows-the-change/intent.md
  6:stage: build
exit: 0

$ python3 -I -B plugins/factory/scripts/factory.py start 125 --for build   (in scratch, base branch absent)
  base= None behind= None refusals= [] 
  Run the factory on 125-build-gate-shows-the-change: the builder plans and builds it, with no gate configured, code, security, test and behaviour review it in up to 3 rounds, ...
exit: 0

$ git branch main origin/main; python3 -I -B plugins/factory/scripts/factory.py start 125 --for build   (in scratch)
  base= main behind= 0 refusals= []
  Run the factory on 125-build-gate-shows-the-change: the builder plans and builds it, the base branch's gate ./check.sh runs on each build before any reviewer (up to 2 fixes a round), code, security, test and behaviour review it in up to 3 rounds (or code in up to 2 rounds when the diff touches no sensitive path), and, on a diff touching scripts/board.html, scripts/board.py, tests/fixtures/board/, the ui and ux reviewers, which start sh tests/fixtures/board/serve.sh {fixture} {port}, a verifier checks each round's changes, the approver decides, at most 32 agent runs, agents in auto, all left uncommitted at stage: test? (yes / change the reviewers or rounds / no)
exit: 0

$ python3 -I -B $S/forms.py <worktree>/plugins/factory/scripts/factory.py   (in scratch; loads factory.py by path)
  == plain, no gate, no sensitive  ... with no gate configured, code and test review it in up to 3 rounds ...
  == spec draft  ... Write this spec and run the factory on NNN-x: ... (yes / revise a requirement / change the reviewers or rounds / no)
  == restart  ... Send NNN-x back to the factory: decision.md kept as decision-1.md, ... in up to 2 more rounds ... approver decides again ...
  == upgraded  ... Write this spec and carry on NNN-x's factory run as Tier 2: ... builds round 2 ... at most 26 more agent runs ... (yes / revise a requirement / ...)
  == ui complete  ... on a diff touching a/, b, the ui and ux reviewers, which start sh s.sh ...
exit: 0

$ grep -rn -e "Leave out the parenthesis" -e "Send NNN-<slug> back" -e "Write this spec and run the factory on" -e "Write this spec and carry on" -e "text before its parentheses" --exclude-dir=.sdlc --exclude-dir=.git .
  (no hits in SKILL.md for the removed template text; hits only in factory.py's new wording, tests, and the shared "text before its parentheses" rule in every skill's WAIT, incl. build SKILL.md:231)
exit: 0

$ sed -n 99,106p plugins/factory/skills/build/SKILL.md; grep -n "parenthes\|land-check" plugins/factory/skills/land/SKILL.md
  (land SKILL.md:101 carries the same "text before its parentheses" rule)
exit: 0

$ git -C <scratch>/repo branch -D main; python3 -I -B plugins/factory/scripts/factory.py start 125 --for build
  base= None behind= None refusals= [] warnings= ["ui is read from the base branch's ..."]
  Run the factory on 125-build-gate-shows-the-change: the builder plans and builds it, with no gate configured, code, security, test and behaviour review it in up to 3 rounds, ...
exit: 0

$ grep -n 'if not base\|"base"\|base is None' plugins/factory/scripts/factory.py   (base None handling)
  442: if not base:  (_base_factory returns {})   ...  2079: if base is None: refuse "no base branch"
exit: 0

$ python3 -I -B plugins/factory/scripts/factory.py fresh 125   (in scratch, base absent)
  state= held base= None refusals= []
exit: 0

$ python3 -I -B -c "...print(d['question'].split('(')[0])" $S/start.json
  Run the factory on 125-build-gate-shows-the-change: the builder plans and builds it, the base branch's gate ./check.sh runs on each build before any reviewer 
exit: 0

$ git status --short   (in the worktree)
   M .sdlc/work/125-build-gate-shows-the-change/runs/costs.jsonl
  ?? .sdlc/work/125-build-gate-shows-the-change/build/land-1.gate.md
  ?? .sdlc/work/125-build-gate-shows-the-change/reviews/land-1/
exit: 0
