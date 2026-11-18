# 152-board-drawer-browser-test — entries

## [2026-11-18-74] [idea] Limit CI's GITHUB_TOKEN to contents: read in check.yml

Left undone by 152-board-drawer-browser-test, carried forward when it landed: pre-existing: .github/workflows/check.yml:13: no `permissions:` block; set `permissions: contents: read` so a compromised dev dependency running in CI can't use a write-scoped token
See .sdlc/work/152-board-drawer-browser-test/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-75] [nit] the header comment line now runs to 166 characters; the rest of the file wraps near 100.

Raised by the code review of 152-board-drawer-browser-test, round 1: .github/workflows/check.yml:3: the header comment line now runs to 166 characters; the rest of the file wraps near 100. Re-wrap it

Theme: style
Paths: .github/workflows/check.yml
Cost: S
Value: low
Raised by: 152-board-drawer-browser-test (correctness)

## [2026-11-18-76] [nit] the intent's open question on a skip note in `./check.sh`'s summary is not addressed.

Raised by the code review of 152-board-drawer-browser-test, round 1: tests/test_board_browser.py:75: the intent's open question on a skip note in `./check.sh`'s summary is not addressed. Recorded here as a possible follow-up; the gate record shows 28 skipped without saying why

Theme: docs
Paths: tests/test_board_browser.py
Cost: S
Value: low
Raised by: 152-board-drawer-browser-test (correctness)

## [2026-11-18-77] [nit] the rewrapped header comment runs past the file's line width

Raised by the security review of 152-board-drawer-browser-test, round 1: .github/workflows/check.yml:3: the rewrapped header comment runs past the file's line width

Theme: style
Paths: .github/workflows/check.yml
Cost: S
Value: low
Raised by: 152-board-drawer-browser-test (contract)

## [2026-11-18-78] [nit] the reflowed header comment leaves one line far over the file's roughly 100-column wrapping

Raised by the test review of 152-board-drawer-browser-test, round 1: .github/workflows/check.yml:3: the reflowed header comment leaves one line far over the file's roughly 100-column wrapping

Theme: style
Paths: .github/workflows/check.yml
Cost: S
Value: low
Raised by: 152-board-drawer-browser-test (correctness)

## [2026-11-18-79] [nit] the test takes about 49s here, mostly waiting on the poll interval.

Raised by the test review of 152-board-drawer-browser-test, round 1: tests/test_board_browser.py:98: the test takes about 49s here, mostly waiting on the poll interval. A shorter bounded wait or a faster poll in the fixture would speed up `./check.sh`

Theme: tests
Paths: tests/test_board_browser.py
Cost: M
Value: low
Raised by: 152-board-drawer-browser-test (correctness)
