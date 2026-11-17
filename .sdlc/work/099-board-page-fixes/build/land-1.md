I resolved the two conflicts in `.sdlc/work/inbox.md`, the only file I edited, and ran no git command. One call goes beyond simply keeping both sides: I dropped this change's entry 2026-11-17-60 because the base already files the same bug as 2026-11-17-50. The register parses into 44 entries with no duplicate ids, and the gate passes (2074 passed, 9 skipped).

**First conflict (the board bug entries):** each side had removed the entries its own fixes cover. The base dropped -22 and -23, the two `scripts/board.py` bugs, which I take to be the work of `098-board-fixes`. I'm inferring that from the entries, since I couldn't check history without git. This change dropped -24, -25 and -26, its `fixes:`. The resolution keeps both removals, so none of the five entries remains, and I took out the extra blank line that left behind.

**Second conflict (new entries at the end):**
- **Kept from the base:** -50 to -58, in their order. The base side's -58 ended without its `Raised 2026-11-17.` line, so I added it there; the shared line after the markers still closes this change's last entry.
- **Kept from this change:** -59, -61 and -62, which this change carried forward when it landed, after the base's entries. The ids don't clash.
- **Dropped:** this change's -60, about the board rebuilding every card on each poll. It repeats the review finding the base already files as -50, which also carries a severity and paths, so keeping both would duplicate it in the register.

**Overlap left for you:** the base's -53, -54 and -55 are ideas `098-board-fixes` carried forward. -53 is the drawer's missing focus trap; -54 and -55 are Needs you sitting last on a phone. This change fixes all three, but its `fixes:` names only -24 to -26, so I kept them rather than remove entries the change doesn't declare.

- DECISION: [default] Close the base's -53, -54 and -55 along with this change? Options: add them to the intent's `fixes:` so they close when it lands; or leave them open. Going ahead with leaving them open. I recommend adding them to `fixes:`, since this change fixes what they describe.

## Evidence

$ grep -c -E "^(<<<<<<< |=======$|>>>>>>> )" .sdlc/work/inbox.md
0
exit: 1

$ grep -o "^## \[[0-9-]*\]" .sdlc/work/inbox.md | sort | uniq -d | wc -l
       0
exit: 0

$ uv run --quiet --group dev python -c "... m.inbox_entries(Path('.')) ..."
44 True ['2026-11-17-50', '2026-11-17-59', '2026-11-17-61', '2026-11-17-62']
exit: 0

$ ./check.sh
All checks passed!
223 files already formatted
2074 passed, 9 skipped in 45.27s
✔ Validation passed
✔ Validation passed
exit: 0
