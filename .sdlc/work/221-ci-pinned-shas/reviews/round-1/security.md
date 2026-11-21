VERDICT: PASS

## Notes

**Trust boundary.** The change covers the third-party code CI runs: `actions/checkout` and `astral-sh/setup-uv`. That code runs with the workflow's token, which is `contents: read` and stays that way. Before the change, whoever controls an action's repo could move its tag to other code, which would then run here (tampering, and elevation of privilege up to that read token). After it, each `uses:` names a commit that can't change, which closes that path. Dependabot opens pull requests that run on that same read-only token, so it brings no new privilege. It also brings no dependency, install script or secret.

**What I checked and ran.**
- **The pinned SHAs.** I checked them against upstream with `git ls-remote`:
  - `actions/checkout`: `11d5960a…7262` is `refs/tags/v4.4.0`, and `refs/tags/v4` points at the same commit. CI runs exactly what it ran before.
  - `astral-sh/setup-uv`: `d0cc045d…688e` is `refs/tags/v6.8.0`, the same as `v6.8^{}` and `v6^{}`. `v6` and `v6.8` are annotated tags, and the pin names the commit they resolve to, not the tag object, which is correct. CI's behaviour doesn't change, as the intent requires.
- **The gate.** `build/round-1.gate.md` shows `./check.sh` passed: exit 0, tree unchanged.
- **The test (`tests/test_ci.py`).**
  - Anything it can't read as a pin, a quoted or `docker://` `uses:` included, counts as a failure, which is the safe direction.
  - Local `./` actions are excluded, which is right.
  - It is marked `portable` and reads with `encoding="utf-8"`.
  - The self-test covers a tag, a branch, a short SHA and a pin with no version comment.

**Low.**
- The test reads only `*.yml` files. A workflow saved as `.yaml`, which GitHub also runs, would get through unchecked. The fix is to glob both extensions.
- The version comment is checked for shape only. Nothing confirms that the SHA really belongs to that release, so a wrong `# v4.4.0` would mislead whoever reads it. Dependabot rewrites both the SHA and the comment together, so the risk is small, and I'd accept it.

- NIT: tests/test_ci.py:52: the workflow glob misses `.github/workflows/*.yaml`, which GitHub also runs, so an unpinned action there would pass the test; glob both extensions {robustness S med}

**Done well.** The pins are the commits the current tags resolve to, each with its release in the comment. The test pins the rule and checks its own matcher. The comment in `check.yml` says why, and Dependabot keeps the pins from going stale.
