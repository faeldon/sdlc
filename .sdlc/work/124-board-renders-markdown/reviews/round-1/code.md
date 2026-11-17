VERDICT: CHANGES

- CHANGE: [correctness] scripts/board.html:626: `trapTab()` builds its focus cycle from `FOCUSABLE`, which matches `button:not([disabled])` and does not exclude `[hidden]`. The Raw button is hidden for every file that isn't `.md`, and for the "no file yet" note, but it still matches. It is the first node in the drawer's DOM order (it sits in `.d-head` before `#d-close`), so it becomes `first`. Focus then breaks in two ways. Tab on the last node calls `first.focus()` on a `display:none` element, which does nothing, so focus stays stuck on the last node. Shift-Tab from the first visible node is not caught by the trap, so focus leaves the `aria-modal` drawer. The spec's constraint says the focus trap must still work, and before this change `first` was `#d-close`, so this is a regression. Fix: exclude hidden nodes, for example `const FOCUSABLE = 'a[href], button:not([disabled]):not([hidden]), [tabindex]:not([tabindex="-1"])';`, or filter `!n.hidden` in `trapTab()`. Add a test in the style of `test_only_a_markdown_file_is_rendered` that asserts the trap's selector excludes hidden nodes.

## Notes

Requirements walked against the code:
- Rendered `.md`: headings, paragraphs, lists (bullet, numbered, nested), task checkboxes (`disabled`, ticked from `[x]`), fences, inline code, bold, italic, links and blockquotes are all in `renderMarkdown()` and covered by `test_the_drawer_renders_markdown_as_nodes`.
- Other files: `paint()` keeps the `<pre>` for anything not ending `.md`, covered by `test_only_a_markdown_file_is_rendered`.
- Hostile input: `test_markdown_holding_markup_shows_it_as_text` covers `<script>`, `<img onerror>` and `javascript:`, `data:` and absolute-path links. Internal links only ever become `data-path` on an `href="#"` anchor, so a scheme can never reach `href`. I traced `mdResolve()` for `..` escapes and it refuses them.
- No new dependency and no CDN. `board.py` is untouched.

Contract and context: the page still builds every node through `h()` with text nodes and no HTML strings. The spec says `createElement` and `textContent`, and the code uses `createTextNode` through `h()`, which is equally safe. The REFERENCE.md edit is accurate. Nothing in `AGENTS.md` or `CLAUDE.md` describes the drawer, and nothing a future session needs is missing, so there is no `[context]` CHANGE.

Cost: `renderMarkdown()` is linear, with no unbounded loops. I checked that every `mdBlocks()` and `mdList()` branch advances `i`.

Nits (not counted in the verdict):
- NIT: scripts/board.html (the comment branch in `mdBlocks()`): a line like `<!-- note --> more text` drops the text after `-->`, because the whole line is skipped. Keep the remainder after `-->` as a paragraph.
- NIT: scripts/board.html (`renderMarkdown()`): a file that starts with `---` and has any later `---` line reads everything up to it as frontmatter. A file that opens with a horizontal rule is rare, but a check that the closing `---` follows a key-like line would be safer.
- NIT: scripts/board.html (`mdInline()`): `![alt](https://…)` renders as a link to the image URL. `![alt](x.png)` shows as the alt text. Both are acceptable for this scope.

The `show()` fetch race in `notes.md` is real and older than this change, as the builder says. I did not raise it as a CHANGE. The builder's `decisions.md` defaults D1–D4 are reasonable. D5 is a real trade-off against the spec's Approach, which names the ui screenshots, so the person should settle it. I have no CHANGE for it.

Tests and commands I ran:
- `uv run --group dev pytest -q -p no:cacheprovider tests/test_board.py`: 137 passed, 13 skipped (the skips are the `needs_node` tests and others marked by the module; node v26.13.0 is present, so the node-backed markdown tests ran).
- `ruff check` and `ruff format --check` on `tests/test_board.py`: clean.

I did not run the page in a browser. The focus-trap finding comes from reading `trapTab()`, `FOCUSABLE` and the `[hidden] { display:none !important }` rule at line 166, which means the button is unfocusable but still matches the selector. A short browser check of Tab and Shift-Tab on a non-`.md` file would confirm it before the rework.
