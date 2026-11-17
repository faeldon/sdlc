---
id: 124
slug: board-renders-markdown
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 124 — The board renders a change's markdown files · plan

> Written after reading `scripts/board.html` (the drawer: `show()`, `openDrawer()`, `trapTab()`,
> `h()`), `tests/test_board.py`'s page tests (`_page_parts()`, the sink checks, the focus trap)
> and the board fixture. Tier 1: the intent's Approach is the spec; its Outcome bullets are what
> the tests prove.

## Files to change

- `scripts/board.html`: a markdown section between `// ---- markdown` and `// ---- end markdown`
  holding `mdResolve()`, `mdLink()`, `mdInline()`, `mdList()` and `renderMarkdown(text, ctx)`,
  every node made by the existing `h()` (so `createElement` and text nodes, nothing parsed as
  HTML). `show()` keeps the fetched text and calls a new `paint()`, which renders a `.md` path
  into a `div.md` and anything else into the `<pre>` as today. `#d-doc` becomes a `div` holding
  either. A `Raw` toggle (`#d-raw`, `aria-pressed`) in the drawer's head, shown for `.md` only. A
  click on a rendered link to another file of the change opens it in the drawer and moves focus
  to the scrolling pane (now `id="d-pane"`, since the clicked link is gone once it repaints). CSS for `.md`,
  through the existing colour variables, so light and dark both hold; fenced code and tables
  scroll inside themselves.
- `tests/test_board.py`: a test that runs the markdown section under `node` with a small stand-in
  DOM and reads back the tree; a source test that `show()`/`paint()` render only `.md`, that the
  toggle is a button in the drawer, and that code blocks and tables scroll inside themselves.
- `tests/fixtures/board/changes/005-draft-sharing/reviews/round-1/code.md`: a review body with
  headings, a list, a task list, code, a table and a link, for a person or reviewer opening the
  drawer on the fixture board. Its first line stays `VERDICT: PASS`.
- `docs/REFERENCE.md`, *The board*: one clause saying a markdown file shows rendered, with a raw
  toggle, and that nothing in it is parsed as HTML.

Reuse: `h()` for every node; `open.files` (the list the drawer already holds) to decide whether a
relative link names a file of the change; the drawer's `FOCUSABLE` trap, which already covers
`a[href]` and buttons inside `#drawer`, so rendered links and the toggle stay in the focus cycle.

## Work order

1. Red: the node-run test feeding `renderMarkdown` every construct plus `<script>`,
   `<img onerror>` and a `javascript:` link. Fails: no markdown section in the page.
2. Green: the markdown section (blocks, then inline, then links). Test passes; gate green.
3. Red: the source test for `show()`/`paint()`, the toggle and the CSS. Green: wire `show()`,
   `paint()`, the toggle, the in-drawer link click and the CSS. Gate green.
4. The fixture review and the REFERENCE.md clause.

## Tests

- Outcome 1 (constructs rendered): `test_the_drawer_renders_markdown_as_nodes` asserts headings,
  paragraphs, bullet, numbered and nested lists, disabled checkboxes ticked or not, fenced code,
  inline code, strong, em, links, quotes, a table and the frontmatter block.
- Outcome 2 (other files as before): `test_only_a_markdown_file_is_rendered` asserts `paint()`
  renders only a path ending `.md` and puts the rest in a `pre` by `h()`.
- Outcome 3 (nothing parsed as HTML): the existing sink checks
  (`test_the_page_is_self_contained_and_never_parses_data_as_html`), plus
  `test_markdown_holding_markup_shows_it_as_text`: `<script>`, `<img onerror>` reach the tree as
  text only, a `javascript:` link and a link outside the change become no `a` at all, and an
  outside `https:` link opens a new tab with `rel="noopener noreferrer"`.
- Outcome 4 (no dependency, no CDN): the existing self-contained check.
- Constraint (390px): `test_only_a_markdown_file_is_rendered` asserts the code block and table
  rules set `overflow-x: auto` and code keeps `white-space: pre`.
- Constraint (focus trap): the existing `test_the_open_drawer_keeps_tab_inside_it` still passes;
  the toggle is a `button` inside `#drawer`.

The node-run tests are skipped where no `node` is on the path; they are not `portable`.

## Rollback

`git revert` undoes all of it: the board writes nothing, and nothing outside the repo reads the
page.
