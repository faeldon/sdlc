VERDICT: PASS

No Critical or Required findings. The change does what the intent asks, and the new rows in both tables behave as written.

## Notes

I checked each requirement against the code and the tests:

- **`file -C`:** `file` leaves `READS` and gets its own condition beside `sort`'s. Any short-flag cluster containing `C` and any `--co…` is refused. `file x`, `file -b -m magic x` and `file --version` are still reads.
- **git `--ext-diff` and `--textconv`:** `GIT_RUNS` matches by unambiguous prefix. The cut-offs are `--ext` and `--textc`, so `--text` stays a read. `--no-ext-diff`, `--no-textconv` and `--exit-code` pass. `git grep --textconv`, `git -C x show --textc`, `git cat-file --textconv` and `git diff --ext-diff` are refused. `--no-ext-diff --ext-diff` is refused because the last flag wins.
- **Intent's open question (git `-c`):** already refused. `_git_reads()` allows only `-C` and `--no-pager` before the subcommand, so `git -c diff.external=… diff` was never a read. The new row pins it.
- **Bypasses I tried:** `GIT_EXTERNAL_DIFF=./x git diff` is refused by the assignment check. `git -P log` and `git --paginate log` are refused. `git -- --ext-diff` passes only because `--` makes it a path, which is correct.

Tests run: I ran every row of `READS` (14) and `NON_READS` (35) through `is_read()` by importing the module with bytecode writing off. None were misjudged. I did not rerun pytest, since it writes caches. I did not verify the builder's gate record, which is in `build/round-1.md`.

What is done well: the abbreviation table is the right way to handle git's prefix matching, and the new rows cover both the spelling variants and the flags that must still read. The factory README's description ("a short allowlist of programs that change nothing") is still true, so it needed no edit.

- NIT: plugins/factory/scripts/factory.py:208: the comment says git's options that "run an external program" are refused, but `git log --show-signature` and `git show --format=%G?` run `gpg`, which the rule as written lets through. The table is narrower than its comment. Either reword the comment to name the two options, or add the signature cases.
- NIT: plugins/factory/scripts/factory.py:1204: the `--co` prefix also refuses `file --cont` (`--continue`), which is harmless and within the strict rule the docstring describes.
- Not covered, and disclosed by the builder: a `diff.external` setting or a textconv driver in the repo's git config still runs on a plain `git diff`, since only the command line is judged. The intent asks only for the command line, so this is not a finding.

DECISION: [default] Should `--show-signature` and `%G…` (which run `gpg` from a read) be refused in this change? Options: (a) refuse them now, with rows in `NON_READS`; (b) leave them and file a follow-up idea. I'd assume (b): the intent names two options, and gpg's writes go to `~/.gnupg`, outside the change's folder. Raise it as its own entry if you want them covered.
