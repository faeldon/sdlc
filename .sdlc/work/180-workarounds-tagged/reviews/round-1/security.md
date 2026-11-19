VERDICT: PASS

## Notes

I found no security problems. This change records and counts things; it adds no new way for untrusted data to reach a shell, the network, or anything that deletes or publishes.

**Where untrusted data comes in, and what it can reach (STRIDE):**
- **Commit subjects and paths on the base branch, read by `retro`** (`_workarounds()`, `_log_blocks()`, `_restored()`). Every git call passes its arguments as a list through `sdlc._git`, never through a shell. Subjects are only compared with regexes and prefixes, and copied into the report's JSON. `_log_blocks` splits git's output on `\x01` and `\x00`, which can't appear in a commit subject, so a crafted subject can't break the parsing. Spoofing: someone can word a hand commit like a command's (`Close 123-x`, `File …`) to hide it from the count. The section comment says so ("a reading, not a guard"), and it only skews a metric; it gives no one any access. Info.
- **`runs/ejections.jsonl` and `build/land-<n>.ask.md` from a change's own commit** (`factory_records.ejections()`, `land_asks()`). `_json_rows` keeps only JSON objects. `cause` goes through `str()`. `train` is added to the set only when it's a string, and anything else falls back to a tuple, so a malformed row can't crash `retro` by making it hash a list or dict. `land_asks` only counts paths that match a fixed, anchored regex. Tampering with these files can only change counts.
- **`_record_ejection` error text** (`landing.py`). On an `OSError` it returns `strerror` and the file name. That holds no secrets, and it goes only into the eject's or stop's JSON output, never into a commit trailer. It doesn't block the eject, so no safety control is turned off. The ejection itself (`reset --keep`, undo printed) works as before.
- **Prompt injection into the retro skill.** Commit subjects now reach the model in `simplicity.workarounds.rows`. The retro skill already reads commit subjects elsewhere, and its writes still sit behind its WAIT, so this adds nothing new. Info.
- **The nit about `measure.errors`** (`closing.py`). The docstrings now say the raw exception text is for the person running close and must never become a trailer. That keeps exception text, which may hold paths, out of public commit trailers. Good.

**Other checks:**
- No new dependencies, and nothing new that deletes, force-pushes or publishes.
- `SETUP_SUBJECTS` and `TRIAGE_SUBJECT` are constants. The `_inbox_commit` subject it builds is unchanged.
- The gate record `build/round-1.gate.md` says PASS (`./check.sh`, exit 0). I didn't run the gate myself.

**What I read:** `intent.md`, `decisions.md` and the full code diff (`landing.py`, `closing.py`, `factory_records.py`, `retro.py`, `sdlc.py`, `REVIEW.md`, both skills), plus `_json_rows` and `_records_at` for context.
