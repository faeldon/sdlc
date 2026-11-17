- KEPT: code: C1: scripts/board.html:625: FOCUSABLE doesn't exclude `[hidden]`, so the hidden Raw button (first in DOM order) becomes `first` in the focus trap, and focus escapes or sticks
- KEPT: ux: C2: scripts/board.html:338: `pre.md-code` and `.md-table` scroll sideways with `overflow-x: auto` but have no `tabindex` or name, so a keyboard person in browsers that don't focus scrollers can't reach cut-off content

## Notes
I ran no tests and only read the code.
- C1: line 563 sets `$("d-raw").hidden = !md`, and the Raw button is the first button in the drawer head. The selector at line 625 has no `:not([hidden])`. The defect is there as described.
- C2: lines 338 and 361 create the scrollers with no `tabindex`, and the CSS at lines 150–158 shows they overflow. `notes.md` lines 6–7 already flag the gap, so it is a real accessibility gap and not a matter of taste.
