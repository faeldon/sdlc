I've pinned CI's actions to commit SHAs, added Dependabot to propose the bumps, and added a test that fails on any tag or branch pin. The tests I ran pass. Whether CI itself is green can only show once the change is committed and pushed, at `/sdlc:ship`. Everything is left uncommitted.

**Slices built**
1. **The test.** `tests/test_ci.py` reads every file in `.github/workflows/` as text and lists each `uses:` that isn't a full 40-character SHA followed by a `# v<version>` comment. Local `./` actions are allowed. The file is marked `portable`, so CI's Windows job runs it too. Run against the old `@v4` and `@v6` pins, it failed and named all four `uses:` lines.
2. **The pins.** Each pin in `check.yml` is the commit its current tag names, so CI's behaviour doesn't change:

   | Action | Was | Now |
   |---|---|---|
   | `actions/checkout` | `@v4` | `@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0` |
   | `astral-sh/setup-uv` | `@v6` | `@d0cc045d04ccac9d8b7881df0226f9e82c39688e # v6.8.0` |

   `v6` is an annotated tag, so I followed it to the commit it names. I also extended the comment above `permissions:` to say why the actions are pinned.
3. **Dependabot.** The new `.github/dependabot.yml` covers `github-actions` in `/`, weekly. It's proved by an acceptance check in `checks.md` rather than a test, since only removing the file could break it.

**Tests added**
- `test_the_check_refuses_a_tag_or_branch_pin`: the rule refuses a tag, a branch, a short SHA and a SHA with no version comment, and accepts a commented SHA and a local action.
- `test_every_action_is_pinned_to_a_commit`: every `uses:` in the repo's workflows passes that rule.

**Named runs:** `tests/test_ci.py`, `test_the_gate_and_ci_never_run_the_skills_cases` and `tests/test_windows.py` together passed 113. Ruff check and format on the new file are clean, and `sdlc.py accept 221` passed. I didn't run the whole suite; the gate does that.

**`plan.md`:** written before the code. It's a short plan for three files, and the build matches it.

**`notes.md`:** nothing left.

The intent's open question (Dependabot, or bumps by hand) is answered by its own Outcome, which asks for Dependabot, so I raised no decision.

- UNTESTABLE: R4: "CI is green on the change's commit" needs a push and a GitHub runner, which only happen after `/sdlc:ship`.

## Evidence

$ gh api repos/actions/checkout/git/ref/tags/v4 --jq '.object.type+" "+.object.sha'
commit 11d5960a326750d5838078e36cf38b85af677262
exit: 0

$ gh api repos/astral-sh/setup-uv/git/ref/tags/v6 --jq '.object.type+" "+.object.sha'
tag d0d8abe699bfb85fec6de9f7adb5ae17292296ff
exit: 0

$ gh api repos/astral-sh/setup-uv/git/tags/d0d8abe699bfb85fec6de9f7adb5ae17292296ff --jq '.object.type+" "+.object.sha+" "+.tag'
commit d0cc045d04ccac9d8b7881df0226f9e82c39688e v6
exit: 0

$ gh api repos/actions/checkout/tags --paginate --jq '.[] | select(.commit.sha=="11d5960a326750d5838078e36cf38b85af677262") | .name'
v4.4.0
v4
exit: 0

$ gh api repos/astral-sh/setup-uv/tags --paginate --jq '.[] | select(.commit.sha=="d0cc045d04ccac9d8b7881df0226f9e82c39688e") | .name'
v6.8.0
v6.8
v6
exit: 0

$ uv run --group dev pytest -q tests/test_ci.py   (before pinning)
E       AssertionError: {'check.yml': ['- uses: actions/checkout@v4', '- uses: astral-sh/setup-uv@v6', '- uses: actions/checkout@v4', '- uses: astral-sh/setup-uv@v6']}
FAILED tests/test_ci.py::test_every_action_is_pinned_to_a_commit - AssertionE...
1 failed, 1 passed in 0.03s
exit: 1

$ uv run --group dev pytest -q tests/test_ci.py tests/test_skills.py::test_the_gate_and_ci_never_run_the_skills_cases tests/test_windows.py
113 passed in 25.69s
exit: 0

$ uv run --group dev ruff check tests/test_ci.py && uv run --group dev ruff format --check tests/test_ci.py
All checks passed!
1 file already formatted
exit: 0

$ sh -c "<checks.md's Dependabot block>"
exit: 0

$ uv run --quiet --script scripts/sdlc.py accept 221
  "passed": true,
  "problems": []
}
exit: 0

$ git status --short
 M .github/workflows/check.yml
?? .github/dependabot.yml
?? .sdlc/work/221-ci-pinned-shas/
?? tests/test_ci.py
exit: 0
