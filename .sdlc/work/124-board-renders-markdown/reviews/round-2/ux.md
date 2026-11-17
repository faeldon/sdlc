VERDICT: CHANGES

- CHANGE: scripts/board.html:570: a `.md` file with no text (`doc.text` is `""`) draws a blank pane, because `??` keeps the empty string and the markdown branch renders an empty `div`. The drawer looks broken. Say the file is empty, for example "This file is empty." in the same note style as "This folder holds no file yet."
- PREEXISTING: scripts/board.html:573-585: `show()` assigns `doc` when its fetch resolves, whichever file was asked for last. If two files are clicked quickly and the older response arrives second, the pane shows the older file while the list highlights the newer one. Filed for later, not reworked here.

## Notes

**Read:** both screenshots (1280×800 and 390×844), which show the board only, not the drawer (D5 keeps it that way). `intent.md`, and `decisions.md` (D1–D5, all open defaults, none answered). `spec.md` does not exist in this folder, so I judged the flow from intent's Approach and Outcome at Tier 1. `scripts/board.html` in full. I did not run a browser, so the drawer at 390px and its code and table scrolling are read from the CSS and markup, not seen.

**Kept changes, checked:**
- Keyboard, code: `trapTab()` now drops hidden nodes (line 631). The hidden Raw button is skipped, Tab wraps from the last visible node to the first, and Shift-Tab from the first stays inside the drawer. The focus cycle now holds.
- Keyboard, ux: `pre.md-code` (line 340) and `.md-table` (line 364) each carry `tabindex="0"`, `role="region"` and an `aria-label`. The `:focus-visible` outline is at line 159. A keyboard person can reach and scroll both.

**States:**
- Loading: a bare "…" in the pane (line 570). It works, but a slow file can look stuck. Smaller finding below.
- No file: "This folder holds no file yet." Says what happened, not how to start.
- Unreadable file: "can't be read (404)." Says what happened and gives a status code, with no next step.
- Empty file: blank (the CHANGE above).

**Smaller findings:**
- Loading shows only "…" (line 570). Use "Loading…" so a slow file doesn't look stuck.
- The "Raw" toggle is terse. "Show raw text" would say what pressing it does, and it is the only control in the drawer's header with no name beyond one word.
- The unreadable-file note (line 580) should add a next step, such as "Pick another file from the list."
- Every rendered table is named "table" and every code block "code". A screen reader user hearing several of each can't tell them apart. Consider a heading or a caption-based name. Not a blocker.

**Done well:** the drawer's own states are deliberate. Its `aria-modal` focus trap and Escape both work, and focus returns to the card that opened it. Task checkboxes are `disabled`, so they are read as state and never reachable as controls. Links are real anchors when followed and plain words otherwise, with the refused target in a tooltip.
