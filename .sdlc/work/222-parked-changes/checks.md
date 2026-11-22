# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The factory README configures `[park]`, suggesting 75

R18: the README's *Configuration* block gains the three keys; only removing them could fail this.

```sh
grep -q '^\[park\]' plugins/factory/README.md && grep -q '^# exit = 75 ' plugins/factory/README.md && grep -q '^deadline = 60 ' plugins/factory/README.md && grep -q '^retry = 5 ' plugins/factory/README.md && grep -q 'EX_TEMPFAIL' plugins/factory/README.md
```

## REFERENCE.md names the host's side of a park

R18: the `[park]` section and its three `SDLC-BUSY-` lines; only a revert of the section could fail this.

```sh
grep -q "^### A host resource the check waits on: the factory's \`\[park\]\`" docs/REFERENCE.md && grep -q '^SDLC-BUSY-RESOURCE: ' docs/REFERENCE.md && grep -q '^SDLC-BUSY-HOLDER: ' docs/REFERENCE.md && grep -q '^SDLC-BUSY-UNTIL: ' docs/REFERENCE.md
```

## AGENTS.md's `verdicts` sentence names the park

R18 and *Contracts touched*: the map says `verdicts` reads the vouched `runs/parked.md`; only rewording the sentence back could fail this.

```sh
grep -q "reads no state file but \`runs/mended\` and the vouched" AGENTS.md && grep -q '^`runs/parked.md`, and the clock only for a park' AGENTS.md
```
