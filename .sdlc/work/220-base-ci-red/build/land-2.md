FIX: ALREADY MADE

No line of `SIGNAL_KINDS` (`plugins/factory/scripts/landing.py`, lines 542–545) is over 100 characters, so I edited nothing. The longest line is exactly 100, starting `"sensitive", "irreversible", "issue", "ci", ...`, which is the repo's ruff limit (`line-length = 100`), and ruff's line-length rule (E501) passes on the file.

If you want that line shorter than 100 anyway, I can wrap the tuple onto more lines.

## Evidence

$ sed -n 536,560p plugins/factory/scripts/landing.py | awk '{print length": "$0}'
16: SIGNAL_KINDS = (
100:     "sensitive", "irreversible", "issue", "ci", "impact", "escalated", "open", "assumed", "settled",
97:     "resolved", "fixed", "unreviewed", "auto_off", "undone", "checks", "cases", "nits", "unread",
14: )  # fmt: skip
exit: 0

$ awk 'NR>=542 && NR<=545 && length>100 {print NR": "length; n++} END {print (n+0)" lines over 100"}' plugins/factory/scripts/landing.py
0 lines over 100
exit: 0

$ uv run --group dev ruff check --select E501 plugins/factory/scripts/landing.py
All checks passed!
exit: 0
