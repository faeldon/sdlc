VERDICT: PASS

## Notes

- NIT: plugins/factory/skills/land/SKILL.md:76: the Step 1 sentence "Under each change, what the yes approves for it…" runs past the ~100-column wrap of the paragraphs around it. Rewrap it.
- NIT: plugins/factory/skills/land/SKILL.md:102: the question still says "as shown" twice. It stays, as the intent requires, but a session can't tell that "shown" now means the `preview` text. The skill's Step 2 explains it, so this is only a note.

**What's done well**

- Each intent requirement has code and a test. The title, Problem and Outcome come from `intent_parts()` through the existing `_section()`, unparaphrased. `land_shown()` covers the seed, bug, drop, assumed decision, check, cases and recovery lines, with a change that has none of them shown by title alone.
- `land_shown()` is read-only and renders the note text as one line (`note_items()` joins continuation lines), so the list formatting holds for multi-line notes.
- `intent_parts()` reads UTF-8 explicitly and writes nothing, so it is Windows-safe. `factory.py` still doesn't import `sdlc.py`.
- The question's wording and what a yes approves are unchanged, as the intent requires.
- The four builder decisions (D1–D4) are open defaults, and the diff implements them as written. I raised none of my own.

**Tests and commands run**

- `uv run --group dev pytest -q tests/test_land.py tests/test_skills.py`: 412 passed.
- `ruff check` and `ruff format --check` on `factory.py` and `tests/test_land.py`: clean.
- Not run: the full `./check.sh`, `tests/test_nothing_local.py`, `tests/test_windows.py`. The new test data uses neutral names.

**Unsure, and what would settle it**

- I can't tell from the code whether the harness's AskUserQuestion renders `preview` on the focused `yes` option. If it doesn't, the dispositions still reach the person only through the text the skill prints above the dialog. One live landing of a batch with a seed, a bug and a drop would settle it.
- There is no `spec.md` (Tier 1), so I took the requirements from `intent.md`'s Outcome and Constraints.
