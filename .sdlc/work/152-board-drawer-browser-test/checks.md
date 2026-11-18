# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## CI's Linux job installs Chromium before its tests, and Windows doesn't

The step is a line in the workflow that nothing else reads, so only removing it could fail this.

```sh
grep -q '^      - run: uv run --group dev playwright install --with-deps --only-shell chromium$' .github/workflows/check.yml && test "$(grep -c playwright .github/workflows/check.yml)" -eq 1 && awk '/playwright install/{p=NR} /pytest -q -n auto/{t=NR} END{exit !(p && t && p < t)}' .github/workflows/check.yml
```

## Playwright is in the dev group, with the browser marker

Two lines of pyproject.toml; the suite would still pass without the marker's declaration.

```sh
grep -q '^  "playwright>=1.49",$' pyproject.toml && grep -q '^  "browser: ' pyproject.toml
```

## CONTRIBUTING says how to install the browser locally

A paragraph of prose, which no test reads.

```sh
grep -q 'uv run --group dev playwright install --only-shell chromium' docs/CONTRIBUTING.md
```
