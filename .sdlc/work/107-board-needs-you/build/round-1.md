The board and `status` now both say what each change needs from you. Answered escalations move to Ready to ship, and a poll no longer takes keyboard focus off a card. The full gate passes (2091 tests), as do the 288 tests Windows CI runs. Nothing is committed; it's all left for `/sdlc:ship`.

**Slices built** (each test written and seen failing first)

1. **One set of rules, in `sdlc.py`.** `needs_of(rec)` and `answered(rec)` decide what a change needs from fields already read, and read nothing themselves (R1–R5, R7, R8). The order is: every problem as `fix: …`; nothing more once a change is shipped or dropped; at `build`, `stopped: <way>` then `decide D<n>`; for an ESCALATE at `test`, `decide D<n>`, `confirm N default(s)`, `reconsider the approach`, and `read the escalation` when the ledger is empty; at `plan`, `approve its spec` for a Tier 2 whose spec is written.
2. **The board's columns.** `_factory()` now also reads:
   - whether `decision.md` has a Reconsider section (via a `RECONSIDER` copy of `factory.py`'s, pinned by a test);
   - how many decision lines the ledger holds;
   - an open `- [ ]` line the ledger can't read, which becomes a problem (R6).

   `_entry()` sets `needs` and `answered`, and `column()` puts a card in Needs you exactly when `needs` is non-empty. An escalation with every line ticked goes to Ready to ship (R5, R9).
3. **`status`.** A new `factory_reading(folder)` reads the same files, and never raises. Each open record gains only `needs` and `answered`. The output now ends with `■ What needs me`, after `■ Problems`, listing each waiting change or `nothing` (R11, R12). The text for an unreadable ledger line is one shared constant, so the board and `status` word it the same way.
4. **The page.**
   - Cards show a `needs you: a · b` line and an `escalated: answered` badge, built with `h()` (R10).
   - The "approver escalated it to you" flag is hidden once the escalation is answered, which the spec didn't spell out.
   - The render key stores times as the page shows them, so a poll only rebuilds when something visible changed (bug 2026-11-17-50, R13).
   - After a rebuild, focus goes back to the card that had it, unless the drawer is open (R14).
   - `aria-live` is now only on `#status`, which reads `live`, `live · N need(s) you`, or that the board isn't answering, and only changes when its words do. The poll time moved to a new `#polled` span (R15).
   - The script passes `node --check`.
5. **Docs (R16).** `docs/REFERENCE.md` describes the needs texts, the answered badge, `■ What needs me`, and how the page polls and announces. `skills/status/SKILL.md` names the new section, in prose only.

**Tests added**
- `tests/test_sdlc.py`: six tests driving `needs_of` from plain records, one of which fails if it touches the file system, `open` or a subprocess.
- `tests/test_board.py`:
  - on the board: the answered escalation, the unreadable ledger line, a written spec at `plan`;
  - for `status`: the new section is last and agrees with the board on the same folders, it says `nothing` when nothing waits, and records only gain keys;
  - on the page: four tests reading its script for R10, R13, R14 and R15;
  - existing tests updated: change 022 (an escalation with an empty ledger) now stays in Needs you as `read the escalation`, a new change 028 with a ticked ledger lands in Ready to ship, the unreadable-file test also checks its `fix:` lines, the render-key check follows the new key, and the pinned-copy test gains `RECONSIDER`.
- `tests/test_metrics.py`: pins `FACTORY_RECONSIDER` to `factory.RECONSIDER`.

**`plan.md`:** written before any code, and the build followed its five slices. The one correction afterwards was to its wording, to say the unreadable-line text is shared. The `status` tests sit in `tests/test_board.py`, as the plan said, so they can compare against the board on the same folders.

**Left in `notes.md`:**
- A stop record that won't read still shows differently in the two places. The board treats it as a problem (`fix: runs/stopped.md …`), as an earlier change pinned; `status` shows `stopped: read runs/stopped.md`. Both put it in front of you.
- As the spec asked, the next step a card names is unchanged. So an escalation that still needs `decide D2` shows `/sdlc:ship, or /sdlc-factory:land …` as its next step, beside its `needs you:` line. A next step that follows the needs would read better.

The manual checks (focus staying put across several polls, VoiceOver quiet between polls) still need doing by hand.

No decisions raised this round.

## Evidence

$ ./check.sh
All checks passed!
2091 passed, 9 skipped in 84.99s (0:01:24)
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q -m portable -n auto
288 passed, 9 skipped in 17.67s
exit: 0

$ uv run --group dev pytest -q tests/test_board.py -n auto
115 passed, 9 skipped in 3.49s
exit: 0

$ node --check /tmp/b107.js
parses
exit: 0
