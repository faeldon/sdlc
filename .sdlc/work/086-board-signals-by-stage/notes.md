# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

- [x] pre-existing: scripts/board.py:580-587 (`next_action`): a change with a file that won't read sits in Needs you at a closed stage, but its next line still says `/sdlc:close NNN`, because `next_action` returns before it looks at `problems` unless the stage is `None`. The card says two things at once. It predates this change, so it is filed here and not reworked. → dropped: filed as bug 2026-11-17-23
- [x] pre-existing: `scripts/board.html:44`: below 760px the seven columns stack in stage order, so Needs you, the one column that waits on the person, sits after every other column. The 390px screenshot shows only Plan, Design and the start of Build. This may predate this change; if so it is for later. A possible fix is to put Needs you first at narrow widths. → dropped: filed as bug 2026-11-17-24
- [x] pre-existing: `scripts/board.html:113-124` and the `aria-modal` drawer: Escape closes it and focus returns to the card, but Tab can move into the page behind the scrim. No focus trap is in the script. → dropped: filed as bug 2026-11-17-25
