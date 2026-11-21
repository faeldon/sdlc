# 206-update-skill — entries

## [2026-11-21-7] [idea] Manually verify the update hook and /sdlc:update in a scratch repo

Left undone by 206-update-skill, carried forward when it landed: Manual (the spec's Verification): in a scratch repo with the plugin installed from GitHub at an older version, a new session shows the one line (proves `systemMessage` reaches the person), `/sdlc:update` lists its steps, and `--scope project` acts on the folder it runs in.
See .sdlc/work/206-update-skill/notes.md in its commit.
Raised 2026-11-21.

## [2026-11-21-8] [nit] `update_line` returns None when the sdlc install here is read from a folder, so a stale `sdlc-factory` install is also never mentioned.

Raised by the code review of 206-update-skill, round 1: scripts/sdlc.py:9507: `update_line` returns None when the sdlc install here is read from a folder, so a stale `sdlc-factory` install is also never mentioned. This follows D2 but is broader than it needs to be. Check the factory row separately if that matters

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 206-update-skill (correctness)

## [2026-11-21-9] [nit] `update_line`'s first form ("this session runs X") also fires when the install is already updated and only the restart is missing.

Raised by the code review of 206-update-skill, round 1: scripts/sdlc.py:9546: `update_line`'s first form ("this session runs X") also fires when the install is already updated and only the restart is missing. `/sdlc:update` then handles it through `restart_first`, so this is fine. A short comment would say so

Theme: docs
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 206-update-skill (correctness)

## [2026-11-21-10] [nit] the fake `claude` opens its log and rows files without an encoding, unlike the `encoding="utf-8"` the repo's tests use elsewhere.

Raised by the test review of 206-update-skill, round 1: tests/test_update.py:107: the fake `claude` opens its log and rows files without an encoding, unlike the `encoding="utf-8"` the repo's tests use elsewhere. It is not a portable test, so it only matters on a non-UTF-8 locale.

Theme: tests
Paths: tests/test_update.py
Cost: S
Value: low
Raised by: 206-update-skill (correctness)

## [2026-11-21-11] [nit] the fake `claude` opens its log and rows files without `encoding="utf-8"`.

Raised by the test review of 206-update-skill, round 2: tests/test_update.py:107: the fake `claude` opens its log and rows files without `encoding="utf-8"`. It is not a portable test, so it only matters on a non-UTF-8 locale.

Theme: tests
Paths: tests/test_update.py
Cost: S
Value: low
Raised by: 206-update-skill (correctness)
