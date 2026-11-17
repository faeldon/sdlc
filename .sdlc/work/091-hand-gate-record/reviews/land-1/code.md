VERDICT: PASS

I found nothing in the rebased diff that needs rework. The change is unchanged in substance by the rebase. The two conflicts the builder resolved (`scripts/board.html` and `docs/REFERENCE.md`) keep both sides, as `land-1.md` says. They carry the base's `chip` badge and the reworded Needs-you text, and the change's gate badge and its Test rule.

## Notes

**Requirements walked:**
- R1–R7: `cmd_gate`, `_hand_paths`, `hand_build`, `_hand_placeholders` and `hand_gate` are all present.
- R8–R9: `_seen()` and `next_action()` in `scripts/board.py` implement both.
- R10–R11: the board's `gate` key and badge, and status's `· gate green` / `· gate red` mark.
- R12: `HAND_GATE_RE` in `scripts/metrics.py`.
- R13: `gate` is in `OWN_SCRIPT_CMDS` and in none of the lists the spec excludes it from.
- R14: the record is written with `newline="\n"` and `encoding="utf-8"`.
- R15: `docs/REFERENCE.md` documents the command and its readers.
- Each has a test in `tests/test_hand_gate.py` (16 tests), `tests/test_board.py` or `tests/test_metrics.py`.

**Done well:**
- The tree check and the hash share one walk.
- The check command comes from the base branch's config, never the checkout's.
- `hand_gate` never raises, and a missing or garbled record counts for nothing.
- Placeholders are applied before anything is written.

**Nits:**
- `_hand_paths` builds its excluded prefix from `work_rel(checkout)`, where `cmd_gate` uses `home`. `work_rel()` is probably the same string either way, so this is harmless.
- The `_seen()` and `print_status` code reads `gate["current"]` directly. This is safe because `hand_gate` always sets that key.

**Ran:**
- `pytest tests/test_hand_gate.py tests/test_board.py tests/test_metrics.py`: 184 passed.
- I did not rerun the full `./check.sh`. The builder's `land-1.md` records it passing on the rebased tree (1,952 tests).

I read the diff against `main` and ran no command that writes.
