I've added this repo's release rule to `.sdlc/SDLC.md`: it releases once each wave has landed and before the next retrospective, rather than when `status` shows Release due. The test that enforces "answers the guide, doesn't copy it" passes, and the new acceptance check passes. Nothing is committed.

**What I built** (Tier 1, one file, so no `plan.md`):
- A new section in `.sdlc/SDLC.md` under the guide's heading `### The release loop → /sdlc:release, then /sdlc:publish`. It sits between Stage 5 and Stage 6, the same place as in `guide/process.md`.
- It points to where waves are defined (`docs/RETRO-SCORECARD.md`, *Waves*) and gives two reasons:
  - Changes in a wave depend on each other, so releasing mid-wave gives users half a wave.
  - Releasing before the retrospective gives `time_to_users` something to measure.
- It doesn't restate the guide's Release due rule.

**Proof:** a requirement only a deliberate revert could break gets an acceptance check, not a suite test. The one in `.sdlc/work/205-release-cadence/checks.md` passes when the release-loop section of `.sdlc/SDLC.md` mentions waves and says "before the next retrospective". It failed before the edit (exit 1) and passes after (exit 0), leaving the tree unchanged.

**Tests run:**
- `tests/test_defaults.py`: 127 passed. This covers the edit's two constraints: every block sits under a heading the guide has, and none copies a guide block word for word. It also includes the check that `.sdlc/setup.json` is up to date.
- `tests/test_nothing_local.py`: 8 passed, since the new text is prose.

Nothing is left in `notes.md`, and I raised no decisions.

## Evidence

$ sh -c "$(awk '/^```sh/{f=1;next} /^```/{f=0} f' .sdlc/work/205-release-cadence/checks.md)"   # before the edit
exit: 1

$ sh -c "$(awk '/^```sh/{f=1;next} /^```/{f=0} f' .sdlc/work/205-release-cadence/checks.md)"   # after the edit
exit: 0

$ git status --short
 M .sdlc/SDLC.md
?? .sdlc/work/205-release-cadence/
exit: 0

$ uv run --group dev pytest -q tests/test_defaults.py
127 passed in 0.97s
exit: 0

$ uv run --group dev pytest -q tests/test_nothing_local.py
8 passed in 0.93s
exit: 0
