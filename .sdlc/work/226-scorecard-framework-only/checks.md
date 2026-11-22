# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The scorecard ends after Hosts

The build plan's sections are deleted text; only putting them back could fail this.

```sh
f=docs/RETRO-SCORECARD.md
test "$(grep '^## ' "$f" | tail -1)" = "## Hosts" &&
  ! grep -q -e '^## Seeds to build it' -e '^### Waves' -e 'lists the seeds that build it' "$f"
```

## Every Status line is captured or not captured, with no seed id or change number

The lines are reworded text; only a revert or a new edit naming a seed again could fail this.

```sh
f=docs/RETRO-SCORECARD.md
test "$(grep -c '\*\*Status:\*\*' "$f")" -eq 36 &&
  ! grep '\*\*Status:\*\*' "$f" | grep -v -E '\*\*Status:\*\* (captured|not captured: )' | grep -q . &&
  ! grep -A3 '\*\*Status:\*\*' "$f" | grep -E '\bS[0-9]+\b|\bR[0-9]+\b|\b1[0-9]{2}\b' | grep -v '\*\*What' | grep -q .
```

## This repo releases on Release due

The wave-based release block is deleted text in `.sdlc/SDLC.md`.

```sh
! grep -q -e 'release follows the waves' -e '^### The release loop' .sdlc/SDLC.md
```

## The contributor docs no longer list the scorecard's seeds

The scorecard row's wording is deleted text.

```sh
grep -q '^| `docs/RETRO-SCORECARD.md` |' docs/CONTRIBUTING.md &&
  ! grep -q 'the seeds that build it' docs/CONTRIBUTING.md
```

## No seed id or wave change number is left anywhere in the scorecard

The ids were deleted from the prose; only putting one back could fail this. The baselines' change
ranges (`139–148`) are figures, not plan ids, and don't match.

```sh
! grep -qE '\bS[0-9]+\b|\bR[0-9]+\b|\(1[0-9]{2}\)|, 1[0-9]{2}\)' docs/RETRO-SCORECARD.md
```
