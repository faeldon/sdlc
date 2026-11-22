VERDICT: PASS

The two edits the person asked for are in `docs/REFERENCE.md` and match the code.

- **`status` line, around line 657:** a `mend` stop being mended reads `mending`, with no `⚠` lines, and its `→` line is `the factory is mending the <role>: wait for it`. This is the text `sdlc.py` prints at line 11003. The 3-hour timeout matches `AGENT_TIMEOUT = 3 * 3600` in `factory_records.py` and `factory.py`.
- **Needs-you list, around line 674:** the `stopped: mending the <role> since HH:MM with no reply: rerun /sdlc-factory:build NNN if no session runs it` text matches `sdlc.py` line 5211. The `HH:MM` is `since[11:16]`.

## Notes
- NIT: docs/REFERENCE.md:~678: the new clause lengthens the line that continues `parked past its deadline: free <resource>`, which now runs well past the file's wrap width. Re-wrap it. {docs S low}
- NIT: docs/REFERENCE.md:~658: the board's own `→` text is `the factory is mending the <role>: wait for it, or …` (`board.py:748`), longer than the `status` text this line quotes. The line is about `status`, so this holds. A word saying the board adds more would remove any doubt. {docs S low}
- Done well: both new texts are exact quotes of what the script prints, and the timeout is named as the agent's, not a number invented in the doc.
- I read `docs/REFERENCE.md` (the diff and the lines around it) and `land-2.md`. I ran `grep` on `scripts/sdlc.py`, `scripts/board.py`, `scripts/factory_records.py` and `plugins/factory/scripts/factory.py` to check each text.
