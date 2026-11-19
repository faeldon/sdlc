# Decisions

- [x] D1 (builder round 1, default): Should the read-only list also check a value glued to a short option (`grep -f/etc/passwd`)? Going ahead with yes unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: check it — closes a way to read outside the checkout that the spec's rules leave open; a harmless glued value pays the same path check
  - OPTION: the spec's rules only — exactly as written; `-f/abs/path` slips past the list and only the approver would catch it
  - WHY: R4 and R8 rest on the list refusing reads outside the checkout
- [x] D2 (builder round 1, default): Should R17's evidence lines keep naming a long command in full, even past 160 characters? Going ahead with yes unless told otherwise. → settled by the approver: R17 is about `_not_already_made()`'s own refusal lines, and those are all short. Its case loop in `tests/test_land.py` passes. The only lines that can run past 160 characters are the person's own command, echoed by `read_evidence()`, which the build loop shares. Truncating them would hide the command the refusal is about. Code round 1 agreed with the default, and test round 1 accepted R17's assertion as written.
  - OPTION: keep them whole — the refusal shows the exact command; a very long command makes a long line
  - OPTION: truncate them — every line stays under 160; the person loses part of the command they need to see
  - WHY: those lines come from `read_evidence()`, which the build loop shares; R17's own lines are all short
- [x] D3 (builder round 1, default): Should the `AGENTS.md` factory paragraph be edited as the spec's *Contracts touched* section words it? Going ahead with yes unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: as the spec words it — the map matches the code; it changes the "host command only behind a prompt" contract for anyone reading the map
  - OPTION: hold the edit for separate approval — the contract change gets its own yes; the map is wrong about the code until it lands
  - WHY: the spec says that edit needs explicit approval, and approving the spec may or may not have been meant to cover it
