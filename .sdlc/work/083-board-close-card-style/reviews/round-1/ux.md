VERDICT: PASS

No required changes. The drawer button and the card no longer share a class, so the card in Ready to close picks up the `.card` rules and nothing overrides them. The screenshots don't show a card in that column, so the visual fix is judged from the stylesheet, not from a picture.

## Notes

**Read:** both round-1 screenshots (1280×800 and 390×844), `intent.md` (Tier 1, so its Approach is the spec; there is no `spec.md`), and `scripts/board.html` in full, including the stylesheet, `card()`, `COLUMNS`, the drawer markup and its handlers. From `tests/test_board.py` I read the test names and the lines that touch `close` and the stylesheet (around lines 390–410). I had no shell in this session, so I could not run `git diff`. I judged the changed CSS from the current file, not from the before-and-after.

**Walked the change:**
- A card in Ready to close is a `button.card.close`. Only `.col.close .col-head h2` is scoped by the column key, so the card keeps the shared border, panel background, 10px 12px padding, 8px radius and inherited 14px type. Nothing styles `.card.close`.
- The drawer's × is `button.d-close`, which has its own rule (`font-size: 20px`, no background, no border). It no longer collides with the column key.
- The phone layout (`@media (max-width: 760px)`) is one column of full-width cards, and the drawer stacks its file list above the doc. A person can still reach and read a card there.
- The × has `aria-label="Close"`. Escape closes the drawer. Focus moves to × on open and back to the card on close. Cards are native buttons with a visible `:focus-visible` border.

**States:**
- The screenshots were taken with no change in Ready to close, so the column shows its `—` placeholder. That placeholder is the same for every empty column, and it is not this change's to fix.
- I could not see a populated Ready to close column, so I did not judge how a 081-style card looks in it beyond the CSS. The test change, not the screenshots, is what covers the regression.
- The loading and error states (`connecting…`, `the board isn't answering…`) are unchanged by this change.

**Smaller points:**
- Worth a glance by the builder: `.d-close` now sets `color`, `line-height`, `cursor` and `font: inherit`. If the old `.close` rule did not have those, the × will look slightly different. Confirm against the pre-change rule, since the intent says the × should look the same as today.
- The new test (`test_no_column_key_is_a_class_the_page_styles_on_its_own`) checks the keys against the stylesheet's selectors. It does not check the `.card` markup, so a future rule like `.card.close` written in a different form could slip past it. That is a test-coverage point, not a user-facing one.

**Works well:** the fix is the smallest one the intent could have taken. It renames the one class that collided, keeps `column: "close"` in `/state.json` and the `.col.close` heading colour, and adds a test that fails on the next clash.
