I've made `is_read()` stop treating two kinds of command as reads, since both can write: `file` with `-C`, and git's `--ext-diff` and `--textconv`. The gate is green, with 2336 tests passed and 13 skipped. Nothing is committed.

This change is Tier 1, so I skipped the `plan.md` the prompt asked for. The builder rules give a Tier 1 change a plan only when its Approach touches more than a couple of files, and this one touches two (`factory.py` and `tests/test_factory.py`).

**What I built** (one slice, test first):
- **Red:** I added rows to the existing `READS` / `NON_READS` tables in `tests/test_factory.py` and ran the test. It failed because every new writer row passed as a read.
- **Green, `file`:** `file` is off the plain-read list and has its own condition, the way `sort` does. Any `-C` in a group of short flags (`-C`, `-bC`) or any `--co…` (`--compile` and its shortened forms) is refused. `file x` and `file -b -m magic x` are still reads.
- **Green, git:** a new `GIT_RUNS` table in `_git_reads()` refuses `--ext-diff` and `--textconv` on any git read command, including shortened forms down to `--ext` and `--textc`. The cut-off is at `--textc` so that `--text`, which only reads, still passes. `--no-ext-diff`, `--no-textconv` and `--exit-code` still pass too.
- No acceptance checks were needed: the table test proves every outcome.

**Tests added:** five reads that must still pass (`file x`, `file -b -m magic x`, `git diff`, `git diff --text --no-ext-diff --no-textconv`, `git log -p --exit-code`). Ten non-reads that must be refused: four `file -C` spellings, the git flags on `diff`, `log`, `show`, `blame` and `cat-file`, and `git -c diff.external=./x diff`. Every existing `READS` row still passes.

**The intent's open question, about git's `-c`:** it was already refused. `_git_reads()` turns down any option before the subcommand other than `-C` and `--no-pager`, so `git -c diff.external=… diff` was never a read. The new `NON_READS` row pins that, so it isn't a decision for you.

**Not covered:** a `diff.external` setting or textconv driver in the repo's git config still runs on a plain `git diff`. Only the command line is checked, and the intent asks for nothing more.

No other code keeps a copy of this parsing, and `plugins/factory/README.md` describes `is_read()` only in general terms, so neither needed an edit. Nothing went into `notes.md`, and I raised no decisions.

## Evidence

$ uv run --group dev pytest -q tests/test_factory.py -k "read_is_only"   (before the fix)
E       AssertionError: ['file -C -m magic', 'file -bC -m magic', 'file --compile -m magic', 'file --comp -m magic', 'git diff --ext-diff', 'git log -p --ext', ...]
1 failed, 252 deselected in 0.72s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k "read"
25 passed, 228 deselected in 10.06s
exit: 0

$ ./check.sh
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q -n auto
2336 passed, 13 skipped in 125.15s (0:02:05)
exit: 0
