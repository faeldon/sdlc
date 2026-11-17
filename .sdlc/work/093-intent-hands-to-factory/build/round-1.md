# Build report: 093-intent-hands-to-factory, round 1

When the factory is enabled for the repo, `/sdlc:intent` now offers `yes, by hand` and `yes, for the factory`. Without the factory, the question is the same as before. The gate passes: 1913 tests, ruff clean, and `plugin validate --strict` passes. Everything is left uncommitted.

I wrote `plan.md` first, then built five slices, writing each slice's test before its code.

## Slices built

1. **Finding the factory (R1–R3).** A new function, `factory_enabled(home)` in `scripts/sdlc.py`, reads `enabledPlugins` from three files, most specific first: the main checkout's `.claude/settings.local.json`, then its `.claude/settings.json`, then `~/.claude/settings.json`. The first file that names any `sdlc-factory@*` decides. A file that is missing or won't parse, or whose `enabledPlugins` isn't an object, is skipped, and the answer defaults to no factory. It runs no subprocess and reads nothing under `plugins/`. `config` prints the result as `factory: {enabled, scope}`; in this repo that is `{enabled: true, scope: project}`.
2. **The intent skill (R4–R8, R10).**
   - **Step 0** now notes `factory.enabled`.
   - **Step 4, factory not enabled:** keeps today's two questions.
   - **Step 4, factory enabled:** adds two questions, one for each tier, with the answers `yes, by hand / yes, for the factory / change the tier / edit a section`.
   - **Step 5:** skips `EnterWorktree` when the answer is `yes, for the factory`.
   - **Step 6:** `yes, by hand` follows the same branch `yes` always has. `yes, for the factory` names `/sdlc-factory:build NNN`, never enters plan mode, and leaves the change at `stage: plan`.
   - No `allowed-tools` rule was added.
3. **Metrics (R9).** A test pins that both new answers count as approval. It passed straight away because the existing regex already accepts them. To see it fail, I briefly took `yes` out of `APPROVE_RE`, then restored the file.
4. **The product case (R11, nit 2026-11-17-6).**
   - A new fixture, `evals/fixtures/product/`: a copy of the `set-up` fixture plus a `.sdlc/PRODUCT.md` with open outcomes O1 and O2 about drafts. The test scaffold doesn't support `extends` for this kind of fixture, so it is a copy.
   - A new case, `evals/intent-product/`, tagged `[intent]`. It has the never-* graders, `asks-config`, an `asks-the-question` grader that requires the `serving` clause, and a judgment grader that fails if the reply asks which outcome the change serves.
5. **Docs (R12).** The README's "Factory and manual" section, the factory README's "Where it sits", and a new `docs/REFERENCE.md` section on `config`'s `factory` object, covering the three files and their order. I also added one sentence to `AGENTS.md`'s factory paragraph, which the spec didn't list. `sdlc.py context` names that file for this diff.

## Tests added

| Test | Proves |
|---|---|
| `test_config_reports_the_factory_by_scope` | R1: each scope on its own; a local `false` beats a user `true`; any marketplace counts; `config` prints it. |
| `test_config_reports_no_factory_without_settings` | R2: no files, bad JSON, or a non-object `enabledPlugins` give exit 0, no warning, no factory. |
| `test_factory_detection_runs_nothing` | R3: still answers with `subprocess.run` and `subprocess.Popen` patched to raise. |
| `test_intent_asks_as_before_without_the_factory` | R4 |
| `test_intent_offers_the_factory_when_it_is_enabled` | R5 |
| `test_intent_by_hand_is_the_old_yes` | R6 |
| `test_intent_for_the_factory_stays_in_the_main_checkout` | R7 and R8, including no rule naming the factory in `allowed-tools`. |
| `READS_CONFIG["sdlc:intent"]` gains `factory.enabled` | R10 |
| `test_both_intent_yes_answers_read_as_approval` | R9 |
| `STOP_CASES["intent-product"]` | R11's stop-case graders; `test_every_fixture_passes_check[product]` comes from the existing fixture glob. |

The unchanged `test_spec_and_a_tier_one_intent_start_plan_mode_after_their_wait` still passes.

## Other files changed

- **`plan.md`** was written before any code. After building, I updated it for the fixture being a copy and for the `AGENTS.md` sentence.
- **`spec.md`**: two wrapped lines began with `<`, which `sdlc.py check` read as an unfilled template. I only re-wrapped them; no words changed. `check --strict` now reports 0 problems.
- **`notes.md`** records those departures from the spec and plan. It has no unticked line, so nothing blocks the land.

## Not run here

The paid skills' cases, `run-cases --tag intent` (`intent` and `intent-product`). Ship names that run.

No decisions raised.

## Evidence

$ ./check.sh > /tmp/093-gate.log 2>&1; echo "exit: $?"; grep -E "[0-9]+ passed" /tmp/093-gate.log; tail -1 /tmp/093-gate.log
exit: 0
1913 passed in 97.85s (0:01:37)
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q -k "factory_by_scope or no_factory_without or detection_runs or intent or both_intent_yes or product or stop_case or cases_are_read" tests/test_sdlc.py tests/test_skills.py tests/test_metrics.py tests/test_evals.py   (with pipefail)
55 passed, 627 deselected in 5.83s
exit: 0

$ uv run --group dev pytest -q tests/test_metrics.py -k both_intent   (with `yes` removed from APPROVE_RE, then restored)
FAILED tests/test_metrics.py::test_both_intent_yes_answers_read_as_approval
1 failed, 108 deselected in 0.03s
exit: 1

$ uv run --group dev pytest -q tests/test_sdlc.py -k "factory_by_scope or no_factory_without or detection_runs"   (before the code)
3 failed, 200 deselected in 0.83s
exit: 1

$ uv run --group dev pytest -q tests/test_skills.py -k "intent"   (before the skill edit)
5 failed, 21 passed, 317 deselected in 0.16s
exit: 1

$ uv run --group dev pytest -q tests/test_evals.py   (before the case existed)
2 failed, 24 passed in 2.35s
exit: 1

$ uv run --quiet --script scripts/sdlc.py drift
"breaking": [], "refresh": [], "report": []
exit: 0

$ uv run --quiet --script scripts/sdlc.py check --strict
■ Problems: 0
    none ✅
exit: 0

$ uv run --quiet --script scripts/sdlc.py config | python3 -c '…["factory"]'
{'enabled': True, 'scope': 'project'}
exit: 0
