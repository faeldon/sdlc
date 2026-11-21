DECISION: READY

**Why:** Round 2 is all `VERDICT: PASS` from the code, test and behaviour reviewers. The gate is green (3660 passed, plugin validation passed). Round 2 only re-recorded the close-output fixture at 1.11.0. D1 through D6 are ticked and no default is open. The only unticked items in `notes.md` are minor and are listed below.

**Open items:** None. The reviewers raised no CHANGE items. The one NIT is `tests/test_update.py:107`, where the fake `claude` opens its log files without `encoding="utf-8"`. It is low severity and only matters on a non-UTF-8 locale, in a test not marked portable.

**Decisions to confirm:** None open. D1 was decided by the person (re-record the fixture at 1.11.0). D2 to D5 are settled by the approver, and D6 is seen.

**For the person at ship:**
- **Landing order:** Your memory note says land 207 first. At 206's landing, keep 207's masked close-output fixture and drop 206's re-record of `tests/fixtures/close-output.json`.
- **Look first:**
  - `scripts/sdlc.py`: `update_line`, `cmd_update` and the install-row logic, covering the folder-read, worktree-row and no-`claude` silence cases.
  - `hooks/hooks.json`: the new startup hook.
  - `skills/update/SKILL.md`: the new skill and its WAIT.
  - Setup's `complete` stop, which points at Step 6.
- **Published surfaces:** The `/sdlc:update` skill and the startup hook are new. The intent and spec approve them, so I name them here and don't escalate on them.

- IMPACT: minor — someone holding the previous release can newly run `/sdlc:update` and hears of a newer release at session start.

**Undone items:**
- UNDONE: `tests/fixtures/close-output.json` records `Sdlc-Runtime: plugin=<version>`, and the test reads the running manifest, so every release turns it red. This change re-records it at 1.11.0 (D1); it breaks again at the next release. Pinning the version in `_close_scenario()` would end that, and other recorded outputs may read `plugin_version()` the same way; worth a look. → dropped: 207 lands first with its masked close-output fixture, which fixes the release-bump breakage and replaces this re-record.
- UNDONE: Manual (the spec's Verification): in a scratch repo with the plugin installed from GitHub at an older version, a new session shows the one line (proves `systemMessage` reaches the person), `/sdlc:update` lists its steps, and `--scope project` acts on the folder it runs in. → seed: Manually verify the update hook and /sdlc:update in a scratch repo
