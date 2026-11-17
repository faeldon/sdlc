DECISION: ESCALATE

**Why:** The build looks finished. AGENTS.md went from 517 to 293 lines, ship's context pass asks the new question, and the reviewer's single round was `VERDICT: PASS`. `./check.sh` passed with 1903 tests. Even so, D1, D2 and D3 in `decisions.md` are all unticked, so the build rests on three assumptions you haven't confirmed. The reviewer also raised the `.sdlc/work/inbox.md` edit on this branch, which may break the "the register is only committed through `inbox-commit`" rule. That needs your eye before anything lands.

**Open items**
- REFERENCE.md:234 is a new 121-character line in a paragraph wrapped at about 100 characters and should be rewrapped (nit, raised by the code reviewer).
- `.sdlc/work/inbox.md` is modified in the worktree: seed 2026-11-17-3 went from `[idea]` to `[building]`. Confirm this is the intended flow and that ship won't commit the register onto this branch (code reviewer, optional 2).
- The Architecture section may still be more manual than map: Factory, Setup and Closing each run 10–20 lines and still restate mechanics. Whether to cut further is your call (code reviewer, optional 1).
- In `notes.md`: several docstrings (`sdlc.py`'s module docstring, `change_dirs()`, `next_id()`, `claim()`, `cmd_uninstall()`) still say `work/`, and AGENTS.md now points at some of them (builder).
- In `notes.md`: `sdlc.py`'s module docstring lists only about half the subcommands (builder).
- In `notes.md`: CONTRIBUTING.md's *Writing a tracker* leaves out the intake methods (`mark()`, `unmark()`, `needs_info()`, `open_marks()`, `open_numbers()`, `closed_by()`), and AGENTS.md points there for the interface (builder).
- Pre-existing, not part of this diff: the `_drop_record` docstring at scripts/sdlc.py:3926 breaks off mid-sentence (code reviewer).

**Decisions to confirm**
- D1: detail that REFERENCE.md doesn't hold goes into the named function's docstring. Topics CONTRIBUTING.md already covers (handoffs, trackers, cases) stay pointed there.
- D2: no suite test. A length cap (under 300 lines) and a check that every pointer exists are only acceptance checks in `checks.md`, plus the new context-pass question.
- D3: one change, not one per area. Every cut is traced in `plan.md`'s table.

**For the person at ship**
1. Read the new Architecture section in AGENTS.md next to `plan.md`'s "Where each cut rule lives" table. The reviewer checked for lost rules with grep, concept by concept, and says the factory README's *Mechanism* and *What it leaves* sections weren't read line by line against the old factory paragraph. That is the likeliest place for a dropped rule.
2. Check the five docstrings that received moved rules: `cmd_base()`, `cmd_resolve()` with the `RESOLVE_REFS` comment, `cmd_close()`, `retro.py`'s module docstring, and `recorded_issues()`.
3. Look at step 4 of `skills/ship/SKILL.md`. This edit reaches every host. The skill is now at exactly its 475-line budget, and two existing sentences were reworded shorter to fit.
4. Make sure `.sdlc/work/inbox.md` is not part of the commit.

- IMPACT: patch — the only change a host receives is one more question in ship's context pass, so it proposes fewer restatements. Nobody has to do anything differently and no new feature appears; the rest is this repo's own docs and docstrings.
