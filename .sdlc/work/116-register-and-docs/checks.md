# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## No comment in sdlc.py calls the change folder work/

The six comments were reworded; only putting the old words back could bring a bare `work/` into a
`#` comment, where `HISTORY_WORK` is named by the constant, never as a path.

```sh
! grep -nE '^[[:space:]]*#.*[^/]work/' scripts/sdlc.py
```

## CONTRIBUTING's tracker section lists every intake method core calls

The list is prose in the contributor doc; only an edit taking a method out of it could fail this.

```sh
s=$(sed -n '/^## Writing a tracker/,/^## Releasing/p' docs/CONTRIBUTING.md) && for m in 'intake()' 'dangling(recorded)' 'titles(numbers)' 'open_numbers()' 'open_marks()' 'mark(number' 'needs_info(number' 'closed_by(message)' 'unmark(number'; do printf '%s\n' "$s" | grep -qF "\`$m" || { echo "missing: $m"; exit 1; }; done
```
