VERDICT: PASS

## Notes

**What the rework changed.** It made the change I filed as a NIT in round 1. `workflow_files()` now picks up both `.yml` and `.yaml` files. A new test, `test_a_yaml_workflow_is_read_as_well`, writes `a.yml`, `b.yaml` and `notes.md` into a scratch folder and checks that the first two are picked up and the third is not. So a workflow saved as `.yaml`, which GitHub also runs, can no longer hold an unpinned action that the test misses.

**What I checked and ran.**
- **The workflow and Dependabot files are unchanged since round 1.** The two SHA pins in `check.yml` are still the ones I checked upstream last round, and they match the commits the old `v4` and `v6` tags pointed at. `dependabot.yml` adds no new privilege, since its pull requests run on the same `contents: read` token.
- **The matcher.** Any `uses:` value it can't read as a pin still counts as a failure, whether quoted or `docker://`. That is the safe direction. Local `./` actions are still excluded, which is right because they run the repo's own code.
- **The new test** writes its file with `encoding="utf-8"` and `newline="\n"`, and the module stays marked `portable`, so it runs in CI's Windows job too.
- **The gate.** `build/round-2.gate.md` shows `./check.sh` passed, exit 0, tree unchanged.
- **The tests.** I ran `uv run --group dev pytest tests/test_ci.py -q` myself: 3 passed.

**Low, accepted from round 1.** The version comment is still checked for its shape only, so nothing confirms the SHA belongs to that release. Dependabot rewrites the SHA and the comment together, so I'd accept this.

**Done well.** The rework made exactly the fix that was filed and added a test for it, with no change outside `tests/test_ci.py`.
