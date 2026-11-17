- KEPT: code: C1: .sdlc/work/inbox.md:312-337: seed 2026-11-17-85 (the `[bug]` about the ui and ux reviewers) is missing from this branch but still on main. The diff against main removes it along with 52, 56, 57, 58, 69 and 70. It isn't among the change's own seeds, so the landing dropped a live bug report.

## Notes
I ran read-only commands only: `grep` on the branch and on `main:.sdlc/work/inbox.md`, and a `git diff main` of the inbox headings. The `## [2026-11-17-85]` heading is at line 355 on main. It is absent here, and 84 is the last seed before the gap.
