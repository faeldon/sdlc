All four seeds and nine nits from the batch are fixed, and the gate passes: 2832 passed, 28 skipped. The work is uncommitted on the change's branch, ready for `/sdlc:ship`.

It's a Tier 1 change, but it touches more than a couple of files, so I wrote a `plan.md` first.

**Built, test first where there was behaviour to change** (each test was run and seen to fail for the expected reason first):
- **-72, terms quoted in a filed reply.** `factory.py` now reads the main checkout's `.sdlc/terms.local` (through `_all_checkouts()`) and writes any matching term as `<term>`. That covers every reply it files, `defuse`, and the approver's stop, which names only the file and line, never the term. `sdlc.py`'s copy for the hand gate does the same. New test `test_a_reply_quoting_a_local_term_is_filed_as_a_placeholder` files a reply from the change's worktree and finds `<term>`. It also checks that `forbidden_lines` names the line and `defuse` rewrites it. `test_the_placeholders_are_the_factorys` now also pins that the two copies agree.
- **-62.** In `_own_folder()` the `*` can no longer be backtracked off, so `work/NNN*x` is left alone. The existing own-folder test gained that case.
- **-57.** With `sdlc-factory` enabled and no screenshots, `passes.ui.why` now ends with `take them with factory.py shots NNN --round 1 --role ui`, and `skills/ship/ui.md` says the same. Ship never runs it. `test_preflight_passes_ui` checks both the enabled and not-enabled wording.
- **-56.** The "unverified" case now asserts `next == "rework"` as well.
- **-54, -48, -51, -52.** These are wording, comments and a type annotation: the "111 C1" docstring now states the rule it pins, `replies[-1]` has a comment, and `stop_text` uses `list[str] | tuple = ()`. The comment at `status`'s `needs_of` call says which fields it reads for a shipped change. I confirmed `_claude()` really returns at least one reply whenever it reports no problem, so the `replies[-1]` comment is accurate.
- **Docs.** The three ship pass files now say "a factory run, whose own reviewers ran", and `security.md` says "a deep diff". In AGENTS.md, the two agents' `supersedes` sentence and the README paragraph, only line breaks changed: a word-diff ignoring whitespace shows no change. AGENTS.md now has no line past 100 columns. Its one exception to "line breaks only" is in the commands block: one comment now continues on a second `#` line, and one line lost some padding spaces.

**Acceptance checks.** `checks.md` holds three, for things only a deliberate revert could break: AGENTS.md's line length, the wrapped sentences and README paragraph, and the pass files' wording. `sdlc.py accept 150` passes all three.

**`plan.md` changes:** the exact shots command, and the docs now proved by `checks.md`. **`notes.md`** has two unticked items: other lines past 100 columns in the two reviewer agents and in the factory README, which were outside -55's and -63's scope.

- DECISION: [default] For -57, name `factory.py shots NNN --round 1 --role ui` rather than the bare `factory.py shots NNN` the intent wrote, since the bare form is refused. Going ahead unless told otherwise.
  - OPTION: full command — works when pasted as is; a longer `why` in the note and the question
  - OPTION: bare `factory.py shots NNN` — matches the intent's words; fails with a missing-argument error
  - WHY: a pointer the person can't run as written defeats -57
- DECISION: [default] For -72's open question, use a generic `<term>` placeholder, not the term's kind. Going ahead unless told otherwise.
  - OPTION: `<term>` — `terms.local` is bare regexes with no kind to name; nothing else to maintain
  - OPTION: a kind per term — reads better; needs a new format for `terms.local` that the scan would also have to parse
  - WHY: the file holds no kinds, and the intent's constraint is only that a term is never quoted

## Evidence

$ ./check.sh
All checks passed!
280 files already formatted
2832 passed, 28 skipped in 510.85s (0:08:30)
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_factory.py -k local_term   (before the fix)
1 failed, 343 deselected in 1.61s
exit: 1

$ uv run --group dev pytest -q tests/test_hand_gate.py -k placeholders   (before the fix)
E       - built for <term>
E       + built for Stale Widgets
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k own_change_by_number   (before the fix)
E       AssertionError: never backtracked off its `*`
1 failed, 343 deselected in 0.89s
exit: 1

$ uv run --group dev pytest -q tests/test_preflight.py -k test_preflight_passes_ui   (before the fix)
E           AssertionError: {'applies': True, 'why': 'no screenshots of this change', 'shots': []}
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py tests/test_hand_gate.py tests/test_preflight.py -k "local_term or placeholders_are or own_change_by_number or passes_ui or kept_twice or fails_on_its_own"
6 passed, 442 deselected in 51.98s
exit: 0

$ uv run --quiet --script scripts/sdlc.py accept 150
  "passed": true,
  "problems": []
exit: 0

$ git diff -w --word-diff=porcelain AGENTS.md plugins/factory/agents plugins/factory/README.md | grep -cE '^[+-][^+-]'   (the AGENTS.md part of this command ran before the commands-block edit)
0
exit: 1

$ git log --oneline -1
7128522 Close 147-landing-runs-unattended
