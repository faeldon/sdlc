# Notes

- [x] `tests/fixtures/close-output.json` records `Sdlc-Runtime: plugin=<version>`, and the test → dropped: 207 lands first with its masked close-output fixture, which fixes the release-bump breakage and replaces this re-record.
  reads the running manifest, so every release turns it red. This change re-records it at 1.11.0
  (D1); it breaks again at the next release. Pinning the version in `_close_scenario()` would end
  that, and other recorded outputs may read `plugin_version()` the same way; worth a look.
- [x] Manual (the spec's Verification): in a scratch repo with the plugin installed from GitHub at → seed: 2026-11-21-7
  an older version, a new session shows the one line (proves `systemMessage` reaches the person),
  `/sdlc:update` lists its steps, and `--scope project` acts on the folder it runs in.
