The board's drawer now shows a `.md` file as a formatted document instead of raw text. Every other file still shows in the `<pre>` as before. The full gate passes (2319 passed, 13 skipped) and `sdlc.py check` reports no problems. The work is uncommitted, waiting for `/sdlc:ship`.

**What I built** (in `scripts/board.html`). It's Tier 1, but the Approach touches several files, so I wrote `plan.md` first.
- **The renderer.** `renderMarkdown(text, ctx)` handles frontmatter, headings, paragraphs, bullet, numbered and nested lists, checkboxes, fenced code, quotes, rules, pipe tables, and inline code, bold, italic, strikethrough and links. Every node is made with the existing `h()`, so nothing in a file is ever parsed as HTML. HTML comments are hidden. `snake_case` words are left alone rather than turned into italics.
- **Links.** `http(s):` and `mailto:` links open in a new tab. A relative link to another file in the change's folder opens that file in the drawer. Any other link (`javascript:`, `data:`, absolute paths, paths leading out of the folder, files the change doesn't have) shows as plain words with no link.
- **Drawer wiring.** A new `paint()` renders only paths ending in `.md`. There's a `Raw` toggle (`#d-raw`) in the drawer header, shown only for markdown files. Clicking an in-drawer link moves focus to the scrolling pane.
- **Styling.** It uses the existing colour variables, so light and dark both work. Code blocks and tables scroll sideways inside themselves.
- **Other files.** The fixture review `005-draft-sharing/reviews/round-1/code.md` now has a checklist, a table, code and links; its first line is still `VERDICT: PASS`. I added one clause to `docs/REFERENCE.md` under *The board*.

**Tests added** to `tests/test_board.py`. Each was run and seen to fail before the code existed.
- `test_the_drawer_renders_markdown_as_nodes` runs the page's real markdown code under `node`, using a small stand-in for the browser. It checks that every construct comes out as the right element and that links resolve as described.
- `test_markdown_holding_markup_shows_it_as_text` feeds it `<script>`, `<img onerror>`, `javascript:`, `JavaScript:`, `data:`, `../../../` and `/abs` links. The tags come out as text, no link is created, and no element gets an `on*`, `href`, `src` or `style` attribute.
- `test_only_a_markdown_file_is_rendered` checks the page source: only `.md` is rendered, other files go to `<pre>`, the toggle is a button inside the drawer, and code blocks and tables scroll inside themselves.

The two `node` tests are skipped wherever `node` isn't installed, so they don't run in CI's Windows job.

**Browser check (by hand, not part of the suite).** I served the fixture board and drove it in Chromium at 1280px in light mode and 390px in dark mode. At both sizes:
- The page never got wider than the window, and the code block scrolled inside itself.
- Checkboxes were ticked or not as written, and all were disabled.
- The `spec.md` link opened that file in the drawer.
- The Raw toggle switched views.
- Focus stayed inside the drawer through 40 Tabs, and Escape closed it.
- There were no script errors.

**`plan.md`** was updated after building to say that a clicked link moves focus to the pane, which now has `id="d-pane"`.

**Left in `notes.md`**, both unticked:
- `show()` has no guard when two file loads overlap, so a slow reply can paint over a later pick. This was already true before this change.
- A code block or table that scrolls sideways can't be reached with Tab on its own in every browser.

**Decisions** (the intent's open questions; I built on each default):
- DECISION: [default] Frontmatter shows as a plain block of its own lines (dimmed, set apart from the document), not a key/value table. Going ahead unless told otherwise. Reason: it's exact, and lists in frontmatter would break a table.
- DECISION: [default] Links: a link to another file in the change's folder opens it in the drawer; `http(s):` and `mailto:` open a new tab with `rel="noopener noreferrer"`; every other link shows as its words only, with the target in a tooltip. Going ahead unless told otherwise.
- DECISION: [default] Add a `Raw` toggle (a button with `aria-pressed`, shown for `.md` only) that stays as set while the drawer is open. Going ahead unless told otherwise. Reason: copying an exact line, and seeing hidden comments.
- DECISION: [default] Coverage: pipe tables and nested lists are rendered; HTML comments are hidden (the Raw view shows them); raw HTML is shown as text. Going ahead unless told otherwise.
- DECISION: [default] The UI reviewers' screenshots show the board only, since the shot command never opens the drawer, so the rendered fixture review is for anyone who opens the drawer. I'm not adding a deep link to an open drawer, which would also mean changing `.sdlc/factory.toml`. Going ahead unless told otherwise. Reason: the intent didn't ask for it.

## Evidence

$ ./check.sh   (with pipefail, filtered to its summary lines)
All checks passed!
246 files already formatted
2319 passed, 13 skipped in 65.81s (0:01:05)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_board.py -k "markdown"   (before the renderer, red)
FAILED tests/test_board.py::test_the_drawer_renders_markdown_as_nodes - Asser...
FAILED tests/test_board.py::test_markdown_holding_markup_shows_it_as_text - A...
FAILED tests/test_board.py::test_only_a_markdown_file_is_rendered - Assertion...
3 failed, 147 deselected in 0.43s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py -k "markdown"
3 passed, 147 deselected in 0.15s
exit: 0

$ uv run --group dev pytest -q tests/test_board.py -rs
137 passed, 13 skipped in 28.90s
exit: 0

$ uv run --quiet --script scripts/sdlc.py check
■ Problems: 0
    none ✅
exit: 0
