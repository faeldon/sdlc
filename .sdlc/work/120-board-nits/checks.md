# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The board's stop test is parenthesised

`_progress()` reads the same with or without the parentheses, so no test can tell them apart;
only putting the bare `or ... and` back removes them.

```sh
grep -qF 'if entry.get("stopped") or ((folder / STOPPED).is_file() and entry["stage"] == "build"):' scripts/board.py
```
