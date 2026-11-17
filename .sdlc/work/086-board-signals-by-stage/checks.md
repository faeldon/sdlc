# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The card's flags count each signal only at its stage

The page has no test runner, and only an edit back to the ungated lines could break these two.

```sh
grep -qF 'c.stage === "build" ? c.pending' scripts/board.html && grep -qF 'c.stage === "test" && c.decision === "ESCALATE"' scripts/board.html
```

## The decision chip is live only at test, and history past it

The page has no test runner, and only an edit back to the ungated chip could break this.

```sh
grep -qF 'c.stage === "test" ? c.decision' scripts/board.html && grep -qF '`was ${c.decision}`' scripts/board.html && ! grep -qF 'c.decision ? h("span", { class: "badge" }, c.decision)' scripts/board.html
```
