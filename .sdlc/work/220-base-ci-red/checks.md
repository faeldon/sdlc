# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The tracker interface lists ci() as optional

R10: only an edit removing the line from *Writing a tracker* could fail it.

```sh
grep -q '^- `ci(branch, sha, timeout)`, optional: CI on commit' docs/CONTRIBUTING.md
```

## REFERENCE.md says what a red base shows and when nothing does

R10: only an edit removing the paragraph under *Trackers* could fail it.

```sh
grep -q '^\*\*CI on the base branch\.\*\*' docs/REFERENCE.md && grep -q 'nothing new is shown\.$' docs/REFERENCE.md
```

## AGENTS.md names the CI cache beside the update cache

R10: only an edit taking `CI_CACHE` back out of *Updates* could fail it.

```sh
grep -q 'reading, `sdlc-ci.json` (`CI_CACHE`, `base_ci()`' AGENTS.md && ! grep -q 'That cache is the one write made with' AGENTS.md
```
