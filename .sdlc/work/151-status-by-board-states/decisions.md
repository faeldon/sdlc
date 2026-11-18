# Decisions

- [x] D1 (builder round 1, default): Keep `■ Needs you` last, not first as the intent's Outcome says. Going ahead with last unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: last — the board's order, the spec's call and where the eye ends; contradicts the intent's word "first"
  - OPTION: first — what the intent says; breaks the board's order, and the status skill's guidance and test would need rewriting
  - WHY: the spec decided it from the code, the board and the skill, and its "Left for you" names it as the person's call
- [x] D2 (builder round 1, default): Leave the problems only the board reads (a reply with no VERDICT, an unreadable findings or step file) off `status`. Going ahead with leaving them off unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: leave them off — `status` stays quick; such a change sits under its stage's state in `status` but under Needs you on the board, as REFERENCE.md now says
  - OPTION: read them all — closes the gap completely; `status` reads every review file of every change
  - WHY: the spec's Boundaries say to ask before closing this gap, and this change already closed one part of it (`runs/land-step.md`)
- [x] D3 (approver round 1, look): `status`'s section names change for every host. `■ Open changes`, `■ Shipped`, `■ Ready to close` and `■ What needs me` become `■ Planned`, `■ Designing`, `■ Building`, `■ Ready`, `■ Landing` and `■ Needs you`. REFERENCE.md documents these sections, so they are a published interface: any host script that parses the old headings would break. The plugin's own readers were updated, and `test_nothing_names_a_retired_status_section` passes. The person should confirm this break is meant, as the intent implies. → decided: seen
