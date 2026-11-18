VERDICT: PASS

## Notes
- NIT: plugins/factory/scripts/factory.py:1956: `stop_text` types `stuck` and `untestable` as `list[str] = ()`. The annotation says list while the default is a tuple. `list[str] | tuple = ()` or `None` would match what callers pass. {style S low}
- NIT: scripts/sdlc.py:9986: `status`'s `needs_of` call for ready (shipped) changes builds a minimal `reading` dict by hand. A test pins the resulting output, so this is fine. If `needs_of` later reads more fields at `shipped`, this site is easy to miss. {robustness S low}
- Done well:
  - Every outcome in the intent has code and a test.
  - The board's copies of `factory.py`'s parsing (`STUCK_RE`, `UNTESTABLE_RE`, the land-step shape) are added and pinned.
  - Each stop text now has a plain line, with the raw text kept under it.
  - `column()` moves a stopped landing to Needs you ahead of the `close` column, and `status` reads the same rule through `needs_of()`. This resolves the intent's open question in favour of both surfaces, which I accept.
  - `[context]` pass: `docs/REFERENCE.md` and `plugins/factory/README.md` are updated in the same diff, and I found no false statement left in the context docs.
- Ran `./check.sh`: it passes. The only warning is the plugin icon, which plugin validation reports as not affecting its result.
- Ran `pytest` on `test_board`, `test_factory`, `test_land` and `test_sdlc`: 837 passed, 18 skipped.

I could not read `spec.md`, because the change is Tier 1 and has none. I reviewed against `intent.md`'s Outcome and `plan.md`.
