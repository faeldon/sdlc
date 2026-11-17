DECISION: READY

**Why.** Every outcome in the intent is built and tested. `file` with `-C` in any spelling is refused, and so are `--ext-diff` and `--textconv` on any git read command, short forms included. Each has rows in the one table test, and `file x` and `git diff` stay reads. The only round is `VERDICT: PASS` with two nits, and the gate passed (`./check.sh`, 2336 passed). The code reviewer ran all 14 read rows and 35 non-read rows through `is_read()` and none came out wrong. The intent's open question about git's `-c` is already settled: `_git_reads()` never let it through, and a new row now tests that. Nothing the reviewers wrote suggests the intent itself was wrong.

**Open items.** Both are nits (marked minor in `findings.md`), and neither blocks:
- F1 (code): the comment at `factory.py:208` says git options that "run an external program" are refused. But `git log --show-signature` and `git show --format=%G?` run `gpg` and still count as reads. The comment claims more than the table covers.
- F2 (code): the `--co` prefix also refuses `file --cont` (`--continue`). That's harmless and stays within the strict rule.

**Decisions to confirm.** `decisions.md` doesn't exist, so the ledger has no unticked decisions. The code reviewer did raise one `[default]` call that was never copied into a ledger: should `--show-signature` and `%G…` (both run `gpg`) be refused in this change? It assumed (b): leave them, and file a follow-up idea. Nothing in this build depends on that answer. But `notes.md` doesn't exist either, so nothing will carry it forward at landing. If you want it covered, file it yourself with `/sdlc:idea` (for example, "is_read() refuses git's signature options that run gpg").

**For the person at ship.**
- Start with `_git_reads()` at `factory.py:1179` and the `GIT_RUNS` table at `factory.py:208–210`. Its prefix lengths decide that `--text` stays a read while `--textc` is refused.
- Then the `file` condition at `factory.py:1203–1207`.
- Consider rewording the comment at line 208 to name only the two options it covers (F1).

**Release impact.**
- IMPACT: patch — the factory's evidence check is stricter: three writer commands that wrongly passed as reads are now refused. No interface, config key or file shape changed.

**Undone items.** None: there is no `notes.md`, and the builder put nothing there.

**How to recover.** The prompt names no irreversible paths. The change touches only `plugins/factory/scripts/factory.py` and `tests/test_factory.py`, and a `git revert` of the change's commit undoes it.
