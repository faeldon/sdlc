I built the change: `.github/workflows/check.yml` now gives CI's token read access only. Whether both CI jobs pass with it can only be seen once it's pushed.

- **The change:** the workflow now has a top-level `permissions:` block with `contents: read`, placed after `on:`, with a two-line comment saying why that's enough. Neither job (`linux`, `windows`) sets permissions of its own. This is a Tier 1 change touching one file, so there is no `plan.md`.
- **The open question** (does any step need more than read access?): no. Every step checks out the code, installs tools, or runs ruff and pytest. Nothing pushes, uploads an artifact or comments. `setup-uv`'s cache uses the runner's own cache token, not this one. I didn't edit `intent.md`; the answer is recorded here and in the workflow's comment.
- **Acceptance check:** `checks.md` has one check, "CI's token is read-only". It passes only while:
  - the top-level `permissions:` line exists;
  - the line under it is exactly `  contents: read`, with no further scope indented below it;
  - `permissions:` appears only once in the file, so no job adds its own.

  I ran it before the edit and it failed (exit 1). After the edit it passed, both run directly and through `sdlc.py accept 211`, and left the tree unchanged.
- **No suite test added:** only deliberately removing the block could undo this, so the acceptance check covers it. Nothing in the suite checks the workflow's top-level keys. I ran the one test that reads every workflow file by name, and it passes (1 passed). The workflow still parses as YAML, with `permissions == {'contents': 'read'}` and no permissions on either job.
- **notes.md:** nothing added.

- UNTESTABLE: Outcome "both CI jobs (Linux and Windows) still pass on the push that lands it": that is GitHub Actions running on the pushed commit, which nothing in this repo can start.

No decisions raised.

## Evidence

$ sh -c "$(sed -n '/^```sh$/,/^```$/p' .sdlc/work/211-ci-token-read/checks.md | sed '1d;$d')"   # before the edit
exit: 1

$ sh -c "$(sed -n '/^```sh$/,/^```$/p' .sdlc/work/211-ci-token-read/checks.md | sed '1d;$d')"   # after the edit
exit: 0

$ uv run --quiet --script scripts/sdlc.py accept 211
"name": "CI's token is read-only", "exit": 0, "passed": true, "left": []
"passed": true, "problems": []
exit: 0

$ uv run --quiet --group dev python -c "import yaml; d=yaml.safe_load(open('.github/workflows/check.yml')); print(d['permissions'], list(d['jobs']), [j.get('permissions') for j in d['jobs'].values()])"
{'contents': 'read'} ['linux', 'windows'] [None, None]
exit: 0

$ uv run --group dev pytest tests/test_skills.py::test_the_gate_and_ci_never_run_the_skills_cases -q
1 passed in 0.50s
exit: 0

$ git status --short
 M .github/workflows/check.yml
?? .sdlc/work/211-ci-token-read/
