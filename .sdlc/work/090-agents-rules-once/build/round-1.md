I've rewritten the Architecture section of AGENTS.md as a map, and ship's context pass now asks a third question. AGENTS.md went from 517 lines to 293, and the gate passes with 1903 tests. Everything is left uncommitted.

**The AGENTS.md rewrite.** I went through the old section paragraph by paragraph. Each one now keeps its boundary and the rules you can't see from any single function, such as: never write `main` into a git call, never a stash, never a merge of `main` into a branch, never match an entry by title alone, and the board never in the allow rules. For the detail it points at the one place that holds it: a section of REFERENCE.md, CONTRIBUTING.md, the factory's README, or a named function's docstring. I checked every cut sentence against where its pointer leads before cutting it. The table in `plan.md` shows where each one lives now.

Five rules were said nowhere but AGENTS.md, so I added them to the code first. These are docstring and comment edits only; no code changed:
- **`cmd_base()`**: when a conflict counts as resolvable, and that the factory resolves conflicts with its own command, so `base` never does. I also fixed its stale "the one write before a WAIT" (there are now three).
- **The `RESOLVE_REFS` comment and `cmd_resolve()`**: the resolve state lives in refs, never in a file in the tree, which the rebase would trip on. The side file ship uses is `skills/ship/conflict.md`.
- **`cmd_close()`**: the steps in order; a refused push is `push_failed`, never a failed close; and close never restores a file the fast-forward deletes.
- **`retro.py`'s module docstring**: tests call its names as `sdlc.retro.<name>`; a default argument can't read `sdlc`; and the readers `status` and release use stay in `sdlc.py`.
- **`recorded_issues()`**: the tracker's `mark()`, `unmark()` and `needs_info()` only set what it decides.

**Ship's context pass.** Step 4 of `skills/ship/SKILL.md` now asks whether a line is already said in another context doc or a docstring, and if so proposes a pointer instead of the line. The skill was already at its 475-line limit, so to stay under it rather than raise the limit I shortened two existing sentences by a line each without changing what they say. REFERENCE.md's description of the pass now includes the new question. I also corrected CONTRIBUTING.md's opening, which said AGENTS.md covers the architecture "function by function".

**Tests.** I added no suite tests, since this is prose. `checks.md` has three acceptance checks:
- **AGENTS.md is under 300 lines.** Fails on the old text.
- **Ship asks the new question.** Fails on the old text.
- **Every `name()` AGENTS.md points at is defined in the scripts.** It also passes on the old text, so it catches a pointer left behind by a rename rather than a revert.

**Changes from the plan.**
- I had planned to fix `sdlc.py`'s module docstring and point at it for the list of subcommands. I left it alone because it lists only about half of them, so it would be a poor pointer.
- The ship skill rewording to fit the line limit is recorded in `plan.md`.
- The wording of check 3 changed to match.

**Left in `notes.md`** (three unticked items):
- [ ] Several docstrings still call the change folder `work/`, its name before 1.4.0, and AGENTS.md now points at some of them.
- [ ] `sdlc.py`'s module docstring lists about half the subcommands.
- [ ] CONTRIBUTING.md's *Writing a tracker* leaves out the intake methods (`mark`, `unmark`, `needs_info`, `open_marks`, `open_numbers`, `closed_by`).

- DECISION: [default] Where does detail go that REFERENCE.md doesn't hold? Options: CONTRIBUTING.md; docstrings. Going ahead with the named function's docstring for internals and CONTRIBUTING.md where it already covers the topic (handoffs, trackers, cases), since REFERENCE.md is written for hosts.
- DECISION: [default] Should a suite test cap AGENTS.md's length or check its pointers? Options: a suite test; acceptance checks only. Going ahead with acceptance checks only (a length check and a pointers-exist check in `checks.md`), plus the new context-pass question, since the outcome asks only for the skill's wording.
- DECISION: [default] One change, or one per area of the section? Going ahead with one change: every cut is traced in `plan.md`'s table, so the review can check it in one place.

## Evidence

$ ./check.sh
All checks passed!
1903 passed in 62.87s (0:01:02)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --quiet --script scripts/sdlc.py check --strict
■ Problems: 0
    none ✅
exit: 0

$ wc -l AGENTS.md skills/ship/SKILL.md
     293 AGENTS.md
     475 skills/ship/SKILL.md
exit: 0

$ test "$(wc -l < AGENTS.md)" -lt 300
exit: 0

$ test "$(git show HEAD:AGENTS.md | wc -l)" -lt 300
exit: 1

$ grep -o '`[A-Za-z_][A-Za-z0-9_]*()`' AGENTS.md | tr -d '`()' | sort -u | grep -vxE 'as_posix|open' | while read -r f; do grep -qE "def $f\(" scripts/*.py scripts/trackers/*.py plugins/factory/scripts/*.py || { echo "AGENTS.md names $f(), defined nowhere"; exit 1; }; done
exit: 0

$ grep -q 'already said in another context doc, or in the docstring of the code it is about' skills/ship/SKILL.md && grep -q 'propose a pointer there, never the line' skills/ship/SKILL.md
exit: 0

$ git show HEAD:skills/ship/SKILL.md | grep -q 'propose a pointer there, never the line'
exit: 1

$ uv run --quiet --script scripts/sdlc.py checks 090
"problems": []
exit: 0
