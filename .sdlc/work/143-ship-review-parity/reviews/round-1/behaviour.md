VERDICT: PASS

The path runs as the spec says. `sdlc.py preflight 143` reports `passes.behaviour.applies: true` and the other two false, each with its reason. It lists `behaviour.md` in `branches`, and `preflight --question` still prints the unchanged question. The change's gate record, `build/round-1.gate.md`, is green. I did not run the gate again.

## Notes
- **checks.md:** `.sdlc/work/143-ship-review-parity/checks.md` does not exist, so there is nothing to read or run.
- **Security:** it does not apply because the diff touches no sensitive path (R2).
- **UI:** it does not apply because the diff touches no `[ui]` path (R4).
- **Question wording:** the clauses for passes that ran or were skipped need a `findings.md` note, and none exists yet. I did not exercise those clauses by hand. I judged them from `_passes_clauses()` and from the passing `test_the_question_names_the_passes`.
- **Eval case:** `evals/ship-behaviour/` and its `evals/fixtures/built-tier2/` fixture are present. `test_evals.py` builds the fixture and runs `check --strict` on it. I did not run the paid case.
- **Decision D1:** it is a builder default, still open, and not blocking.

## Evidence
$ cat .sdlc/work/143-ship-review-parity/intent.md; tail of build/round-1.gate.md; cat checks.md; cat decisions.md; git log; git diff --stat
(tail) GATE: PASS, ./check.sh exit 0; checks.md missing: No such file or directory
exit: 0

$ git status --short; grep -n requirement lines in spec.md; sdlc.py preflight --help
(tail) new files: agents/security.md ui.md ux.md, skills/ship/{behaviour,security,ui}.md, evals/ship-behaviour/, evals/fixtures/built-tier2/
exit: 0

$ git status --short | tail -n +20; ls skills/ship agents evals; sdlc.py preflight 143 (passes, branches as JSON); sdlc.py preflight 143 --question | tail -15; head of build/round-1.gate.md
(tail) passes.security false, behaviour true, ui false; branches ["undone.md","recover.md","behaviour.md","cases.md"]; question "Commit this, with how to recover it shown, and .sdlc/work/143-ship-review-parity/ stamped shipped, then update its issue? (yes / edit the message)"; head of gate record: GATE: PASS
exit: 0

$ sed -n 86,98p spec.md; grep -n "behaviour\|Behaviour" scripts/sdlc.py
(tail) R14 and R15 text; BEHAVIOUR_RE, SHIP_PASSES and passes code at lines 1195–1248 and 7995–8086
exit: 0

$ sed -n 8040,8082p scripts/sdlc.py; sdlc.py check 143 --strict; ls evals/ship-behaviour; head -40 skills/ship/behaviour.md
(tail) `_passes_clauses()` and `SHIP_BRANCHES` shown; the `check` call errored: "unrecognized arguments: 143" (my invocation, not the change); eval case files and behaviour.md read
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_preflight.py tests/test_findings.py tests/test_skills.py tests/test_evals.py tests/test_hand_gate.py tests/test_retro.py; sdlc.py check --strict
(tail) 719 passed in 47.29s; "Problems: 0"
exit: 0
