VERDICT: PASS

The kept round-1 change is done. `AGENTS.md:195` now reads "Ship, the factory's `carry`, and its `land --close` write `findings.md`, and `sdlc.py` only reads it (`findings_entries()`)", which matches the wording asked for and matches the code: `cmd_land_close()` calls `write_findings()` before `_record_move()` and `_amend_record()`. The rewrapped paragraph is still a true statement of the repo's invariants. Nothing else in the rework touches a reviewed path, and no context doc in `[docs] context` now says something false.

## Notes

- NIT: templates/findings.md:4: its note says "the factory's `carry` writes its agents' findings into it", which is still true but no longer names the landing. Adding "and its `land --close` its landing's rounds" would match REFERENCE.md. The template isn't a context doc, so this is optional, and a `templates/` edit needs `sdlc.py record` (the round-1 notes.md line already covers it).
- Done well: the rework is prose only, and it names every writer the code now has, with `sdlc.py` kept as reader only, as the invariant says.
- Tests run: none. I'm read-only here, so I checked the diff, the line widths of the reworked paragraph (all under 100 columns), and the code path behind the new sentence. The builder's report says `./check.sh` passed (2337 passed, 13 skipped). I haven't rerun it, and I haven't checked `claude plugin validate`.
