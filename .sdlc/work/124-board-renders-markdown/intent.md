---
id: 124
slug: board-renders-markdown
tier: 1
impact: minor
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea:
depends_on:
serves: none
---

# 124 — The board renders a change's markdown files

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

"Render the markdown files in the dashboard when you click a change." Clicking a card on the board
opens a drawer listing the change's files, and the one picked is shown as raw text in a `<pre>`
(`scripts/board.html`, the drawer's `#d-doc` and `show()`). Nearly all of them are markdown
(`intent.md`, `spec.md`, `plan.md`, `decision.md`, `reviews/round-N/*.md`, `notes.md`), so headings
read as `##`, lists as `-`, checkboxes as `- [ ]`, emphasis as `**` and code as backticks, and long
lines wrap mid-sentence. A review round or a decision is what the drawer is opened to read, and it
is the hardest thing there to read.

## Outcome

- A `.md` file picked in the drawer shows rendered: headings, paragraphs, bullet and numbered
  lists, task checkboxes (shown ticked or not, never clickable), fenced code blocks, inline code,
  bold and italic, links and blockquotes.
- Every other file (`.files`, `.sessions`, `.jsonl` and the like) shows as today, in the `<pre>`.
- The renderer builds every node with `createElement` and `textContent`; nothing is parsed as HTML.
  `tests/test_board.py`'s sink checks still pass, and a test feeds the renderer a file holding
  `<script>`, `<img onerror>` and a `javascript:` link and finds them shown as text, or a link
  refused.
- No new dependency and no CDN: the page stays one self-contained file served from `127.0.0.1`.

## Affected

- **Area:** the board page.
- **Files & components:** `scripts/board.html` (the drawer's `show()`, a small markdown-to-DOM
  renderer and its CSS, light and dark); `tests/test_board.py`; a markdown file in the board's
  fixture under `tests/fixtures/board/changes`. `board.py` is untouched: `/file` already serves the
  text.
- **Downstream:** the person, in their browser. No skill, script or host parses the page.
  `scripts/board.html` is in `[ui] paths`, so a factory build adds the ui and ux reviewers.
- **Contracts:** AGENTS.md, *The board*: it writes nothing, serves `127.0.0.1` alone, and the page
  builds every node with `textContent`, never from a string of HTML.

## Constraints

- No string from a change's files is ever parsed as HTML.
- The drawer's focus trap and Escape-to-close still work; it is `aria-modal`, so the rendered
  document stays inside its focus cycle.
- At 390px wide, code blocks scroll inside themselves and never widen the page.

## Open questions

- Frontmatter (`---` … `---` atop `intent.md` and others): a small key/value table, or a plain
  block?
- Links: does a relative link to another file in the change's folder open it in the drawer, an
  outside link a new tab with `rel=noopener`, and `javascript:` and other schemes refused?
- A raw toggle, so a person can still see the exact text, to copy a line?
- How much markdown: tables (reviews sometimes use them), nested lists, HTML comments?

## Approach

A `renderMarkdown(text)` in `board.html` that walks the file's lines into block nodes (headings,
lists, fences, quotes, paragraphs), then a small inline pass splitting each block's text into text,
`code`, `strong`, `em` and `a` nodes. `show()` calls it when the path ends in `.md`, else keeps the
`<pre>`. Tests in `tests/test_board.py`, in its pattern of reading the page's source, plus a
fixture `.md` that the ui reviewers' screenshots show rendered. No open nits touch these paths.
