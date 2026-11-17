# Notes

> Free-form notes on the change. Anything left undone is an unticked `- [ ]` line, which
> `/sdlc:ship` carries to a seed in the register or drops with a reason.

## Left undone

- [x] Six `#` comments in `scripts/sdlc.py` still call the change folder `work/` (above `ENTRY_RE`, `OPEN_ITEM_RE`, `DOC_TEMPLATES`, `LAST_ID`, `config`'s `"work"` key, and the trackers section). They aren't docstrings, so they're outside this change's scope. → seed: 2026-11-17-65
