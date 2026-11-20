VERDICT: PASS

The re-check after the slot wait is in both `cmd_gate` functions, and the docs now say what the person asked. I read the diff and ran no tests. I took the full gate's green result from the builder's report and did not read `build/land-1.gate.md`.

## Notes
- NIT: plugins/factory/scripts/factory.py:2898: the comment still says the ledger "guards against a write in a worktree, never one into the git common dir". Use the docs' wording (the Edit and Write tools, not a shell that can reach the git common dir). {docs S med}
- **Check after the wait:** each gate refuses with "this attempt was not recorded" when the earlier record is no longer vouched for. It does this before reading the earlier attempts, and writes nothing to the record or the ledger.
- **Tests:** the builder's two new tests have the check command itself forge the record mid-run, and each failed before the code and passed after it.
- **Docs:** the README, REFERENCE.md and the land skill all say the same thing, and the builder also updated the acceptance check in `checks.md` to grep for the new wording.
- **Remaining gap:** a forgery landing between this re-check and the vouch is still possible. A shell command in the same worktree could do that, and that is the case the docs already disclaim.
