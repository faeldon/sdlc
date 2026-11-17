I resolved the one conflict in `.sdlc/work/inbox.md` by keeping both sides' new entries. Both sides had only added seeds at the end of the register, after 2026-11-17-80. I ran no git command and edited no other file. The gate passes on the result (2208 tests).

**From the base branch:** seed 2026-11-17-85, the bug that the factory's ui and ux reviewers can't run at the same time, filed in `e7e2f1a`. I kept it as written.

**From this change:** seeds 2026-11-17-81 to -84, the four follow-ups carried over from this change's `notes.md`:
- 81: wrap long tokens in a card's next step.
- 82: shorten the stop's `NEXT:` wording for phone-width cards.
- 83: add parentheses to the stop test in `_progress()`.
- 84: say "stopped: mend" in plain words.

I kept all four as written.

The five entries now run in id order (81–84, then 85), each once, with one blank line between them. Seeds 52, 56, 57, 58, 69 and 70 stay deleted, and no conflict markers remain.

## Evidence

```
$ grep -c -E '^(<<<<<<<|=======|>>>>>>>)( |$)' .sdlc/work/inbox.md
0
exit: 1

$ grep -c -E '^## \[2026-11-17-(52|56|57|58|69|70)\]' .sdlc/work/inbox.md
0
exit: 1

$ grep -o -E '^## \[2026-11-17-8[0-5]\]' .sdlc/work/inbox.md | sort | uniq -c
   1 ## [2026-11-17-80]
   1 ## [2026-11-17-81]
   1 ## [2026-11-17-82]
   1 ## [2026-11-17-83]
   1 ## [2026-11-17-84]
   1 ## [2026-11-17-85]
exit: 0

$ uv run --quiet --script scripts/sdlc.py check --strict
■ Problems: 0
    none ✅
exit: 0

$ ./check.sh
All checks passed!
2208 passed, 13 skipped in 58.56s
✔ Validation passed
✔ Validation passed
exit: 0
```

The two `grep -c` lines exit 1 because they found no matches, which is the result wanted here.
