Both bugs are fixed and the full gate is green (`./check.sh`: 2663 passed, 18 skipped). The work is uncommitted, ready for review at `/sdlc:ship`.

**What changed:**
- **Bug 2026-11-18-41, `[models]`:** the factory now reads `[models]` only from the base branch's `.sdlc/factory.toml`, the way it already reads `mode`. A setting committed on the base branch now reaches a change whose worktree was made before it. A `[models]` table in the change's own checkout changes nothing, and gives a warning saying it applies once it lands. Bad entries (such as an unknown role) are still warned about, now checked in the base branch's table.
- **Bug 2026-11-18-42, folder citations:** when `factory.py agent` files a reply, the change's own folder cited by bare number becomes its full `NNN-slug` name. That covers `work/NNN`, `work/NNN/…` and the glob `work/NNN*`. This runs right after the existing path marks, so spec drafts get it too. Another change's number, a longer number, and anything already followed by `-` are left as written.
- **README:** says `[models]` is read from the base branch, and that a setting there reaches every open change at once.

**Tests added:**
- `test_models_are_the_base_branch_s_even_for_an_older_worktree`: commits `[models] builder = "fable"` on the base branch after the change's worktree exists. It checks that `start`'s `models_at` shows `fable` at both depths, and that `agent` launches `claude --model fable`. It also checks that the base branch's entries are validated, and that the checkout's own `[models]` is ignored with a warning, which goes away once the two match.
- `test_a_reply_citing_its_own_change_by_number_is_filed_by_its_full_name`: files a reply citing the change in every bare-number form and checks each comes out under its full name. It also checks the forms that must stay untouched, and that `test_nothing_local`'s patterns find nothing in the change's own citations. The test builds those strings from parts, because the scan also reads the test file.

I watched both fail for the expected reason before writing the code (`opus` instead of `fable`; the number left bare).

Two older tests set `[models]` only in the change's checkout, so I updated them:
- `test_config_defaults_and_its_warnings` now expects no models and the "read from the base branch" warning.
- `test_a_host_s_own_depth_and_models_are_kept` now commits its config on the base branch too, through a new `_on_base` helper.

**`plan.md`:** I didn't write one. This is Tier 1 and the Approach touches only `factory.py`, its tests and one README passage.

**`notes.md`:** nothing left there.

**Decision for you:**
- DECISION: [default] Should a `[models]` table in the change's own checkout that differs from the base branch's give a warning? Going ahead with a warning, as `mode`, `gate_jobs` and `[ui]` already do, unless told otherwise.
  - OPTION: warn — same as the other base-branch settings; a person who edits it in a change learns why it has no effect
  - OPTION: ignore silently — less noise; the edit seems to do nothing, with no reason given
  - WHY: the intent's Approach asks for the warning `mode` gives, and it answers the intent's open question the same way the other settings do

## Evidence

$ uv run --group dev pytest -q tests/test_factory.py -k "models_are_the_base or citing_its_own"   (before the fix)
E       AssertionError: assert {'opus'} == {'fable'}
E       AssertionError: assert '$ ls .sdlc/work/008-reopen-drafts/build\n' in 'Built it.\n\n## Evidence\n\n$ ls .sdlc/work/NNN*/build\n…'
2 failed, 330 deselected
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k "models_are_the_base or citing_its_own"   (after the fix)
2 passed, 330 deselected in 0.95s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_factory.py
332 passed in 10.02s
exit: 0

$ ./check.sh
All checks passed!
276 files already formatted
2663 passed, 18 skipped in 91.60s (0:01:31)
✔ Validation passed
exit: 0

The gate is green again (`./check.sh`: 2663 passed, 18 skipped). The code was not at fault: my round-1 report broke the repo's scan for paths cited by bare number.

**What failed:** `test_nothing_in_the_repo_is_forbidden` flagged line 32 of `build/round-1.md`. My Evidence there quoted the red test's output, which held the test fixture's own bare-number glob, a shape the scan refuses. The gate then copied that line into its own record, `build/round-1.gate.md` (line 65). The scan reads every file in the change folder, so that copy would have failed every later gate run as well.

**What I did:**
- I rewrote the citation as `work/NNN*`, the same placeholder the intent uses, in both `build/round-1.md` and `build/round-1.gate.md`. I changed only that one citation in each file and nothing else.
- In the gate record that is the quoted output of attempt 1, not its result. The script reads only the `## Attempt`, `Verdict:`, `Build:` and `Exit:` lines, so what the attempt recorded is unchanged.
- No change to the code, the tests or the gate's config.

**`notes.md`** (new) has one unticked item: a gate record that quotes a line the scan refuses keeps every later gate red. This change rewrites only the change's own number in an agent's reply. The gate's output and other numbers, such as a test fixture's, are not covered. Covering them would be a change of its own.

**Decision for you:**
- DECISION: [default] Keep the hand edit of attempt 1's quoted output in `build/round-1.gate.md`? Going ahead with it unless told otherwise.
  - OPTION: keep the edit — the gate can pass again; one quoted citation in the record differs from what the gate printed
  - OPTION: restore the original line — the record is exactly as the gate wrote it; every gate run on this change stays red until the scan or the filing changes
  - WHY: without the edit no build of this change can pass, and the intent shows the person fixed records the same way by hand on 2026-11-18

Still open from round 1: the `[default]` decision to warn when a change's own `[models]` differs from the base branch's.

## Evidence

$ grep -rnP '\bwork/\d{3,}\b(?!-)' .sdlc/work/144-factory-records-and-models
exit: 1

$ uv run --group dev pytest -q tests/test_nothing_local.py
8 passed in 1.38s
exit: 0

$ ./check.sh
All checks passed!
281 files already formatted
2663 passed, 18 skipped in 91.38s (0:01:31)
✔ Validation passed
exit: 0
