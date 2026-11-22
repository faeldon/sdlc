VERDICT: PASS

The end-to-end preview path does what the spec says. No `checks.md` exists for this change, so there were no acceptance checks to read.

## Notes
- **R1:** `status --json` printed `direction` with goals G7–G9, milestones M13, M20–M23 (each with `serves` and `seeds`) and empty `problems`. The milestones' `seeds` are all empty, because the register has no open seeds those milestones name. Struck-item and title-to-id resolution are covered by the test file I ran.
- **R4:** With no `--goal`, the preview proposed `theme:board` (source `register`, 1 candidate). That fits R4, because no open milestone has a candidate in scope. I did not check R4's ordering rules beyond that case.
- **R2:** `--goal M99` was refused with "M99 isn't an open goal or milestone in the direction doc".
- **R5:** The preview's `question` begins `Run autopilot toward theme:board "…" (register) until …`, and `shown` opens with a `Goal:` block. The block gives the goal's source and a line saying another goal is a new `--preview`.
- **Not run:** I did not run `--begin`, because the auto-mode classifier denied it: it writes run state. R6, R9, R11 and R12 were checked only through `tests/test_autopilot.py`, which passed (71 tests).
- **Gate:** `round-1.gate.md` shows `GATE: PASS` with exit 0 for `./check.sh`.
- **Working tree:** it still shows the same 10 modified files plus the untracked change folder; my commands changed nothing.

## Evidence
$ cat .sdlc/work/231-autopilot-goals/build/round-1.gate.md | head/tail
GATE: PASS … Command: ./check.sh … Exit: 0 … ✔ Validation passed
exit: 0

$ uv run --quiet --script scripts/sdlc.py status --json | python3 -c "…print direction…"
direction printed with goals G7–G9, milestones M13, M20–M23 and problems []
exit: 0

$ uv run --group dev pytest tests/test_autopilot.py -q -n 4
71 passed in 54.21s
exit: 0

$ uv run --quiet --script plugins/factory/scripts/factory.py autopilot --preview --usd 5 --hours 1
goal: source register, arg theme:board, count 1; question and shown both name the goal; warnings []
exit: 0

$ uv run --quiet --script plugins/factory/scripts/factory.py autopilot --preview --usd 5 --hours 1 --goal M99
refusals: ["M99 isn't an open goal or milestone in the direction doc"]
exit: 0

$ git status --short | wc -l
11
exit: 0

(A further `--preview … ; --begin …` command was denied by the harness and did not run.)
