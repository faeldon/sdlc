I resolved the one conflicted file, `.sdlc/work/inbox.md`. Both sides had only added new entries after `2026-11-18-1`, so nothing had to be chosen between them. I kept every entry and ran no git command. The full gate passes on the result: 2340 passed, 13 skipped.

- **Kept from the base branch:** entries `2026-11-18-2` to `2026-11-18-7`, unchanged and first. These are the six gaps 114-one-review left: ship's security pass, ship running the spec's path end to end, ship's UI review, ship's UX review, the factory weighing its nits, and landing review rounds in `findings.md`.
- **Kept from this change:** entries `2026-11-18-8` and `2026-11-18-9`, unchanged and after them.
  - `-8` is the idea that a `.md` file with no text should say it's empty instead of showing a blank pane.
  - `-9` is the bug where a slow fetch can show an older file under a newer file's highlight.

The ids still run in order, so no number is used twice. No conflict markers are left, `sdlc.py check` reports no problems, and `sdlc.py bugs` still reads entry `2026-11-18-9`.

## Evidence

$ grep -c -e '^<<<<<<<' -e '^=======' -e '^>>>>>>>' .sdlc/work/inbox.md
0

$ grep -n '^## \[2026-11-18' .sdlc/work/inbox.md
180:## [2026-11-18-1] [idea] `is_read()` refuses `file -C`, and git's `--ext-diff`/`--textconv`
186:## [2026-11-18-2] [idea] Ship's security pass at the factory's depth
193:## [2026-11-18-3] [idea] Ship runs the spec's path end to end
200:## [2026-11-18-4] [idea] Ship's UI review for changes that render a page
207:## [2026-11-18-5] [idea] Ship's UX review when `[ui]` is set
214:## [2026-11-18-6] [idea] Factory weighs its agents' nits and files them as `[nit]`
221:## [2026-11-18-7] [idea] Landing review rounds in `findings.md`
227:## [2026-11-18-8] [idea] The board's drawer says a file is empty instead of showing a blank pane
233:## [2026-11-18-9] [bug] A slow fetch in the board's drawer can show an older file under a newer file's highlight

$ uv run --quiet --script scripts/sdlc.py check
■ Problems: 0
    none ✅
exit: 0

$ uv run --quiet --script scripts/sdlc.py bugs | grep -n "2026-11-18-9"
10:      "id": "2026-11-18-9",
exit: 0

$ ./check.sh   (with pipefail, filtered to its summary lines)
All checks passed!
263 files already formatted
2340 passed, 13 skipped in 185.43s (0:03:05)
✔ Validation passed
✔ Validation passed
exit: 0
