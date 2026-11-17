I resolved the one conflict, in `.sdlc/work/inbox.md`, and the gate is green on the result: 2257 passed, 13 skipped. I edited only that file and ran no git command that changes anything.

- **From the base branch:** its version of the register, with seeds `2026-11-17-65` and `-66` left removed. The base deleted them when `0a99c1d` ("Correct the work/ comments, idea's themes and the tracker docs") landed. This change's side of the conflict still had them only because that commit came after this change's base, so bringing them back would undo the base's work.
- **From this change:** seed `2026-11-17-63` (the idea this change builds), deleted with its body and its `Raised 2026-11-17.` line, as the landing asked.

No conflict markers are left. Diffing the result against the base branch's register shows the only difference is entry 63's lines. The seeds on either side (`-59`, `-76` and on) are untouched.

## Evidence

```
$ grep -c "^<<<<<<<\|^=======\|^>>>>>>>" .sdlc/work/inbox.md
0
exit: 1

$ grep -n "2026-11-17-6[3-6]\]" .sdlc/work/inbox.md
(no output)
exit: 1

$ diff <(git show HEAD:.sdlc/work/inbox.md | grep -v "2026-11-17-63") .sdlc/work/inbox.md
191,195d190
< 
< Left undone by 101-factory-start-fresh, carried forward when it landed: `sdlc.py gate` (the hand gate) takes no `gate_jobs` slot, by 101's spec's boundary: sharing the slots would make the lock files' names a contract between sdlc and sdlc-factory.
< See .sdlc/work/101-factory-start-fresh/notes.md in its commit.
< Raised 2026-11-17.
<
exit: 1

$ ./check.sh > /tmp/113-check.log 2>&1
All checks passed!
255 files already formatted
2257 passed, 13 skipped in 72.37s (0:01:12)
✔ Validation passed
✔ Validation passed
exit: 0
```

The two `grep` commands exit 1 because they found nothing, which is the result wanted: no markers and no entries 63–66. The `diff` exits 1 because the files differ, and the lines it shows are only entry 63, which was meant to go.
