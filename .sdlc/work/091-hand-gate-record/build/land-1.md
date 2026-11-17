I resolved both conflicts by keeping both sides in each file. `./check.sh` passes on the result (1,952 tests), no conflict markers are left, and I ran no git command.

**`scripts/board.html`** (the card's top row):
- **Kept from the base branch:** its new `chip` badge, which shows the approver's word only at `test` and as `was …` once shipped or dropped. It replaces the old `c.decision` badge line, so this change's copy of that line is gone.
- **Kept from this change:** the `gate green` / `gate red` badge, shown only while the record is current, placed after the `by hand`/`factory` badge and before the base's chip. Its CSS rules came through the rebase without conflict.

**`docs/REFERENCE.md`** (the board paragraph):
- **Kept from the base branch:** its reworded **Needs you** text in full: a file that won't read at any stage, factory signals only at the stage they belong to, and the stage as the only mark that the person has answered.
- **Kept from this change:** the hand-built Test rule: Test once ship's review has written `findings.md` *or* the gate run by hand is green on the build as it stands, with the badge while that record is current. It goes in place of the base's sentence that ended at `findings.md`. The separate "The gate, run by hand" paragraph came through without conflict.

## Evidence

$ grep -c "^<<<<<<<\|^=======\|^>>>>>>>" docs/REFERENCE.md scripts/board.html
docs/REFERENCE.md:0
scripts/board.html:0

$ ./check.sh
All checks passed!
200 files already formatted
1952 passed in 84.00s (0:01:24)
✔ Validation passed
✔ Validation passed
exit: 0
