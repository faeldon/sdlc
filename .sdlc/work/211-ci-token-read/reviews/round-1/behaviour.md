VERDICT: PASS

The change adds a top-level `permissions: contents: read` block to `check.yml`, after `on:`. It is the only file changed. Neither job sets its own `permissions`, and no step needs more than read. The steps are checkout, `setup-uv`, git config, ruff, playwright install and pytest. There is no upload, comment or push. The spec names no other end-to-end path. I could not confirm that both jobs still pass on the landing push, because that happens in CI.

## Notes
- Gate record `build/round-1.gate.md` says `GATE: PASS`.
- Check "CI's token is read-only" (`checks.md`, read, not run). I expect it to pass.
  - `permissions:` appears exactly once in the file.
  - The line after it is `  contents: read`.
  - The third line after it is blank, not indented, so nothing widens the block.
  - The explanatory comment above the block does not contain the string `permissions:`, so the count of 1 holds.
- I could not parse the YAML, because `python3` has no `yaml` module here. I read the file instead, and its indentation is valid.

## Evidence
$ cat .github/workflows/check.yml
(workflow printed: top-level `permissions:` with `  contents: read`, followed by `jobs:`)
exit: 0

$ git status --short; git diff HEAD --stat
` M .github/workflows/check.yml`, `?? .sdlc/work/211-ci-token-read/`; `.github/workflows/check.yml | 5 +++++`
exit: 0

$ head -5 .sdlc/work/211-ci-token-read/build/round-1.gate.md
GATE: PASS
exit: 0

$ python3 -c "import yaml; ..."
ModuleNotFoundError: No module named 'yaml'
exit: 1

$ grep -c 'permissions:' .github/workflows/check.yml
1
exit: 0
