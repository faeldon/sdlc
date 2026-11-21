VERDICT: PASS

Every requirement R1–R13 maps to a test or a check that would fail without it. The tests can fail, and the gate was green.

## Notes
- **Coverage by requirement:**
  - R1–R3, R8–R10: `test_every_wait_asks_in_a_dialog`, `test_every_wait_names_its_preview` and `test_retros_rating_has_no_preview`, for all 20 gated skills.
  - R4: `test_preview_cut_is_a_pinned_copy` and `test_preview_cut_keeps_forty_lines` check both scripts at 40 and 41 lines.
  - R5: two tests in `test_factory_agent.py`. They check that `preview` holds only the Requirements, that the cut applies, that `--recheck` gives a fresh preview, and that `git status` is unchanged.
  - R6: tests in `test_factory_depth.py` cover the gate, models, rounds, restart and upgraded. They also check that a spec start or a refused start gives no preview.
  - R7, R12: tests in `test_preflight.py` cover findings, paths including a rename, the stamp line, the cut, no writes, refusal on a bad `findings.md`, and `--preview` with `--question`.
  - R11, R13: `checks.md`, below.
- **Gate:** `build/round-1.gate.md` shows 3763 passed, 29 skipped, validation passed.
- **Test command I ran:** I ran named tests only, in the foreground: `pytest tests/test_modules.py -k preview`, `test_preflight_preview_lists_findings_paths_and_stamp` and `test_a_long_spec_preview_is_cut`. 5 passed.
- **Check "No WAIT's literal question changed (R11)":** I ran its diff-and-grep logic read-only, and it exits 0 on the current tree. It can fail, because the question lines are `> \`…? (…)\`` blockquotes and the grep matches an added or removed one. It leaves the tree unchanged.
- **Check "The docs say the yes options carry the draft as their preview (R13)":** it greps for the sentences in `AGENTS.md`, `docs/CONTRIBUTING.md` and `docs/REFERENCE.md`. It fails only if one is removed, and it leaves the tree unchanged. The `AGENTS.md` and CONTRIBUTING lines are present.
- NIT: tests/test_skills.py:263: the `PREVIEW_NAMES` words are checked with substring `in`, so a key word like `path` or `tag` matches any text that contains it {tests S low}
