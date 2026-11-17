# Decisions

- [x] D1 (builder round 1, default): Document `unmark()` as GitHub's own method, not part of core's interface? Options: name it as "core doesn't call it yet"; leave it out; wire it into core in this change. Going ahead with naming it, since the intent listed it but no core path calls it, and wiring it in would add behaviour this change's constraints rule out. → superseded by D2

- [x] R1 (person, restart): wire unmark and send back 116 to the builder
- [x] D2 (builder round 3, default): Call `unmark()` from `sync`, only for an issue this change marked that has left its `closes:` line and that nothing else records, and leave close's marking pass alone. Options: sync only; also close's and `mark-triaged`'s pass; a new command. Going ahead with sync only: close's pass would send just-fixed issues back to triage before the push closes them. → decided: the assumed default, confirmed when landing
- [x] D3 (builder round 3, default): Accept one listing of every open issue with its comments on each `sync`, even for a change with no `closes:` line. Options: always list; skip it when the change's intent never named an issue (would need git history and would miss uncommitted edits). Going ahead with always listing: it is one `gh issue list`. → decided: the assumed default, confirmed when landing
