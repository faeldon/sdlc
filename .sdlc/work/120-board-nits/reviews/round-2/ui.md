VERDICT: PASS

The kept round-1 item is fixed in the code, and the changed styling holds at both widths. The one thing the shots don't show is the new short stop wording, because the 006 card still renders its old record.

- **Kept item, `factory.py:1985`:** `WAYS_WHY["mend"]` now reads "Rerunning /sdlc-factory:build {id} asks an agent again, once, for the reply in its shape; if that reply still lacks it, ship it by hand with /sdlc:ship {id}." The word "mend" no longer appears in the drawer text, which matches the suggested rewording.

## Notes

- **Screenshots read:** `index-1280x800.png` and `index-390x844.png` (round 2). Both are the light theme only.
- **Stale 006 record:** the 006 card still shows the old run-on `next:` ("whose one mend asks again…", about nine lines at 390px). It comes from `tests/fixtures/board/changes/006-draft-purge/runs/stopped.md`, which predates the new `WAYS` text. So the "line or two" outcome in intent.md is not visible in these shots. Updating that fixture's `NEXT:` line would let the next shots show it. Not a CHANGE, because nothing overflows or can't be read.
- **Wrapping:** `.next code` has `overflow-wrap: anywhere` (`board.html:80`), and the monospace `next:` text stays inside its card at 390px and 1280px. No horizontal scroll is visible.
- **Needs-you wording:** the 006 and 007 cards read "needs you: stopped: rerun to ask an agent again" and "decide D1", and neither uses the word "mend".
- **Dark theme:** `board.html` ships a `prefers-color-scheme: dark` palette, which these shots don't show. The `--stop` colour on the card surface should be checked in dark at ship, since the needs-you line and flags are red text.
- **What the change does well:** the stop record keeps its `STOPPED:`, `NEXT:` and `- PROBLEM:` shape, so the board's pinned readers are untouched, and the longer sentence sits in the drawer body where a person reads it.
