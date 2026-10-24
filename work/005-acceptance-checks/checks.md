# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## config lists the checks template

The template exists and `config` names it under `templates`, so a skill or the factory can start a
change's `checks.md` from it.

```sh
uv run --quiet --script scripts/sdlc.py config | grep -q '"checks.md": {'
```

## Stage 4 points acceptance at checks.md, in the default and this repo's copy

Only reverting the Stage 4 edit could fail this; the own-copy test holds the two together.

```sh
grep -Fq 'section of the change'"'"'s `checks.md`, one `sh` block' defaults/SDLC.md &&
  grep -Fq 'section of the change'"'"'s `checks.md`, one `sh` block' .sdlc/SDLC.md
```

## The factory's test reviewer asks for checks.md, not notes.md

```sh
grep -Fq 'ask for it as a section of the change'"'"'s' plugins/factory/agents/reviewer-test.md &&
  ! grep -Fq 'instead of kept in the suite' plugins/factory/agents/reviewer-test.md
```
