---
id: 093
slug: intent-hands-to-factory
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 093 — Intent offers the factory as a way to build the change, with no plan mode · plan

> Written by the factory's builder after reading `skills/intent/SKILL.md`, `cmd_config()`,
> `metrics._reply()`, `tests/test_skills.py`, `tests/test_evals.py`, `evals/scaffold.sh` and the
> `set-up` fixture.

## Files to change

- `scripts/sdlc.py`: new `factory_enabled(home)` (pure reader of three settings files), and
  `cmd_config()` prints its answer as `factory: {enabled, scope}` beside `git`. Reuses
  `main_root()`; reads with `read_text(encoding="utf-8")` and `json.loads`, no subprocess.
- `skills/intent/SKILL.md`: Step 0 notes `factory.enabled`; Step 4 keeps today's forms and adds
  the factory form for each tier (R4, R5); Step 5 skips `EnterWorktree` for
  `yes, for the factory`; Step 6 branches by answer (R6, R7).
- `tests/test_sdlc.py`: `test_config_reports_the_factory_by_scope`,
  `test_config_reports_no_factory_without_settings`, `test_factory_detection_runs_nothing`
  (R1–R3), all `portable`.
- `tests/test_skills.py`: `READS_CONFIG["sdlc:intent"]` gains `factory.enabled` (R10); new
  `test_intent_asks_as_before_without_the_factory`,
  `test_intent_offers_the_factory_when_it_is_enabled`, `test_intent_by_hand_is_the_old_yes`,
  `test_intent_for_the_factory_stays_in_the_main_checkout` (R4–R8).
- `tests/test_metrics.py`: `test_both_intent_yes_answers_read_as_approval` (R9).
- `evals/fixtures/product/` (new): `main` file and `change/`, a copy of `set-up`'s (so
  `readiness` is complete there too) plus `.sdlc/PRODUCT.md` with open `O1` and `O2` about
  drafts, each outcome on one line, as `product_items()` reads only the line it starts on.
- `evals/intent-product/` (new): `case.yaml` tagged `[intent]`, `prompt.md`, `scaffold.sh`
  (`product --sandbox`), graders: the never-* set, `asks-config`, `asks-the-question` with the
  `serving` regex, and a `judgment` grader (R11).
- `tests/test_evals.py`: `STOP_CASES` gains `intent-product: ["new"]`, so the stop-case test
  covers it; `test_every_fixture_passes_check[product]` comes from the glob.
- `AGENTS.md`: one sentence in the factory paragraph on how the core knows it is enabled.
- Docs (R12): `README.md`'s "Factory and manual, change by change"; `plugins/factory/README.md`'s
  `/sdlc:intent` account; `docs/REFERENCE.md`, a `config`'s `factory` subsection.

## Work order

1. **Detection, through `config`.** Tests for R1–R3 red, then `factory_enabled()` and the
   `config` field. Gate.
2. **Intent's question and branches.** Tests for R4–R8 and R10 red, then the skill's Steps 0, 4,
   5 and 6. Gate.
3. **Metrics reads both yeses.** R9's test (expected green at once: `APPROVE_RE` already takes
   `yes, …`; it pins that, so it is seen to fail only by breaking the regex locally).
4. **The product case.** Fixture and case, `STOP_CASES` entry; `test_every_fixture_passes_check`
   and `test_a_stop_case_keeps_every_never_write_grader` red until both exist. Gate.
5. **Docs.** README, factory README, REFERENCE. Gate, `drift`.

## Tests

- R1: `test_config_reports_the_factory_by_scope` (each scope alone; local `false` beats user
  `true`).
- R2: `test_config_reports_no_factory_without_settings` (no files, bad JSON, non-object
  `enabledPlugins`: exit 0, `{"enabled": false, "scope": null}`).
- R3: `test_factory_detection_runs_nothing` (`subprocess.run` patched to raise);
  `test_sdlc_loads_nothing_from_plugins` unchanged.
- R4: `test_intent_asks_as_before_without_the_factory`, and the existing
  `test_spec_and_a_tier_one_intent_start_plan_mode_after_their_wait`.
- R5: `test_intent_offers_the_factory_when_it_is_enabled`; `test_every_gate_offers_two_to_four_answers`.
- R6: `test_intent_by_hand_is_the_old_yes`.
- R7, R8: `test_intent_for_the_factory_stays_in_the_main_checkout` (also asserts no `factory`
  rule in `allowed-tools`); the existing cross-plugin script check.
- R9: `test_both_intent_yes_answers_read_as_approval`.
- R10: `test_skills_read_host_specifics_from_config[sdlc:intent]`.
- R11: `test_every_fixture_passes_check[product]`,
  `test_a_stop_case_keeps_every_never_write_grader[intent-product]`; the paid run is
  `run-cases --tag intent`, named by ship.
- R12: manual, `sdlc.py context` names the docs; ship shows the edits.
- R13: `./check.sh`, `sdlc.py drift`.

## Rollback

`git revert` undoes all of it: `config` only reads the settings files and writes nothing, and the
skill's factory answer creates exactly what the manual one does. Nothing outside the repo is
written or published.
