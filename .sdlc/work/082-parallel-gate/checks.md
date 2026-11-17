# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The gate runs pytest across the machine's cores

Only an edit to `check.sh`'s pytest line could drop `-n auto`.

```sh
grep -q '^uv run --quiet --group dev pytest -q -n auto$' check.sh
```

## pytest-xdist is a locked test dependency, not a script one

Only an edit to `pyproject.toml`, `uv.lock` or `sdlc.py`'s PEP 723 block could move it.

```sh
grep -q '"pytest-xdist>=3",' pyproject.toml && grep -q '^name = "pytest-xdist"$' uv.lock && ! grep -q xdist scripts/sdlc.py
```

## CI's Linux job runs in parallel and the Windows job's run is unchanged

Only an edit to the workflow could change either line.

```sh
grep -q 'run: uv run --group dev pytest -q -n auto$' .github/workflows/check.yml && grep -q 'run: uv run --group dev pytest -q -m portable$' .github/workflows/check.yml
```
