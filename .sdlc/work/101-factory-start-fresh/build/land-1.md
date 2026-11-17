The conflict in `.sdlc/work/inbox.md` is resolved, both sides' changes are kept, and the gate passes on the result (2089 passed, exit 0). I edited only that file and ran no git command.

**First conflict: seeds -39 and -40.** Each side had removed a different seed:
- The base had already removed seed **2026-11-17-39** ("The landing writes How to recover…") but still held -40.
- This change removed **2026-11-17-40**, one of its own two seeds (`idea: [2026-11-17-40, 2026-11-17-43]`), and still held -39.

Keeping both meant removing both entries, along with the `Raised 2026-11-17.` line they shared. Seed -38 now runs straight into -41. The change's other seed, -43, had already merged cleanly and is gone.

**Second conflict: new entries at the end.** Both sides had appended entries:
- From the base: bugs **-50** and **-51**, and ideas **-52** to **-59**, **-61** and **-62**, all kept as they were.
- From this change: **-63** and **-64**, the two items carried forward from `notes.md`, placed after -62.
- -62 gets its own `Raised 2026-11-17.` line back, so each entry ends with one.

The base doesn't use -63 or -64, so no id appears twice. None of -39, -40 or -43 is left, and `sdlc.py`'s `inbox_entries()` reads all 44 entries, ending -61, -62, -63, -64.

Two things to know:
- **Truncated titles on -63 and -64.** The carry-forward that wrote them used only the first line of each wrapped `notes.md` item, so both titles end mid-sentence ("…by the spec's boundary: sharing", "…but doesn't show them, and"). I left the text as that side wrote it; rewording a seed is for the person.
- **9 skipped tests.** These are new on the base: the parametrized board test at `tests/test_board.py:1088` skips itself when two stages differ. They have nothing to do with this resolution.

## Evidence

```
$ grep -nE '^(<<<<<<<|=======|>>>>>>>)( |$)' .sdlc/work/inbox.md; echo "markers: $?"
markers: 1
exit: 0

$ git show 54dff78:.sdlc/work/inbox.md | grep -n '2026-11-17-\(39\|40\|43\|60\|63\|64\)\]'
278:## [2026-11-17-40] [idea] factory.py start brings the change's branch up to date first
305:## [2026-11-17-43] [idea] Limit how many factory gates run at once
exit: 0

$ grep -oE '^## \[[0-9-]+\]' .sdlc/work/inbox.md | sort | uniq -d | wc -l; grep -cE '^## \[2026-11-17-(39|40|43)\]' .sdlc/work/inbox.md; uv run --group dev python -c "<load scripts/sdlc.py; print inbox_entries()>"
       0
0
44 ['2026-11-17-61', '2026-11-17-62', '2026-11-17-63', '2026-11-17-64']
exit: 0

$ ./check.sh > /tmp/check-101-resolve.log 2>&1; echo "exit: $?"; grep -E "passed|failed|All checks|Validation" /tmp/check-101-resolve.log
exit: 0
All checks passed!
2089 passed, 9 skipped in 46.75s
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q -rs -n auto 2>&1 | grep SKIP
SKIPPED [1] tests/test_board.py:1088: decision pending and approver decided set different stages
SKIPPED [1] tests/test_board.py:1088: stage missing and closed set different stages
(… 9 in all, every one tests/test_board.py:1088 "… set different stages")
exit: 0
```
