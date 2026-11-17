The code confirms it: the diff makes `land --close` write `findings.md`, and AGENTS.md line 195 names only ship and `carry` as writers.

- KEPT: code: C1: AGENTS.md:195: the line says only ship and `carry` write `findings.md`, but `land --close` now writes it too (factory.py:4315)

## Notes
I read AGENTS.md and the diff, and ran no tests. The change sits in `untouched` because the diff doesn't edit AGENTS.md. I kept it anyway: the line was true before this diff and is wrong because of it, so the problem is in what this change did, not in older code.
