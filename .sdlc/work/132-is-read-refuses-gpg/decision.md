DECISION: ESCALATE

**Why.** The build does what the intent asks. `--show-signature` and any `%G` format value are now refused, every existing `READS` row still passes, and the comment at the refusal table now says what is covered and what isn't. The code reviewer passed it in round 1 and found only nits, and the gate passed (`./check.sh`, 2356 passed). It still has to go to you because D1 in `decisions.md` is unticked: the build relies on a default you haven't confirmed.

**Open items.** None. Round 1 had no Critical or High findings. The code reviewer's three nits are in `findings.md` as F1–F3, marked `minor`:
- F1 (code): `--format`/`--pretty` given as a separate word never reaches gpg in git 2.56, so the next-word branch and its two rows refuse more than they need to. That's harmless, but shouldn't be described as a form git accepts.
- F2 (code): the `GIT_RUNS` entry `len("--show-signature")` could be a plain equality check.
- F3 (code): a literal `%%G` is refused too, which only costs a mend. The code comment could say so.

**Decisions to confirm.**
- D1: a host's own git config (`log.showSignature=true`) is left uncovered by `is_read()`, and the table comment says so. The other option was to treat every `git log`/`git show` without `--no-show-signature` as a non-read. Both the builder and the code reviewer favour leaving it uncovered.

**For the person at ship.**
- Start with `_git_reads()` in `plugins/factory/scripts/factory.py` (around lines 1247–1272), where the new `GIT_FORMATS` check takes the value after `=` or as the next word.
- Then read the rewritten comment above `GIT_RUNS` (lines 208–213). That's where D1's choice is written down.
- Last, check the new rows in the one table test in `tests/test_factory.py`.
- The builder reports that a scripted edit emptied `tests/test_factory.py` partway through and was restored from `HEAD`. It's worth checking that the test diff adds rows only.

**Release impact.**
- IMPACT: patch — the factory's evidence check now refuses git reads that run gpg. That's a stricter, more correct check, and nothing anyone has to do differently or can newly do.

**Undone items.** None. This change has no `notes.md`, and the builder reports writing nothing there.

**How to recover.** The prompt names no irreversible paths.
