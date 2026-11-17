# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## Step 1 opens with the change, quoted from its intent

The build skill's Step 1 is prose a model reads, so only an edit back to the old text could drop it.

```sh
t=$(awk '/^## Step 1/{s=1} /^## Step 2/{s=0} s' plugins/factory/skills/build/SKILL.md | tr '\n' ' ' | tr -s ' ')
printf '%s' "$t" | grep -q "What the person sees first is the change itself, then the run." &&
printf '%s' "$t" | grep -q "quoted from its \`intent.md\`, never summarised or shortened" &&
printf '%s' "$t" | grep -q "\`## Problem\` and \`## Outcome\`" &&
printf '%s' "$t" | grep -q "Tier 1 its \`## Approach\` too"
```

## Step 2 asks the script's question, and the hand-filled forms are gone

Only a revert of the skill's text could bring back the restart and upgraded templates a model filled in.

```sh
f=plugins/factory/skills/build/SKILL.md
grep -q "Ask \`start\`'s \`question\` literally, as printed; never word your own." "$f" &&
! grep -q "Send NNN-<slug> back to the factory" "$f" &&
! grep -q "Write this spec and carry on NNN-<slug>" "$f" &&
! grep -q "Leave out the parenthesis" "$f"
```
