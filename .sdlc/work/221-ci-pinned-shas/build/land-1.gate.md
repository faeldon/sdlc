GATE: FAIL

## Attempt 1

Verdict: FAIL
Command: ./check.sh
Build: aa3b806bb6bc5939
Exit: 1
Seconds: 0.1
Waited: 0.0
Tree: unchanged

Last 80 lines of its output:

    E501 Line too long (103 > 100)
       --> plugins/factory/scripts/landing.py:544:101
        |
    542 | SIGNAL_KINDS = (
    543 |     "sensitive", "irreversible", "issue", "impact", "escalated", "open", "assumed", "settled",
    544 |     "resolved", "fixed", "unreviewed", "auto_off", "undone", "checks", "cases", "nits", "ci", "unread",
        |                                                                                                     ^^^
    545 | )  # fmt: skip
        |
    
    Found 1 error.
