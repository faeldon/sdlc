# Findings

> What a change's review found, one `## ` section a finding, committed with the change.
> `/sdlc:ship` writes it after every review, and the factory's `carry` writes its agents' findings
> into it; `By:` names who raised one: `fresh` for ship's fresh-context reviewer, a factory role
> (`code`, `test`, …) for an agent, and no line on ship's own. A rerun keeps each id, marks one the
> diff no longer shows `fixed`, and never raises again one the person answered `wrong`,
> `intentional` or `minor`; an agent's `wrong` is its verifier's, never the person's, and the same
> fault worded differently is one more. `sdlc.py` reads each heading and its `Evidence:`, `Class:`,
> `Disposition:`, `Reason:`, `By:` and `Fix:` lines, counts ship's own alone into the
> `Sdlc-Findings` trailer (its `agents=` says how many it left out), words ship's question from
> the ones proposed `fix`, and `ship` refuses while one is still `open` or `fix`. On a diff that
> touches a sensitive path, this note also says `Fresh review: ran`, or `Fresh review: skipped,
> <why>`.

## F1. [important] [correctness] `trapTab()` builds its focus cycle from `FOCUSABLE`, which matches `button:not([disabled])` and does not exclude `[hidden]`.

scripts/board.html:626: `trapTab()` builds its focus cycle from `FOCUSABLE`, which matches `button:not([disabled])` and does not exclude `[hidden]`. The Raw button is hidden for every file that isn't `.md`, and for the "no file yet" note, but it still matches. It is the first node in the drawer's DOM order (it sits in `.d-head` before `#d-close`), so it becomes `first`. Focus then breaks in two ways. Tab on the last node calls `first.focus()` on a `display:none` element, which does nothing, so focus stays stuck on the last node. Shift-Tab from the first visible node is not caught by the trap, so focus leaves the `aria-modal` drawer. The spec's constraint says the focus trap must still work, and before this change `first` was `#d-close`, so this is a regression. Fix: exclude hidden nodes, for example `const FOCUSABLE = 'a[href], button:not([disabled]):not([hidden]), [tabindex]:not([tabindex="-1"])';`, or filter `!n.hidden` in `trapTab()`. Add a test in the style of `test_only_a_markdown_file_is_rendered` that asserts the trap's selector excludes hidden nodes.

Evidence: scripts/board.html:626
Class: code review, round 1
Disposition: fixed
By: code

## F2. [nit] [correctness] scripts/board.html (the comment branch in `mdBlocks()`): a line like `<!-- note --> more text` drops the text after `-->`, because the whole line is skipped.

scripts/board.html (the comment branch in `mdBlocks()`): a line like `<!-- note --> more text` drops the text after `-->`, because the whole line is skipped. Keep the remainder after `-->` as a paragraph.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F3. [nit] [correctness] scripts/board.html (`renderMarkdown()`): a file that starts with `---` and has any later `---` line reads everything up to it as frontmatter.

scripts/board.html (`renderMarkdown()`): a file that starts with `---` and has any later `---` line reads everything up to it as frontmatter. A file that opens with a horizontal rule is rare, but a check that the closing `---` follows a key-like line would be safer.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F4. [nit] [correctness] scripts/board.html (`mdInline()`): `![alt](https://…)` renders as a link to the image URL.

scripts/board.html (`mdInline()`): `![alt](https://…)` renders as a link to the image URL. `![alt](x.png)` shows as the alt text. Both are acceptable for this scope.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F5. [important] [correctness] scripts/board.html:338 and :361: a fenced code block or table wider than the drawer scrolls only with a pointer in some browsers (Safari does not make an overflowing box a tab stop, and notes.md flags the same gap), so a keyboard person can't reach the cut-off part of a long line or a wide table.

scripts/board.html:338 and :361: a fenced code block or table wider than the drawer scrolls only with a pointer in some browsers (Safari does not make an overflowing box a tab stop, and notes.md flags the same gap), so a keyboard person can't reach the cut-off part of a long line or a wide table. Give each `pre.md-code` and each `.md-table` `tabindex="0"` and a name (`role="region"` with an `aria-label` such as "code" or "table"), so the box takes focus and can be scrolled from the keyboard. The existing `:focus-visible` outline style on `.doc` can be reused.

Evidence: reviews/round-1/ux.md
Class: ux review, round 1
Disposition: fixed
By: ux

## F6. [nit] [correctness] the focus outline for the two new boxes is a sibling rule rather than a reuse of `.doc:focus-visible` (line 127).

scripts/board.html:159: the focus outline for the two new boxes is a sibling rule rather than a reuse of `.doc:focus-visible` (line 127). The rules match, so this is a style choice and nothing needs to change.

Evidence: scripts/board.html:159
Class: code review, round 2
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F7. [important] [correctness] a `.md` file with no text (`doc.text` is `""`) draws a blank pane, because `??` keeps the empty string and the markdown branch renders an empty `div`.

scripts/board.html:570: a `.md` file with no text (`doc.text` is `""`) draws a blank pane, because `??` keeps the empty string and the markdown branch renders an empty `div`. The drawer looks broken. Say the file is empty, for example "This file is empty." in the same note style as "This folder holds no file yet."

Evidence: scripts/board.html:570
Class: ux review, round 2
Disposition: recorded
By: ux

## F8. [pre-existing] [correctness] `show()` assigns `doc` when its fetch resolves, whichever file was asked for last.

scripts/board.html:573-585: `show()` assigns `doc` when its fetch resolves, whichever file was asked for last. If two files are clicked quickly and the older response arrives second, the pane shows the older file while the list highlights the newer one. Filed for later, not reworked here.

Evidence: scripts/board.html:573-585
Class: ux review, round 2
Disposition: recorded
By: ux
