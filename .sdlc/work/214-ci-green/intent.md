---
id: 214
slug: ci-green
tier: 1
impact: patch
stage: shipped
created: 2026-11-21
opened: 2026-11-21T11:03Z
updated: 2026-11-21
shipped: 2026-11-21
idea:
depends_on:
fixes: [2026-11-21-28]
serves: [O6]
origin: self
---

# 214 — CI on main passes again on Linux and Windows

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

From bug 2026-11-21-28: every push to `main` since `Close 091-hand-gate-record` (9b21760,
2026-11-17) has failed CI, 123 failed runs, and the last green one is `Close
092-retro-outcome-coverage` (5cb3b26). `./check.sh` passes on macOS every time, so no hand gate,
factory gate or landing train has stopped on it, and four days of changes (091 to 213) landed on a
`main` CI never verified on Windows. 211's landing look ("both jobs pass on the push that lands
it") was accepted on CI's word, and CI was already red.

On 209's push (d2c14ac), 6 tests fail:
- **Windows, the portable job:**
  - `test_hand_gate.py::test_the_build_hash_moves_on_a_rebase_onto_a_moved_base`, the first to
    fail, on 9b21760
  - `test_factory_agent.py::test_the_builder_s_evidence_is_mended_once_a_round`
  - `test_sdlc.py::test_check_leaves_out_the_template_plan_during_a_live_upgraded_build` and
    `test_a_live_first_build_hides_no_other_problem`: `UnicodeDecodeError: 'utf-8' codec can't
    decode byte 0x97`. 0x97 is an em dash in cp1252, so some text read or subprocess has no
    `encoding="utf-8"`, which the Windows invariant requires. A Windows host would hit the same.
  - `test_upstream.py::test_upstream_repo_comes_from_the_manifest`: depends on `gh auth`, which
    the runner doesn't have
- **Linux:** `test_factory_ui.py::test_a_server_that_answered_and_closed_first_has_not_lost_its_port`
  ("port … answered, but the dev server had exited 1"), likely timing-dependent.

## Outcome

- Both CI jobs, Linux and Windows, pass on the push that lands this change, shown by `gh run
  list --branch main` on its landing commit.
- Each of the six failures is fixed at its cause, not skipped or unmarked from `portable`: a
  missing `encoding="utf-8"` is added where the script reads text, a test that needs `gh auth` no
  longer depends on the machine's login, and the port test no longer races.
- Each fix has a test that fails on the cause it fixes, where one can be built on macOS (the
  encoding one by reading a file holding cp1252 bytes, or by the Windows test's own pattern check).
- **Moves O6:** a factory change's landing is checked by CI again, so "the gate passed" and "CI
  passed" stop disagreeing silently.

## Affected

- **Area:** tests, the Windows portability of the scripts, and CI.
- **Files & components:** `tests/test_hand_gate.py`, `tests/test_factory_agent.py`,
  `tests/test_sdlc.py`, `tests/test_upstream.py`, `tests/test_factory_ui.py`, and whichever of
  `scripts/sdlc.py`, `plugins/factory/scripts/factory.py` or `scripts/factory_records.py` holds the
  read without an encoding; possibly `.github/workflows/check.yml` (sensitive).
- **Downstream:** every host on Windows, which runs the same code the portable tests cover; every
  factory landing, whose push CI checks.
- **Contracts:** *The scripts run on Windows* (`tests/test_windows.py`): every text-mode read and
  `subprocess.run` names `encoding="utf-8"`. `.github/workflows/` is `[review] sensitive`.

## Constraints

- No test is deleted, skipped on Windows, or taken out of `portable` to make CI pass, unless the
  test cannot hold on Windows by its nature, said in the test.
- The local gate stays what it is; this change doesn't make it run Windows.
- Fixes go to the cause: a script bug a host would hit is fixed in the script, not the test.

## Open questions

- Why did `test_windows.py`'s encoding check miss the 0x97 read? Is it a read it doesn't scan (a
  `read_text()` with no argument, `open()` in read mode), and should the check widen?
- Are the hand-gate and mend failures Windows path or line-ending bugs in the code, or in the tests?
- Should a landing (or `status`) say when CI on `main` is red, so the local gate isn't the only
  word? That is likely a seed of its own, not this change.

## Approach

Reproduce each failure from its CI log, fix the cause, add the test that pins it, then push
nothing until the landing: the landing's push is the proof. Encoding first (the most likely real
host bug), then the `gh auth` dependency (inject the login as the other upstream tests do), the
hand-gate hash and the mend test (likely path or newline handling), and the port race last.
Widen `test_windows.py` if the encoding read was one it can't see. About six files plus tests.

Nits taken in: 2026-11-21-21, 2026-11-21-23
