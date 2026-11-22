Built 218: `ask --answered` now says `rebuild` when a confirmed default came from a reviewer or the approver and no later builder round says it built it. A confirmed builder default still goes to `ship`. The full gate passed (3952 tests, 29 skipped, exit 0). Everything is uncommitted and HEAD is still `3bafdfd`.

The intent is Tier 1, but its Approach touches four files plus tests, so I wrote a short `plan.md` first: files, the three slices below, which test proves what, and rollback (`ask` writes nothing, so a `git revert` undoes it). The build matches it.

**Slices built**
1. **Script** (`plugins/factory/scripts/factory.py`):
   - A new `BUILT_RE` matches a `- BUILT: D<n>` line in a builder report.
   - A new `unbuilt_defaults()` finds each default kept with `the assumed default, confirmed` whose source isn't a builder. It counts as built only when a builder report from a later round than the one that raised it (`build/round-<R>.md`) has a `- BUILT:` line for that id.
   - When `cmd_ask()` is given `--answered`, it lists these lines as `unbuilt` (id, source, question). If any exist, `next` is `rebuild`, with `then` as before: `/sdlc-factory:build NNN` for an ESCALATE, `/sdlc:ship NNN` for a READY. `ask` still writes nothing.
2. **Builder** (`plugins/factory/agents/builder.md`): the builder now writes `- BUILT: D<n>: <what you built>` for any reviewer's or approver's default its round builds, and only for what the code now does.
3. **Wording**: the decide skill's `rebuild` explains the new reason and names each `unbuilt` line, and the factory README's decide entry says the same.

**Tests added**
- `test_ask_says_rebuild_for_a_reviewer_s_default_never_built` replays 216's case. With only the builder's D1 kept, the answer is `ship` and `unbuilt` is empty. With the security reviewer's D2 also kept, it is `rebuild` naming D2, with the right `then` for both ESCALATE and READY.
- `test_ask_says_ship_once_a_later_builder_report_built_it` has three cases. A round-2 `- BUILT: D2` gives `ship`. The same line in round 1, the round that raised D2, gives `rebuild`. A round-2 line naming D1 instead also gives `rebuild`.
- `test_a_reviewer_s_default_is_built_before_it_ships` checks the builder names the `- BUILT:` line and the decide skill's `rebuild` names `unbuilt`. Neither text exists in the base files (both greps count 0), so it would fail there.
- The existing `test_ask_says_ship_when_every_default_is_kept` still covers a builder's own default going to `ship`.

The new script tests failed first for the expected reasons (`KeyError: 'unbuilt'`, and `ship` where `rebuild` was expected), then passed.

**Named runs:** `tests/test_factory_decisions.py` (100 passed); `tests/test_skills.py -k "reviewer_s_default or decide"` (21 passed); ruff check and format on the three Python files are clean. I ran the full gate twice by mistake: the first time only its tail was printed, so I reran it to get the exit code and test count.

Nothing is left in `notes.md`.

- DECISION: [default] A reviewer's default counts as built only when a builder report from a later round has a `- BUILT: D<n>` line for it. Going ahead with that unless told otherwise.
  - OPTION: an explicit `- BUILT: D<n>` line — the script can check it and the builder only writes it for what it built; a builder that forgets it causes a needless rebuild
  - OPTION: any builder report after the raising round — needs no new line; it can't tell a build that made the call from one that ignored it, which is how 216 shipped
  - OPTION: the builder's own `- DECISION:` line naming the id — reuses an existing line; a decision line is a question, not a record of work done
  - WHY: the intent's open question; only a line about the work itself keeps `ask` deciding from the files alone
- DECISION: [default] Leave autopilot's handling of reviewer defaults it answers for a later change. Going ahead unless told otherwise.
  - OPTION: out of scope here — this change stays the size its Approach sets; autopilot can still land a reviewer's default nobody built
  - OPTION: autopilot holds such a change — closes the same gap; it widens 218 into autopilot's hold rules, which the Approach doesn't cover
  - WHY: `autopilot.py` never calls `cmd_ask`, so this fix doesn't reach it, and the intent leaves it as an open question

## Evidence

$ cat .sdlc/work/218-ask-reviewer-defaults/*.md
(intent.md: tier 1, stage build, Approach as quoted above)
exit: 0

$ uv run --group dev pytest -q tests/test_factory_decisions.py -k "reviewer_s_default or later_builder or every_default_is_kept"
FAILED tests/test_factory_decisions.py::test_ask_says_rebuild_for_a_reviewer_s_default_never_built
FAILED tests/test_factory_decisions.py::test_ask_says_ship_once_a_later_builder_report_built_it[same-round]
FAILED tests/test_factory_decisions.py::test_ask_says_ship_once_a_later_builder_report_built_it[another-id]
3 failed, 2 passed, 95 deselected in 2.76s
exit: 1

$ uv run --group dev pytest -q tests/test_factory_decisions.py -k "reviewer_s_default" 2>&1 | grep -E "^E " | head -4
E       KeyError: 'unbuilt'
exit: 0

$ uv run --group dev pytest -q tests/test_factory_decisions.py -k "ask"
13 passed, 87 deselected in 2.92s
exit: 0

$ git show HEAD:plugins/factory/agents/builder.md | grep -c "BUILT: D<n>"; git show HEAD:plugins/factory/skills/decide/SKILL.md | grep -c unbuilt
0
0
exit: 1

$ uv run --group dev pytest -q tests/test_skills.py -k "reviewer_s_default or decide"
21 passed, 471 deselected in 0.75s
exit: 0

$ uv run --group dev pytest -q tests/test_factory_decisions.py
100 passed in 48.22s
exit: 0

$ uv run --group dev ruff check plugins/factory/scripts/factory.py tests/test_factory_decisions.py tests/test_skills.py
E501 Line too long (113 > 100) --> plugins/factory/scripts/factory.py:2337:101
Found 1 error.
exit: 1

$ uv run --group dev ruff check plugins/factory/scripts/factory.py tests/test_factory_decisions.py tests/test_skills.py && uv run --group dev ruff format --check plugins/factory/scripts/factory.py tests/test_factory_decisions.py tests/test_skills.py
All checks passed!
3 files already formatted
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 218 > /tmp/218-check.log 2>&1; echo "exit: $?"; grep -E "passed|failed|error" /tmp/218-check.log | head -5
exit: 0
All checks passed!
3952 passed, 29 skipped in 251.55s (0:04:11)
✔ Validation passed
✔ Validation passed
exit: 0

$ git log --oneline -1 && git status --short
3bafdfd Close 216-autopilot
 M plugins/factory/README.md
 M plugins/factory/agents/builder.md
 M plugins/factory/scripts/factory.py
 M plugins/factory/skills/decide/SKILL.md
 M tests/test_factory_decisions.py
 M tests/test_skills.py
?? .sdlc/work/218-ask-reviewer-defaults/
exit: 0
