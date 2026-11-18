VERDICT: CHANGES

- CHANGE: [correctness] scripts/sdlc.py:7613-7618 (`cmd_intake`): the `try/except Exception` swallows the error, and `unpushed_closes()` returns None when git can't say. Both paths then set `waits_on_push` to False for every dangling issue, so a dangling issue that an unpushed commit closes is offered to triage again, which is the bug this change fixes. Triage can't tell "read failed" from "nothing waits". Fix: when `closing is None` and any dangling entry has a `closed_by` match to check, say so in a field such as `dangling_error` (or a per-entry `waits_on_push: null`). Then have triage's `dangling` bullet not offer any dangling issue while that is set. Narrow the `except` to the errors `closed_by()` can actually raise, or drop it. Add a test for the None path, since no test covers it.

## Notes

- NIT: plugins/factory/skills/spec/SKILL.md:88-91: the skill now has the script's question twice, once as "Ask `start`'s `question`" and again as a literal blockquote. The two can drift, which is what the change was meant to stop. Keep only the instruction to ask `start`'s `question` as printed, or leave the blockquote as a note that it's an example. {docs S med}
- NIT: scripts/sdlc.py:7620: the `# fmt: skip` on the `out["dangling"]` comprehension looks unneeded, since `ruff format --check` passes without it. Remove it if the formatter agrees. {style S low}

**Done well:**
- The stale-response fix uses a request counter (`asking`) and is covered by a test that fails without it. The test releases two fetches out of order and checks that `doc` holds the newer file.
- The empty-file note is tested for both an `.md` and a non-`.md` file, and checks the raw toggle.
- `spec_question()` is worded once in the script, and the spec skill's question text matches it.
- `FINDINGS_HEAD` and `templates/findings.md` match, and `setup.json` was re-recorded. `sdlc.py drift` reports nothing.
- The pinned checks in `checks.md` describe the new wording.

**Ran:**
- `uv run --group dev pytest -q -n auto` on `test_board`, `test_factory`, `test_archive`, `test_defaults`, `test_skills` and `test_sdlc`: 1281 passed, 13 skipped.
- `uv run --script scripts/sdlc.py drift`: no breaking, refresh or report entries.
- `ruff check` passes, and `ruff format --check` reports all 252 files formatted.

Not run: `check.sh` as a whole, and the Windows-marked tests. The change adds no `open()` or subprocess that needs a platform check.
