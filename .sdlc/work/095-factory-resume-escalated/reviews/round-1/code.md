VERDICT: PASS

## Notes

I found no Critical or Required findings. I walked R1–R14 against the diff and the tests.

- **Optional:** `plugins/factory/skills/build/SKILL.md` has one very long line, the artifacts list with the added `decision-<n>.md` clause. It wraps differently from its neighbours. Re-wrap it.
- **Optional:** in `cmd_restart`, a restart that is already under way ignores a differing `--words`. The existing record's `WORDS:` stays, because the record isn't rewritten on that path. The tool does nothing wrong, but a rerun with different words silently drops them. The tool could say so, or refuse the mismatch.
- **Nit:** `restart_state` returns `reasons` as the whole decision text. The spec says "the decision's text", so this matches it. The skill only needs the first reason, so the skill has to extract it itself.
- **Done well:**
  - A single `restart_state()` serves both `start` and `restart`, so the check and the write can't drift apart.
  - The write order of record, rename, then stage lets a cut-short run be resumed, and the rename never overwrites an archive.
  - Counting the round limit and `depth()` from the restart round is small and contained.
  - `decision.md` is the only decision any reader sees, so ready, land and the board needed no change.
  - Only `factory.py restart *` is added to the skill's rules, and the one WAIT is kept.
- **Run:** `./check.sh` exited 0 with ruff clean, the formatter clean, 1923 tests passed, and plugin validation passing for both plugins. Validation printed one warning, for the factory plugin's missing icon. It predates this change and doesn't affect the result.
- **Not checked:** I read the `tests/test_factory.py` and `tests/test_board.py` changes only through the gate's pass. I did not read them test by test against each R-named test.
