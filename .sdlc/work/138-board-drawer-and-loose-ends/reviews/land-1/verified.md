- KEPT: code: C1: .sdlc/work/inbox.md:196: the change's branch deletes seeds 2026-11-18-8, -9, -10, -11 and -12 from the base's register (32 lines). `git diff f1a17ae...HEAD -- .sdlc/work/inbox.md` shows the removals. The register belongs to the base branch, and close retires seeds inside the `Close` commit.

## Notes
I ran `git diff --stat` and the inbox.md diff against `f1a17ae...HEAD`. I did not run the tests or open `entries.md`. The diff contains the deletion, and that settles the claim.
