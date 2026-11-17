- KEPT: code: C1: .sdlc/work/inbox.md:162: the branch is not rebased onto main (`175ad83`), and a merge-tree of the two conflicts in the register, so the recorded gate doesn't cover what would land.

## Notes
I ran `git log`, `git rev-parse`, `git merge-base` and `git merge-tree --write-tree HEAD main`. The change's base is `93f2ba1` and main has three commits it lacks. The merge-tree reports a content conflict in `.sdlc/work/inbox.md`. It lists only that file as conflicted, which matches the claim. I did not count the conflict hunks or check the other files beyond that. I ran no tests.
