DECISION: ESCALATE

**Why:** The build looks complete. R1–R16 each have code and a test, all three round-1 reviewers returned PASS, and the gate is green (`./check.sh`, exit 0, 3660 passed). It escalates on one default only. D1 edits a test outside this change's scope, and a default about scope is the person's to decide.

**Open items**
- None from the reviewers. Their NITs are minor: code.md notes that `update_line` is silent for a stale factory install when the sdlc install is read from a folder, and that the first line form also fires when only the restart is missing. test.md notes that the fake `claude` opens its files without an encoding.

**Decisions to confirm**
- ESCALATED: D1: pinning `plugin_version()` at 1.10.0 in `tests/test_archive.py` edits a test outside this change's scope. That is the person's call, and the alternatives are re-recording the fixture or leaving it to its own change.
- SETTLED: D2: the intent's constraint says to stay silent for a local-path marketplace. `update_line` returns None for a folder-read install, and the code and test reviews confirm it.
- SETTLED: D3: R6 and R8 are tested with a worktree row of this repo and another repo's install. Worktree rows are left out of `elsewhere`, and the test review found the tests cover this.
- SETTLED: D4: the intent lists no `claude` on PATH among the cases to stay silent in. R2 is tested (`test_hook_is_silent_when_it_can_t_tell`), and a line without the stale installs would be wrong about what to update.
- SETTLED: D5: `test_setup_drafts_from_readiness_and_never_commits` pins setup against committing. Pointing at Step 6 keeps that pin and reaches the same commit, and R12 is tested.

**Every other reason you escalate for**
- ESCALATED: look: `tests/test_archive.py: _close_scenario()` — the D1 scope edit (see D1). It is also needed for the gate to pass, so the person should see it.

**For the person at ship**
- Look first at `scripts/sdlc.py`: `cmd_update`, `update_line`, `check_update` and `installed_check`. Then look at `hooks/hooks.json`, `skills/update/SKILL.md`, and the changes to the setup skill.
- The hook is the plugin's first, and it is advisory only: one line or nothing, exit 0 always.
- The AGENTS.md paragraph and the README skill row are covered by checks in `checks.md`.
- The spec's manual verification still needs a person. The behaviour reviewer did not run it, because it needs a real install and the network.

- IMPACT: minor — a new `/sdlc:update` skill and a startup hook that tells the person when a release is out.

- UNDONE: `tests/fixtures/close-output.json` records `Sdlc-Runtime: plugin=<version>`, and the test read the running manifest, so every release turned it red. This change pins the version in `_close_scenario()`. Other recorded outputs may read `plugin_version()` the same way; worth a look. → seed: Check other recorded test outputs for a live `plugin_version()` read
- UNDONE: Manual (the spec's Verification): in a scratch repo with the plugin installed from GitHub at an older version, a new session shows the one line (proves `systemMessage` reaches the person), `/sdlc:update` lists its steps, and `--scope project` acts on the folder it runs in. → seed: Manually verify the update hook and `/sdlc:update` against a real install
