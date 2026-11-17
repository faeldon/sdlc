- KEPT: code: C1: AGENTS.md:434: the line says `verdicts` "never reads a state file", but this change makes it read `runs/mended` (factory.py:1158), and AGENTS.md:443 now calls that "the one file a run writes that `verdicts` reads back". Reword 434 to name the exception, and rewrap 437–443.

## Notes
- I read AGENTS.md lines 432–445 and the diff against the merge base.
- The diff adds the `runs/mended` sentence at 443 and leaves line 434 as it was, so the two lines now contradict each other.
- I grepped factory.py: `mended(folder)` is called from the `verdicts` path at line 1157, so the code agrees with line 443, not with 434.
- Lines 437–443 are unevenly wrapped: some lines run long, and the added sentence ends on a long line.
- I ran no tests.
