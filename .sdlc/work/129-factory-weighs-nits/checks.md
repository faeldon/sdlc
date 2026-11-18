# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The docs name the factory's landing as a source of nits

R13's wording in the guides and the register's template: prose no code reads, so only a revert
would take it back.

```sh
grep -q "rest are filed as nit entries at landing, on the person's yes" guide/review.md && ! grep -q "never weighed or filed" guide/review.md && grep -q '| `\[nit\]` | a finding approved unfixed | `/sdlc:ship`, or the factory'"'"'s landing |' guide/process.md && grep -q "factory's landing) approved unfixed" templates/inbox.md
```
