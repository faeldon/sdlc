# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The factory runs one gate at a time and autopilot is enabled

Two settings in this repo's own `.sdlc/factory.toml`, which no test reads, so only an edit back
could fail it.

```sh
uv run --quiet --group dev python -c 'import tomllib, sys; c = tomllib.load(open(".sdlc/factory.toml", "rb")); sys.exit(0 if c.get("gate_jobs") == 1 and c.get("autopilot", {}).get("enabled") is True else 1)'
```

## The header says why, for M25's run, and no longer says two gates

The header comment's account of `gate_jobs` is prose only a rewrite could undo.

```sh
head -12 .sdlc/factory.toml | grep -q 'M25' && ! grep -q 'two gates at once' .sdlc/factory.toml && ! grep -q '^guards' .sdlc/factory.toml
```
