# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## No WAIT's literal question changed (R11)

The change adds a preview beside each question and rewords none; only an edit to a quoted
question line could fail it, and no later change reruns it.

```sh
! git diff "$(git merge-base HEAD main)" -- skills plugins/factory/skills | grep -E '^[-+]> `'
```

## The docs say the yes options carry the draft as their preview (R13)

AGENTS.md's *Skills* invariant and CONTRIBUTING.md's **One approval per writing skill** each say
it; only removing the sentence could fail it.

```sh
grep -q "only a chosen yes approves), its yes options carrying what the yes" AGENTS.md &&
grep -q "writes as their \`preview\` (cut past 40 lines to its approving part" AGENTS.md &&
grep -q "The dialog's yes options carry the draft as their \`preview\`" docs/CONTRIBUTING.md &&
grep -q "preflight NNN --preview" docs/REFERENCE.md
```
