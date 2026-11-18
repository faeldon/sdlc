VERDICT: PASS

The change does what the intent's Approach says, and I found nothing to fix.

## Notes
- **End-to-end path (-57):** `_passes_report()` at `scripts/sdlc.py:8334` ends `passes.ui.why` with `take them with factory.py shots <ident> --round 1 --role ui`. This applies when the factory is enabled and a UI pass has no shots. `skills/ship/ui.md` says the same and states that ship never runs it. `tests/test_preflight.py` has a test for the line, and it passes.
- **Tests:** I ran `test_preflight.py`, `test_factory.py` and `test_hand_gate.py`: 448 passed. They cover the -72 `terms.local` placeholder and the other nits that carry tests. The full gate record, `build/round-1.gate.md`, is green.
- **Check 1, "AGENTS.md has no line past 100 columns":** I expect it to pass. Measured in characters, no line is over 100. A byte-counting `awk` flagged line 12 only because it holds multi-byte characters.
- **Check 2, wrapped supersedes sentences and README paragraph:** I expect it to pass. Each phrase sits on a single line, at 98, 94 and 99 characters.
- **Check 3, ship's pass files wording:** I expect it to pass. I read each phrase in the files and `security.md` has no `review.sensitive`:
  - `behaviour.md:4` has "not a factory run, whose own reviewers ran".
  - `security.md` has "a deep" and "isn't a factory run, whose own reviewers ran".
  - `ui.md` has "isn't a factory run, whose own reviewers ran".
  - `ui.md:32` has `factory.py shots NNN --round 1 --role ui`.
- I did not run any of the checks, and I did not re-run the gate.

## Evidence
$ git diff --stat $(git merge-base HEAD main) | tail -20
12 files changed, 205 insertions(+), 79 deletions(-)
exit: 0

$ grep -n "factory.py shots" scripts/sdlc.py skills/ship/ui.md
scripts/sdlc.py:8334 why = f"{why}: take them with factory.py shots {ident} --round 1 --role ui"
skills/ship/ui.md:32 enabled, the why names the command that takes them, `factory.py shots NNN --round 1 --role ui`:
exit: 0

$ python3 -c "...len(l)>100 over AGENTS.md..."
(no output)
exit: 0

$ grep -c "review.sensitive" skills/ship/security.md
0
exit: 1

$ python3 -c "...lines holding each phrase, with their lengths..."
reviewer-code.md 1 [98]
reviewer-ux.md 1 [94]
README.md 1 [99]
exit: 0

$ uv run --group dev pytest -q tests/test_preflight.py tests/test_factory.py tests/test_hand_gate.py -n auto | tail -4
448 passed in 104.73s (0:01:44)
exit: 0

$ sed -n 25,40p skills/ship/ui.md
(read; shows the "With no shots" paragraph naming `factory.py shots NNN --round 1 --role ui`)
exit: 0

$ grep -n "factory run, whose own\|a deep" skills/ship/*.md
(read; shows behaviour.md:4, security.md:3-4 and ui.md:5)
exit: 0

$ awk 'length>100{print FILENAME": "FNR}' AGENTS.md
AGENTS.md: 12
exit: 0

$ grep -n "supersedes D<n>" plugins/factory/agents/reviewer-*.md | awk 'length>140'
(reviewer-code.md:105, reviewer-security.md:87 and reviewer-ui.md:79 were listed; the last two are untouched files)
exit: 0

$ cd .sdlc/work/150-pay-down-batch-nits && ls . build reviews; cat intent.md; cat checks.md | head -80; tail -20 build/round-1.gate.md
(read; `reviews` doesn't exist yet. The gate record ends "Validation passed".)
exit: 1
