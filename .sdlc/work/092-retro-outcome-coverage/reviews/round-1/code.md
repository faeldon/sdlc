VERDICT: PASS

No Critical or Required findings. All ten requirements have code and a test that would fail without it, and the repo's invariants hold.

## Notes

**Optional**
- `skills/retro/SKILL.md`, the `direction` bullet in Step 0: one line runs well past the wrap width of its neighbours after the `serves` text was added. Re-wrap it.
- `scripts/sdlc.py`, wrapped-goal reading: D1 is recorded in `decisions.md` and its default is sensible. Nothing here is wrong. It does widen R1 beyond the spec, so the person may want to confirm at ship that the spec gets amended to match.
- `_uncited()`: a milestone that cites only an unknown `G` id gets `why: unknown`, while one that cites a known goal citing nothing gets `none`. Both follow D2 and the spec's own wording, so no change is needed.

**Done well**
- `doc_items()` adds only the `serves` key, appends nothing to `problems`, and leaves `current` and `Groups:` handling as it was.
- The seed's theme is read from the register at the change's base, not today's, with one `git show` per base and a cache. That avoids the trap the spec names, where every `none` change would read as `(no theme)`.
- `_none_themes()` reads only the work path, as AGENTS.md requires for retro.
- `ref_matches()` is used instead of matching titles alone.

**Ran**
- `pytest tests/test_retro.py tests/test_next_up.py tests/test_skills.py tests/test_defaults.py -n auto`: 608 passed.
- I did not run `./check.sh` or the Verification block's `retro` and `status` commands, so `claude plugin validate --strict`, the full-repo test run and the live-repo `retro` output are unchecked. Running `./check.sh` at ship would settle them.
