I built change 132: `is_read()` no longer counts a git command that runs gpg as a read. The full gate passed: `./check.sh` exited 0, with 2356 tests passing and 13 skipped. The work is uncommitted, waiting for `/sdlc:ship`.

This is Tier 1 and touches two files, so I wrote no `plan.md`. Nothing went into `notes.md` and there is no `checks.md`.

**One slice: refuse git's signature options** (`plugins/factory/scripts/factory.py`)
- **`--show-signature`:** added to `GIT_RUNS` at its full length. Running git 2.56 here, `git log` and `git show` reject every shorter form (`--show-sig`, `--show-s`, `--show`, `--sho`), so the full name is the only spelling git accepts.
- **`%G` formats:** a new `GIT_FORMATS = ("--format", "--pretty")`. `_git_reads()` refuses either option when its value holds `%G`, whether after `=` or as the next word. git rejected `--form=` for both `log` and `shortlog`, so only the exact names need matching.
- **The comment at the refusal table** now says exactly what is covered: a diff driver, a textconv filter, and gpg through `--show-signature` or a `%G` format. It also says what isn't: settings in git config with no option on the command line, such as `log.showSignature` or `diff.<driver>.textconv`. `-c` before the subcommand is never a read. That answers 126's nit F1. I also reworded the `_git_reads()` docstring.

**Tests** (`tests/test_factory.py`): I added rows to the one table test. It failed first because all the new non-read rows still counted as reads, then passed.
- **New non-reads:** `git log --show-signature`, `git show --show-signature HEAD`, `git -C . log -1 --show-signature --oneline`, `git log --format=%G?`, `git log --pretty=format:'%h %GS'`, `git log --pretty=tformat:%GK`, `git show -s --format='%GG' HEAD`, `git shortlog --format=%GS`, `git log --format %G?`, `git log --pretty %GF`, and `git -c log.showSignature=true log`.
- **New reads:** `git log --format='%H %s'`, `git show HEAD`, and `git log --no-show-signature -1`. Every existing read row still passes.

**The intent's open questions:**
- **`-c log.showSignature=true`:** already refused, because any option before the subcommand other than `-C` and `--no-pager` is not a read. It's now a table row.
- **`log.showSignature=true` in a host's own git config:** a command can't show it, so it isn't covered. The table comment now says so, and I raised it as a default decision below.
- **Is `%G` the only family that runs gpg?** Among pretty-format placeholders, yes: `%G?`, `%GS`, `%GK`, `%GF`, `%GP`, `%GT` and `%GG` all start with `%G`. The check matches the `%G` prefix, so it covers them all. A literal `%%G` is also refused, which only costs a mend.

During the build, a scripted edit of mine emptied `tests/test_factory.py`. I restored it from `HEAD` before making the edit again, and the diff holds only the intended rows.

- DECISION: [default] Leave a host's own git config (`log.showSignature=true`) uncovered by `is_read()`? Options: leave it uncovered and say so at the table; make every `git log`/`git show` without `--no-show-signature` a non-read. Going ahead with leaving it uncovered: the command can't show it, and the other option would turn every git log read into a mend.

## Evidence

$ git log -1 --oneline --show-sig
fatal: unrecognized argument: --show-sig

$ git log -1 --form='%G?'
fatal: unrecognized argument: --form=%G?

$ git shortlog --form='%GS' HEAD~2..HEAD
error: unknown option `--form=%GS'

$ uv run --group dev pytest -q tests/test_factory.py::test_a_read_is_only_what_the_script_can_tell_changes_nothing
FAILED tests/test_factory.py::test_a_read_is_only_what_the_script_can_tell_changes_nothing
1 failed in 0.52s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py::test_a_read_is_only_what_the_script_can_tell_changes_nothing
1 passed in 0.06s
exit: 0

$ ./check.sh
2356 passed, 13 skipped in 110.65s (0:01:50)
✔ Validation passed
exit: 0
