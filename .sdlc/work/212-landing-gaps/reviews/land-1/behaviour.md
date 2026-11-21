VERDICT: PASS

The change does what the intent asks. The read-only list now refuses `grep -r --dereference-files keep .` and its prefixes. A new train test pins the `refusal` cause.

## Notes
- **End-to-end path.** The intent names two outcomes:
  - `read_only_command` now refuses `--dereference-files` and any prefix of it with three or more characters after `--`. It also refuses ugrep's `dereference-recurse` action, whether it comes through `-d`, `--directories=` or a glued form.
  - `test_a_train_names_a_readiness_refusal_as_its_cause` removes the change's `decision.md`, runs `cmd_train`, and asserts `cause == "refusal"` with nothing committed.
- **Constraint: the list only grows stricter.** The diff adds only refusals. Existing passes such as `--directories=skip` and `--de` stay in `READ_ONLY_PASSES`.
- **Constraint: no change to what a refusal ejects.** The diff leaves the ejection code alone; only the test is new.
- **Open question from the intent.** `--dereference-recursive` was already covered, and the change adds `--dereference-files`. The change also refuses ugrep's `--filter`, `--pager`, `--view`, `--save-config`, `--config` and `---FILE`, which the intent's outcome doesn't list.
- **Gate.** `build/land-1.gate.md` is `GATE: PASS` (`./check.sh`, exit 0).
- **Mutation check.** I did not run the mutation of `refusal` to `review` that the outcome describes. The new test asserts `cause == "refusal"` directly, so it would fail under that mutation.
- **`checks.md`.** There is none for this Tier 1 change.

## Evidence
$ git diff c1b9b0b3220258e4c3701c231fd502f2790036a0...HEAD --stat
(25 files changed, 559 insertions, 8 deletions; code in `plugins/factory/scripts/landing.py` and `tests/test_train.py`)
exit: 0

$ git diff c1b9b0b3220258e4c3701c231fd502f2790036a0...HEAD -- plugins tests
(the `landing.py` grep checks and the new train and read-only tests, as described above)
exit: 0

$ head -12 .sdlc/work/212-landing-gaps/build/land-1.gate.md
GATE: PASS
Verdict: PASS
Command: ./check.sh
Exit: 0
exit: 0

$ uv run --group dev pytest -q tests/test_train.py -k "readiness_refusal or read_only"
74 passed, 103 deselected in 56.93s
exit: 0
