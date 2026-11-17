I resolved both conflicts in `.sdlc/work/inbox.md`, and the gate passes on the result (2071 passed, 9 skipped). No conflict markers are left, and I ran no git command.

To see what each side meant, I read the base branch's `inbox.md` from the main checkout's working copy, as a file.

**First conflict (entries 30–36):**
- **From the base branch:** it had removed seeds 2026-11-17-31 to -36, the landing bugs and ideas. I left them out.
- **From this change:** it had removed bug 2026-11-17-30 ("The board drops a change while its branch is being rebased"). That is the bug this change fixes, its first outcome. I left it out too.
- Neither side kept anything here, so the hunk is now empty. Entry -29 runs straight into -37, with one blank line between them.

**Second conflict (the end of the file):**
- **From the base branch:** its two new bugs, 2026-11-17-50 (a board poll drops keyboard focus) and -51 (resolve treats its own source as a conflict marker). Both are kept as they were.
- **From this change:** seeds 2026-11-17-52 to -58, the `notes.md` lines carried into the register when this change shipped. They are kept after the base branch's two, so the ids stay in order. No id is used twice.

## Evidence

$ grep -n "^## \[2026-11-17-\(29\|3[0-9]\|5[0-9]\)\]" .sdlc/work/inbox.md   (the main checkout's copy, the base branch's side)
291:## [2026-11-17-29] …
300:## [2026-11-17-30] [bug] The board drops a change while its branch is being rebased
311:## [2026-11-17-37] …
320:## [2026-11-17-38] …
427:## [2026-11-17-50] [bug] A board poll rebuilds every card, dropping keyboard focus
440:## [2026-11-17-51] [bug] A resolve refuses its own source as a conflict marker
exit: 0

$ grep -n "^<<<<<<< \|^=======$\|^>>>>>>> " .sdlc/work/inbox.md
exit: 1

$ ./check.sh
2071 passed, 9 skipped in 63.02s (0:01:03)
✔ Validation passed
exit: 0
