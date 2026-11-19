Line 544 is stale and was not updated.

- KEPT: code: C1: docs/REFERENCE.md:544: the look line still reads `- ESCALATED: look: <why>`; the approver now writes `<what to look at> — <why>`, and the decide question quoting the target isn't mentioned

## Notes
I read `docs/REFERENCE.md` and the approver diff, and ran nothing. `docs/REFERENCE.md` isn't among the modified files in `git status`, so no edit to it exists yet. The path is in the diff's scope because `plugins/factory/agents/approver.md` changed the form. I didn't open the decide skill's diff, so I didn't check that its question really quotes the target. The approver text says it does.
