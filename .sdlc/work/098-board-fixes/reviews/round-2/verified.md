- KEPT: ux: C1: scripts/board.py:601-605: the stage-missing check (601) returns "fix intent.md's frontmatter" before the `rebasing` branch (605), so a rebasing card whose `intent.md` won't read never says its rebase is stopped. That is the case the comment at 603-604 names.

## Notes
I only read `scripts/board.py` lines 570-650 and ran nothing. The code matches the change's description. The `rebasing` branch sits at 605, below the `problems and stage is None` return at 601-602.

I did not trace where `entry["rebasing"]` is set. I did not check whether it can be true while `stage` is None. The comment at 603-604 says that case happens, and a conflict in `intent.md` would cause it.
