The code shows the defect: the key includes the raw seconds, and `#board` is `aria-live`.

- **KEPT: ux: C1: scripts/board.html:293: the render key includes raw `touched_ago` seconds, so every 2s poll rebuilds all cards, which drops keyboard focus. `#board` is `aria-live`, so a screen reader hears the whole board each poll. Key on the shown text and move `aria-live` to `#status`, with a test.**

## Notes
- I only read `board.html`, `board.py`, `test_board.py` and `decisions.md`. I ran nothing.
- `st.changes` is serialised whole, and `touched_ago` is `round(now - touched)`. It changes every poll for any change with a touch time. `ago()` shows only minutes, hours or days. `aria-live="polite"` sits on `main#board` at line 137, and `#status` has none.
- The "Settled" line in the prompt (the phone-width DOM order) is context, not a numbered change this round. The code already has `columnOrder()` and a `matchMedia` check, so I gave it no line. Tell me if it was meant as a separate change.
