# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## AGENTS.md's Skills list names update

A word in a list of prose, which no test reads back; only an edit that took it out could fail it.

```sh
grep -q 'Skills that write (`intent`, `spec`, `ship`, `close`, `drop`, `update`,' AGENTS.md
```

## The factory README says 75 is the exit to use

The `[park]` block's comment, which only a deliberate edit could drop.

```sh
grep -q '75 (EX_TEMPFAIL) is the one to use' plugins/factory/README.md
```
