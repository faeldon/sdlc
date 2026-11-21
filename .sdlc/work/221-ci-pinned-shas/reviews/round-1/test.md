VERDICT: PASS

The change has no test gaps. Each Outcome item has a test or a check that would fail without it:

- **Pins and version comments:** `tests/test_ci.py::test_every_action_is_pinned_to_a_commit` reads every `.github/workflows/*.yml`. It fails on any `uses:` that is not pinned to a 40-hex commit with a trailing `# v<version>`. It asserts the workflow list is non-empty, so a glob that matches nothing can't pass it.
- **The rule itself:** `test_the_check_refuses_a_tag_or_branch_pin` runs the checker on inline examples. It refuses `@v4`, `@main`, a short SHA, and a full SHA with no version comment. It accepts a full SHA with a comment and a local `./` action. This test can fail.
- **Dependabot:** the `checks.md` check covers it, since only deleting `.github/dependabot.yml` could fail it. It matches the file I read: `version: 2`, `package-ecosystem: github-actions`, `directory: /`.
- **CI behaviour unchanged:** the diff changes only the `uses:` lines and a comment. The pins are the SHAs the plan names for the current tags.

## Notes
- The gate's record, `build/round-1.gate.md`, shows `Exit: 0` and `3863 passed, 29 skipped`.
- I ran `uv run --group dev pytest tests/test_ci.py -q` myself: 2 passed.
- Both tests are marked `portable`, so CI's Windows job runs them.
- I did not run the `checks.md` check, as the rules require. I expect it to exit 0 against the current tree and leave it unchanged.
- I did not verify that the pinned SHAs match the tags upstream, since that needs `gh` and the network.
- NIT: tests/test_ci.py:16: `VERSION` demands a `v` plus digits, so a comment like `# release-2` would be refused; that is stricter than the outcome's wording but matches the plan {tests S low}
