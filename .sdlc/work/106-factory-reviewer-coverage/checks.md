# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## This repo's UI review serves the board fixture

R12 is a line of this repo's own config, which no test reads: only editing it back could undo it.

```sh
grep -q '^serve = "sh tests/fixtures/board/serve.sh {fixture} {port}"$' .sdlc/factory.toml && grep -q '^fixture = "tests/fixtures/board/changes"$' .sdlc/factory.toml && grep -q '"tests/fixtures/board/"' .sdlc/factory.toml && test -f tests/fixtures/board/serve.sh && test -f tests/fixtures/board/build.sh
```
