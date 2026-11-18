VERDICT: PASS

The change does what the intent asks. I found no Critical or Required findings.

Checked against the spec:
- **`--show-signature` is refused.** `GIT_RUNS` carries the full name. I probed git 2.56: `git log` and `git diff` reject every shorter spelling (`--show-sig`, `--show-si`), and `git show` rejects the flag outright. So the full-length match is correct, and the "any abbreviation git takes" outcome holds in practice.
- **`%G` placeholders are refused** under `--format=` and `--pretty=`, including `format:`/`tformat:` values. Probes confirmed `--format=%G?`, `-s --format=%G?` and `--pretty=tformat:%GK` all run gpg (they print a signature status). The check also refuses a `%G` value given as the next word.
- **Every existing READS row still passes.** The diff only adds rows. The one table test passes (268 in `tests/test_factory.py`), and ruff check and format-check are clean on both files.
- **The comment at the refusal table** now says what is covered and what isn't, which answers 126's nit F1.
- **Contract and context.** `AGENTS.md`, `REFERENCE.md`, `README.md` and the factory README don't list the refused git options, so none of them is now false. The code comment is the right home, and I see no `[context]` change.

## Notes

- Open question D1 (`log.showSignature=true` in a host's git config) is already raised as an unticked default in `decisions.md`, and I agree with leaving it uncovered. It can't be seen from the command, and the comment says so. I haven't raised it again.
- NIT: `tests/test_factory.py` (the `git log --format %G?` and `git log --pretty %GF` rows) and `plugins/factory/scripts/factory.py` (the next-word branch in `_git_reads()`): in git 2.56, `--format` without `=` is unrecognised, and `--pretty` without `=` takes no value. So the separate-word form never reaches gpg. The refusal is harmless over-refusal, and the branch can stay as cheap conservatism. Just don't describe it as a form git accepts.
- NIT: `factory.py`, the `GIT_RUNS` entry `("--show-signature", len("--show-signature"))`: the length is the whole name, so a plain equality check would read more simply. Optional.
- NIT: `factory.py`, `GIT_RUNS`: a literal `%%G` is also refused. That is a conservative over-refusal and costs only a mend. The comment already admits it in the intent; it could say so in code too. Optional.

## Tests and commands run

- `uv run --group dev pytest -q tests/test_factory.py`: 268 passed.
- `uv run --group dev ruff check` and `ruff format --check` on the two changed files: clean.
- Read-only git probes in a scratch repo under `/tmp` (deleted afterwards), covering the option forms listed above.

I did not run the full `./check.sh`. The builder's round-1 report says it passed with 2356 tests, and this diff only touches the factory and its test file.
