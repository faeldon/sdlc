VERDICT: PASS

The kept change is done. The `ESCALATE` chip is no longer drawn on a card whose stage is past `test` in the live form. At `shipped` or `dropped` it reads `was ESCALATE`, which doesn't say the card waits on the person. The chip itself (board.html:253–255) is live only at `test`, and the escalation flag at line 250 is gated to `test` too. Nothing else in the diff needs a change for this round.

## Notes

- Nit: `D3` in `decisions.md` is still unchecked (`[ ]`, the default I'd assume). The code follows it, so it's only a bookkeeping item for the person to tick or answer.
- The browser behaviour is pinned only by the grep checks in `checks.md`, since the page has no test runner. Those checks would catch a revert to the ungated lines, but not a rendering mistake inside the new expression. A person opening the page with an escalated shipped change and an escalated `test` change would settle that quickly.
- Done well: the rework took the second option the reviewer offered (a past-tense label) rather than dropping history, and the `column()` and `next_action()` gates in `board.py` match the chip and flag gates, so the card and its column agree.

## Commands run

- `uv run --group dev pytest -q -p no:cacheprovider tests/test_board.py`: 42 passed.
- The chip grep check from `checks.md` (the one for "live only at test"): passes.
- Read the `stage` field emitted per card in `board.py` (line 150), which the new html gates depend on.
