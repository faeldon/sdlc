I built all five outcomes and left them uncommitted on the change's branch. The full gate passes: 2409 tests passed and 13 skipped. I went beyond the Approach in one place: `intake` now flags dangling issues that are waiting on a push, and I raised that as a default decision below.

**Plan:** I wrote `plan.md` (Tier 1, but the work touches many files). After writing it, I added the `intake` change below to it.

**Slices built** (each test seen failing for the expected reason before the fix):
1. **Late responses:** `show()` in `scripts/board.html` numbers each request and ignores any response that isn't for the newest one. Opening a change whose folder is empty also bumps the number, so a late response from the previous change can't overwrite "This folder holds no file yet." `test_a_stale_response_never_paints_over_the_newer_file` runs the page's real `show()` and `paint()` in node and answers the two requests out of order. It also checks that a single request in order still shows its file.
2. **Empty files:** `paint()` shows "This file is empty." in the plain text pane and hides the Raw toggle, since there is nothing raw to show. `test_an_empty_file_says_so` checks this for an empty `.md` file and for an empty file of another kind. Headings, the task-box label and the Raw toggle work as 124 left them.
3. **Spec gate question:** I added `spec_question()` next to `build_question()`. `start … --for spec` now prints it as `question`. The spec skill's Step 2 tells it to ask that printed question word for word, and still shows the question's form, which the dialog tests read. `test_start_words_the_spec_question` checks the wording. A test that asserted "the spec skill asks its own" now asserts that a refused start gets no question.
4. **Findings note:** `templates/findings.md` and `FINDINGS_HEAD` now say the landing's rounds also write findings. I edited both together and rewrapped the note, which is still a `>` note. I reran `sdlc.py record`, `drift` reports nothing, and `test_findings_head_is_the_template` passes. The check "The findings note names the landing" covers the wording.
5. **Triage's dangling bullet:** the half sentence alone wasn't enough, because `intake`'s output gave the skill no way to tell which dangling issue an unpushed commit closes. So `cmd_intake()` now gives each dangling issue a `waits_on_push` flag, using 128's `unpushed_closes()`. The bullet tells triage to leave those issues alone, and `docs/REFERENCE.md` describes the flag. `test_intake_says_a_dangling_issue_an_unpushed_commit_closes_waits_on_the_push` closes a change without pushing and sees the flag `true`, then `false` once the tracking ref holds the commit. The check "Triage's dangling bullet waits on the push" covers the wording.

`checks.md` holds the two wording checks, and both pass. Nothing is left in `notes.md`.

**Decisions raised:**
- DECISION: [default] Should the spec gate's question move into the script, or should seed 2026-11-18-10 be retired? Options: move it; retire it as minor. Going ahead with moving it: it is about ten lines, and every factory gate's question is then worded by the script.
- DECISION: [default] Should the drawer drop a late response with a request counter, or cancel it with `AbortController`? Options: counter; AbortController; match on the path. Going ahead with the counter: matching only on the path still lets another change's `intent.md` show under this one's highlight, and cancelling adds an error case for little gain.
- DECISION: [default] Should `intake` flag dangling issues that wait on a push (`waits_on_push`), beyond the Approach's half sentence? Options: flag in `intake`; wording only. Going ahead with the flag: without it the skill can't tell which issue the bullet means.

## Evidence

$ ./check.sh
2409 passed, 13 skipped in 221.30s (0:03:41)
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_board.py -k "stale_response or empty_file_says"   (before the fix)
FAILED tests/test_board.py::test_a_stale_response_never_paints_over_the_newer_file
FAILED tests/test_board.py::test_an_empty_file_says_so - AssertionError: inte...
2 failed, 152 deselected in 0.63s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k "spec_question or refusal_or_a_spec"   (before the fix)
E       AssertionError: assert None == 'Write this as .sdlc/work/008-reopen-drafts/spec.md and advance the change to stage: design? (yes / revise a requirement / rethink the design)'
1 failed, 1 passed, 276 deselected in 3.21s
exit: 1

$ uv run --group dev pytest -q tests/test_archive.py -k "waits_on_the_push"   (before the fix)
E       KeyError: 'waits_on_push'
1 failed, 145 deselected in 1.81s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py::test_start_words_the_spec_question tests/test_archive.py::test_intake_says_a_dangling_issue_an_unpushed_commit_closes_waits_on_the_push tests/test_board.py::test_a_stale_response_never_paints_over_the_newer_file tests/test_board.py::test_an_empty_file_says_so
4 passed in 15.75s
exit: 0

$ for n in 1 2; do sh -c "<checks.md block n>"; echo "check $n exit: $?"; done
check 1 exit: 0
check 2 exit: 0
exit: 0

$ uv run --quiet --script scripts/sdlc.py record
  wrote  .sdlc/setup.json  (plugin 1.9.0, 3 doc(s))
exit: 0

$ uv run --group dev pytest -q tests/test_defaults.py
121 passed in 20.91s
exit: 0
