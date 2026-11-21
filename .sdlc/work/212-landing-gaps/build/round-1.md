Both gaps are closed. The read-only list now refuses ugrep's ways of following links, and a new train test pins a readiness refusal's cause: changing it to `review` fails the test. I also refused a handful of ugrep options beyond what the intent asked for, because one of them runs programs; that's raised below as a default for you to confirm. The work is uncommitted, and I wrote no `plan.md` since this Tier 1 change touches two files.

**What ugrep actually does** (tested against the ugrep 7.8.4 this machine has):
- It follows links in three ways: `-R`/`--dereference-recursive`, `-S`/`--dereference-files` (plus an undocumented `--dereference`), and `-d`/`--directories=dereference-recurse`. That last one is the sibling the intent's open question guessed at. The old list caught only the short flags and `--dereference`.
- The intent says ugrep accepts `--deref…` prefixes. It doesn't: it rejects `--deref`, `--der` and `--dereference-f`. Prefixes are GNU grep's habit, so the prefix rule now covers both long names anyway.
- It has a worse hole than links: `grep --filter='txt:touch ran' -q keep a.txt` ran `touch` here, and the old list let it through, because single quotes hide the command from the shell-character check.

**Changes**
- **Link-following (`landing.py`):** the list now refuses any prefix of `--dereference-files` (3+ characters after `--`, as for `--dereference-recursive`), with or without `=value`. It also refuses any option word holding `dereference-recurse`, and that text as a word of its own, which covers `-d dereference-recurse` and bundled forms like `-rd`.
- **Program-running options:** it also refuses `--filter`, `--pager`, `--view`, `--save-config`, `--config` and `---FILE`. These run a program, write a file, or read options from a file that may be outside the checkout.
- **Readiness test:** `test_a_train_names_a_readiness_refusal_as_its_cause` begins a train over one ready change, deletes its `decision.md`, and asserts the train names it for ejection with cause `refusal`. The existing refusal test only ever reached the earlier failed-step path.

**Tests added (`tests/test_train.py`)**
- 14 new refusal cases: the seven link-following forms, and the six run/write/config options with `--config` in two forms.
- 4 new pass cases, so nothing harmless is refused: `-d recurse`, `--directories=recurse`, `--no-dereference`, `--no-config`.
- All 14 refusals failed before the change; the readiness test passes, and fails under the mutation.

**Tests run:** the read-only and readiness tests (73 passed), all of `test_train.py` and `test_modules.py` (208 passed, 1 skipped), and `test_no_agent_but_the_builder_runs_checks` (1 passed). Ruff check and format are clean. Nothing was left in `notes.md`.

- DECISION: [default] Also refuse ugrep's `--filter`, `--pager`, `--view`, `--save-config`, `--config` and `---FILE` in an unattended check? Going ahead with refusing them unless told otherwise.
  - OPTION: refuse them — closes a hole where a single-quoted `--filter` runs any program; only makes the list stricter, as the constraint allows; slightly wider than the intent
  - OPTION: links only, as the intent says — the narrowest change; `grep --filter='*:…'` keeps running programs on a train when the host's grep is ugrep
  - WHY: `--filter` ran `touch` in a test here, and a check that runs a program is worse than one that reads through a link
- DECISION: [default] Refuse the bare word `dereference-recurse` even as a grep pattern? Going ahead with refusing it unless told otherwise.
  - OPTION: refuse it anywhere — covers `-d dereference-recurse` and bundled `-rd` without tracking which flag takes the next word; a check that greps for that exact text needs the person
  - OPTION: refuse it only right after `-d` — fewer false refusals; misses bundled forms unless the code parses short-option bundles
  - WHY: stricter and simpler, and a check grepping for that literal is rare

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_train.py -k "read_only_command or readiness_refusal"   (before the code change)
14 failed, 59 passed, 104 deselected in 1.73s
exit: 1

$ uv run --group dev pytest -q tests/test_train.py -k "read_only_command or readiness_refusal"
73 passed, 104 deselected in 0.69s
exit: 0

$ uv run --group dev pytest -q tests/test_train.py -k "readiness_refusal"   (with `ejecting(name, ready_["refusal"], "review")` at landing.py:2110, then restored)
E       assert ('review' == 'refusal'
1 failed, 176 deselected in 0.59s
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_train.py tests/test_modules.py
208 passed, 1 skipped in 84.70s (0:01:24)
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py -k "builder_runs_checks"
1 passed, 450 deselected in 0.16s
exit: 0

$ uv run --group dev ruff check plugins/factory/scripts/landing.py tests/test_train.py && uv run --group dev ruff format --check plugins/factory/scripts/landing.py tests/test_train.py
All checks passed!
2 files already formatted
exit: 0

$ ARGV0=ugrep "${CLAUDE_CODE_EXECPATH:-$HOME/.local/bin/claude}" --filter='txt:touch ran' -q keep a.txt; echo "exit $?"; ls
exit 1
a.txt
ran
exit: 0
