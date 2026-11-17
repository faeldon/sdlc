DECISION: ESCALATE

**Why.** Both review rounds were used up and one change is still open: the ux reviewer's empty-file pane, which the verifier kept. Under the run's rules that alone means ESCALATE. Separately, all five decisions in `decisions.md` (D1–D5) are still unticked defaults that nobody has confirmed. The code looks sound: every outcome in the intent has a test, the gate passed (2320 passed), and both round-1 changes were fixed and checked. But no reviewer has actually seen the rendered drawer, because the screenshots never open it.

## Reconsider the approach

No finding came back from one round to the next. Round 1 kept two changes: the hidden Raw button broke the focus trap, and wide code blocks and tables couldn't be reached by keyboard. Round 2 confirmed both fixed and raised a new, smaller one: an empty `.md` file draws a blank pane. The verifier added that an empty non-`.md` file gives a blank `<pre>` too. So the loop was converging, and the code approach (a markdown-to-DOM renderer built on `h()`, used only for `.md` files) does not need to change.

What did come back every round is a gap in how the change was checked. The intent's Approach expected the ui reviewers' screenshots to show the fixture rendered, and they never did. Both ui rounds passed on reading the CSS alone, and both said so. Their unseen items are the h1 at 20px outranking the drawer's 15px title, the checkbox hung with a negative margin, the Raw button wrapping at 390px, and the table and code boxes at 390px. D5 chose not to fix the screenshot step. Another build round would not close that gap. A person opening the drawer would, and so would a later change that lets the screenshot step open the drawer. Neither the spec nor the plan needs to change.

## Open items
- ux (round 2, kept): `scripts/board.html:570`: an empty `.md` file draws a blank pane. Show a note such as "This file is empty." An empty non-`.md` file also gives a blank `<pre>`.

## Decisions to confirm
- D1: frontmatter shows as a dimmed plain block of its own lines, not a key/value table.
- D2: a link to another file in the change opens it in the drawer. `http(s):` and `mailto:` links open a new tab with `rel="noopener noreferrer"`. Every other link shows as plain words, with the target in a tooltip.
- D3: a `Raw` toggle button with `aria-pressed`, shown for `.md` files only, that keeps its setting while the drawer is open.
- D4: pipe tables and nested lists are rendered, HTML comments are hidden (the Raw view shows them), and raw HTML shows as text.
- D5: the screenshots show the board only, with no deep link to an open drawer and no change to `.sdlc/factory.toml`. So no reviewer has seen the rendering.

## For the person at ship
1. Open the fixture board and open `005-draft-sharing/reviews/round-1/code.md` in the drawer, at 1280px and at 390px. Check:
   - the h1 size against the drawer title
   - checkbox alignment
   - the Raw button wrapping
   - table and code boxes scrolling inside themselves
   - Tab and Shift-Tab staying inside the drawer on a non-`.md` file.
2. In `scripts/board.html`:
   - `mdResolve()` and `mdLink()`: only `http(s):` and `mailto:` should ever reach an `href`, and `..` should never escape the change's folder.
   - The `[hidden]` filter in `trapTab()` (around line 631).
   - The empty-text branch of `paint()` (around line 570).
3. Confirm the diff has no `innerHTML` or similar HTML sink, which the existing sink test pins.

- IMPACT: minor — the board's drawer now shows a change's markdown rendered, with a Raw toggle and links between the change's files that open in the drawer, so a person can read reviews and decisions in a way they couldn't before. No interface, config or file format changed.

## Undone items
- UNDONE: `show()` has no guard against two fetches overlapping: a slow reply for the file picked first can paint over the one picked after it. Older than this change; a request counter would settle it. → dropped: the same fault as the `pre-existing:` item below, which is filed as a bug
- UNDONE: ux: scripts/board.html:570: a `.md` file with no text (`doc.text` is `""`) draws a blank pane, because `??` keeps the empty string and the markdown branch renders an empty `div`. The drawer looks broken. Say the file is empty, for example "This file is empty." in the same note style as "This folder holds no file yet." → seed: The board's drawer says a file is empty instead of showing a blank pane
- UNDONE: pre-existing: scripts/board.html:573-585: `show()` assigns `doc` when its fetch resolves, whichever file was asked for last. If two files are clicked quickly and the older response arrives second, the pane shows the older file while the list highlights the newer one. Filed for later, not reworked here. → bug: med: scripts/board.html: A slow fetch in the board's drawer can show an older file under a newer file's highlight
