DECISION: ESCALATE

**Why.** All five round-1 reviewers (code, test, behaviour, ui, ux) gave `VERDICT: PASS`. The gate passed: `./check.sh` exited 0 with 2838 passed and 28 skipped. Each of R1–R12 has code and a test named for it. The decision is ESCALATE only because both open defaults are calls the spec itself left to the person. D1 builds against the intent's own wording, and D2 is a question of scope that the spec's Boundaries say to ask about first. The change also reshapes `status`'s documented output for every host, so a person should look before it lands.

**Open items**
- None. No round left a CHANGE open. The code reviewer's two NITs are recorded in `findings.md` as F1 and F2, with disposition `recorded`.

**Decisions to confirm**
- ESCALATED: D1: The intent's Outcome says `■ Needs you` "stays first", but the build prints it last. The spec defends last from the code, the board's order and the status skill. Even so, its "Left for you" and Alternatives rejected sections both say moving it "is the person's call". Only the person can say whether last overrides their own word.
- ESCALATED: D2: Whether `status` should also read the problems only the board reads (a reply with no VERDICT, a findings or step file that won't read) is a question of scope. The spec's Boundaries say "It asks first before closing the gap above", and the spec lists it under "Left for you". So no reviewer or approver can settle it.

**Every other reason I escalate for**
- ESCALATED: look: `status`'s section names change for every host. `■ Open changes`, `■ Shipped`, `■ Ready to close` and `■ What needs me` become `■ Planned`, `■ Designing`, `■ Building`, `■ Ready`, `■ Landing` and `■ Needs you`. REFERENCE.md documents these sections, so they are a published interface: any host script that parses the old headings would break. The plugin's own readers were updated, and `test_nothing_names_a_retired_status_section` passes. The person should confirm this break is meant, as the intent implies.

**For the person at ship**
- Start with `print_status()` and the new `_by_state()`, `_change_lines()` and `_close_line()` in `scripts/sdlc.py`. Then read the output itself, from `uv run --quiet --script scripts/sdlc.py status`. Check the six headings in order and that Needs you comes last (D1).
- Next, check that `column()`, `BY_STAGE`, `seen_stage()`, `touched_paths()` and `rebasing_branches()` moved from `board.py` unchanged. `in_flight` now comes from `factory_landing()` on both sides instead of the board's `progress`. That is the one change in meaning on the board, pinned by `test_the_board_and_status_read_a_landing_in_flight_alike`.
- `held_by_rebase()` (F1) walks the worktree list a second time. `_by_state()`'s fallback for a record with no `column` (F2) drops stages like `test`. Nothing reaches it today.
- The spec expected 151 under Designing. The builder explains it shows under Building because the change's stage is now `build`, which is correct.

- IMPACT: minor — `status` now groups work under the board's six states, so a person newly reads one vocabulary across `status` and the board. A host script that parsed the old headings would need updating, and if the person counts that as breaking, it should be `major`.

**Undone items**
- None. `notes.md` doesn't exist, and the builder reports adding nothing to it.

**How to recover**
- The prompt names no irreversible paths. If needed, `plan.md`'s Rollback (`git revert`) applies, since `status` writes nothing.
