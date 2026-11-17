I resolved the conflict in `.sdlc/work/inbox.md` by keeping every entry from both sides; no other file was edited. The full gate passes on the result (2,237 tests, 13 skipped). I ran no git command, so `factory.py` still needs to stage the file and continue the rebase.

**From the base branch:** its six new entries, 2026-11-17-81 to -86, unchanged and in order:
- four ideas carried forward from 110-board-says-it-plainly (81–84);
- bug 85: the ui and ux reviewers can't run at once;
- bug 86: a landing review reads the base branch's newer commits as the change's deletions.

**From this change:** its two entries, placed after the base's:
- 2026-11-17-87, the suite-pruning pass from spec R11;
- 2026-11-17-88, sharing one `-U0` diff per change between retro's rework and spend.

The two sides used different numbers, so nothing needed renumbering. The register now runs 80 to 88 with no gaps or repeats, and no conflict markers are left.

**Deleted, as you said:** 2026-11-12-2 appears nowhere in the file.

## Evidence

```
$ grep -cE "^(<<<<<<<|=======|>>>>>>>)" .sdlc/work/inbox.md
0

$ grep -c "2026-11-12-2\]" .sdlc/work/inbox.md
0

$ grep -o "^## \[2026-11-17-8[0-9]\]" .sdlc/work/inbox.md | tr '\n' ' '
## [2026-11-17-80] ## [2026-11-17-81] ## [2026-11-17-82] ## [2026-11-17-83] ## [2026-11-17-84] ## [2026-11-17-85] ## [2026-11-17-86] ## [2026-11-17-87] ## [2026-11-17-88]

$ ./check.sh 2>&1 | grep -E "passed|failed|All checks|already formatted|Validation"   (pipefail set)
All checks passed!
255 files already formatted
2237 passed, 13 skipped in 55.12s
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --quiet --script scripts/sdlc.py check --strict
exit: 0
```
