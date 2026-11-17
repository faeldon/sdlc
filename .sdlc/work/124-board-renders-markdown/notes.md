# Notes

- [x] `show()` has no guard against two fetches overlapping: a slow reply for the file picked → dropped: the same fault as the `pre-existing:` item below, which is filed as a bug
  first can paint over the one picked after it. Older than this change; a request counter would
  settle it.

- [x] ux: scripts/board.html:570: a `.md` file with no text (`doc.text` is `""`) draws a blank pane, because `??` keeps the empty string and the markdown branch renders an empty `div`. The drawer looks broken. Say the file is empty, for example "This file is empty." in the same note style as "This folder holds no file yet." → seed: 2026-11-18-8
- [x] pre-existing: scripts/board.html:573-585: `show()` assigns `doc` when its fetch resolves, whichever file was asked for last. If two files are clicked quickly and the older response arrives second, the pane shows the older file while the list highlights the newer one. Filed for later, not reworked here. → bug: 2026-11-18-9
