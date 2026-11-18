---
id: 136
slug: factory-rounds-that-catch-enough
kind: spec
created: 2026-11-18
updated: 2026-11-18
---

# 136 — Factory rounds that catch what the landing catches, and stop early on a fault no round can fix · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions checked in the code before designing:

- The light depth's reviewers come from `light_reviewers()` (`plugins/factory/scripts/factory.py:625`). That list is `[light] reviewers` as a host set it, else `DEFAULTS["light"]["reviewers"]` (`["code"]`), with `test` added for a Tier 2 when the full depth has it. `load_config()` records whether a host set the list in `cfg["light"]["chosen"]`.
- The ui and ux reviewers already join a round at either depth once `[ui]` is complete and the diff touches its `paths` (`ui_review()`, `:1131`). This repo's `.sdlc/factory.toml` sets `[ui]` over the board. So 124's ui and ux misses were not caused by a missing reviewer, which leaves the model as the likeliest cause.
- `model_for()` (`:581`) runs `SCALED` reviewers (`code`, `test`, `behaviour`, `ui`, `ux`) on `haiku` for a Tier 1 at the light depth, and on `sonnet` otherwise. A host's `[models]` entry wins over both.
- After a clean rebase, a landing round runs `behaviour` alone (`land_verdict()`, `:4875`). After a resolved conflict or a fix the person asked for, it runs every reviewer at the run's depth. A kept change there is a stop: "ship it by hand".
- A run's rounds count from its newest restart or upgrade (`first` in `loop_state()`). A run whose last allowed round still has kept changes is `exhausted`. `read_decision()` then accepts only an `ESCALATE` with a `## Reconsider the approach` section.
- A gate already stops the run after `GATE_FIXES` (2) failed fixes in one round (`loop_state()`, `:1887`).
- `findings.md` records each agent finding with `Class: <role> review, landing round <n>` when a landing round raised it (`finding_section()`, `:2165`). `retro.py` reads `class` and `disposition` from it (`_review_at()`, `:1442`).
- The inbox seed (`2026-11-18-14`) says 124 and 125 were light rounds on haiku. I did not read their tiers or round files, because closed folders are only in history and this draft reads the worktree alone. The plan's first step reads them from their `Close` commits (R6).

R1 and R2 are the default changes. They stand only if the person accepts today's evidence (see the open questions). Every other requirement stands either way.

1. **R1. The light depth runs `behaviour` beside `code` unless a host set `[light] reviewers`.**
   - `light_reviewers()` adds `behaviour` at either tier when `[light] reviewers` is unset and the full depth's `reviewers` holds it. This is the same rule that adds `test` for a Tier 2.
   - A Tier 1 change's light run expects `code, behaviour`. A Tier 2's expects `code, test, behaviour`, in `REVIEWERS` order.
   - `test_a_light_round_includes_the_behaviour_reviewer` fails if a Tier 1 light round is complete without `behaviour.md`.
   - `test_a_set_light_list_is_kept_at_either_tier` (existing) still passes with `[light] reviewers = ["code"]` set: that host gets `code` alone.
   - `test_the_behaviour_reviewer_never_deepens_a_light_run` fails if a light round holding `behaviour` makes `depth()` say `full`.
2. **R2. Scaled reviewers run on `sonnet` at both depths and both tiers, unless `[models]` names them.**
   - `model_for()` drops its `haiku` branch.
   - The parametrised `test_reviewers_scale_with_the_change` cases (`tests/test_factory.py:2010`) are rewritten to expect `sonnet` for `("code", 1, "light")`. The test fails if `haiku` comes back.
   - A `[models] code = "haiku"` still yields `haiku`, pinned by the existing test at `:2138`, which is rewritten to set it explicitly.
3. **R3. A change the verifier kept in two consecutive rounds of one run escalates at once.**
   - Two rounds are consecutive when both are at or after the run's `first` round. "The same change" means the same `(role, change)` as `read_verified()` resolves it.
   - When round N's kept list has such a change, `loop_state()` names `approve` rather than `rework`, even though rounds remain. Its `exhausted` is true, and a new field `stuck` lists the repeated `role: change` lines.
   - `test_a_change_kept_twice_escalates_before_the_rounds_run_out` fails if a two-round fixture on a 3-round run says `rework`.
   - The test also fails if `read_decision()` accepts a `READY` for that run.
4. **R4. Reviewers re-raise an undone kept change word for word.**
   - In round N+1, each reviewer's prompt (`_task()`'s `review` branch) tells it to raise again, word for word, any change kept last round that the rework didn't make. Each `plugins/factory/agents/reviewer-*.md` that reads kept changes says the same.
   - `test_the_review_prompt_asks_for_an_undone_kept_change_word_for_word` fails if the prompt loses that sentence.
5. **R5. A builder report that says a requirement can't be tested ends the run's rework.**
   - The newest `build/round-<N>.md` may hold `- UNTESTABLE: <requirement>: <why>` lines (`UNTESTABLE_RE`).
   - Once that round has been gated, reviewed and verified as any round is, `loop_state()` names `approve` rather than `rework`. Its `exhausted` is true and `untestable` lists the lines.
   - `test_an_untestable_requirement_escalates_after_its_round` fails if such a round with kept changes goes to `rework`.
   - The same test fails if a round whose reviews all `PASS` reaches `approve` with `exhausted` false.
6. **R6. The defaults' reasons are written down.**
   - `plugins/factory/README.md` gets a short note under *Configuration* giving the evidence and reason for each changed default, or for keeping each one. Its rules for the depth and the models follow R1 and R2.
   - The note includes a table of the landed factory changes read (124, 125, 129, 131). For each, it gives the round count, depth, tier, the reviewers and models that ran, what the landing kept, and which reviewer at which model would have caught it in a build round.
   - The plan's first slice reads these from each change's `Close` commit (`git show <sha>:.sdlc/work/<name>/…`).
   - `test_readme_names_the_light_reviewers_and_models` fails if the README's light-reviewer or model rule disagrees with `light_reviewers()` and `model_for()` on a Tier 1 light run.
7. **R7. The approver's prompt says why a run stopped early.**
   - When `stuck` or `untestable` is set, the `approve` prompt names the repeated changes or the untestable lines.
   - The prompt also asks the approver to name, under `## Reconsider the approach`, the next step it would take: a requirement to rewrite, a model to try, or an approach to change.
   - `test_an_early_escalation_names_its_reason_to_the_approver` fails if either is missing from the prompt.
8. **R8. `/sdlc:retro` counts landing catches.**
   - The escapes section's findings table gets one line: `Landing catches: k of n factory-reviewed changes`.
   - `n` is the window's changes whose `findings.md` holds any finding `By:` a factory role. `k` is those of them holding an `important` finding whose `Class:` names a landing round, with disposition `fixed` or `recorded`.
   - `test_retro_counts_a_landing_catch_once_per_change` fails if a change with two such findings counts twice, or if a build-round finding counts.
9. **R9. Nothing a host set changes.**
   - A host `factory.toml` with `rounds`, `[light] reviewers`/`rounds` and `[models]` set gives the same `start` output (reviewers, light, `models_at`, `max_runs`) before and after.
   - `test_a_host_s_own_depth_and_models_are_kept` fails if any of those values differs.
10. **R10. The build question still names what a yes approves.**
    - `build_question()` names the light reviewers R1 gives and the unchanged `max_runs`.
    - `test_the_build_question_names_the_base_branch_s_gate_and_light_depth` (existing) is updated to expect `code and behaviour` in the light parenthesis for a Tier 1. It fails if the question and `light_reviewers()` disagree.

## Design

**Defaults (R1, R2).**
- `DEFAULTS["light"]["reviewers"]` stays `["code"]`. The extra reviewer is added in `light_reviewers()`, after the `chosen` check, the way `test` already is: `wanted = {*light["reviewers"], "behaviour"} | ({"test"} if tier == 2 else set())`. Each one is added only if `cfg["reviewers"]` holds it, and the result is ordered by `REVIEWERS`.
- Keeping the extra reviewer out of `DEFAULTS` means `chosen` stays the one signal that a host set its own list. A host whose full depth drops `behaviour` never gets it at the light depth.
- `depth()`'s `beyond` check already subtracts `light_reviewers()`, so a light round holding `behaviour` doesn't deepen the run.
- `model_for()` becomes `cfg["models"].get(role) or ("sonnet" if role in SCALED else FIXED_MODELS[role])`. The `tier` and `level` parameters stay, because `cmd_start`'s `models_at` and other callers pass them. The docstring says both now give the same answer.
- `max_runs()` is unchanged. It counts the full depth, which with the defaults still has more reviewers than light (4 against 2 or 3).

**Why `behaviour`, and why `sonnet`.**
- 125's miss was `behaviour`'s. The landing runs `behaviour` on every rebase, so putting it in the light rounds moves the landing's own first check into the build, where a kept change costs a rework rather than a hand ship.
- 124's misses were ui and ux. They already ran at the light depth (on the board's paths), and on haiku for a Tier 1, so only the model can close that gap.
- 129's miss was `test`'s. If 129 was a Tier 2, `test` already ran there and the model is again the lever. If it was a Tier 1, R1 doesn't cover it. R6's table settles which.
- A third light round changes nothing for these cases, because their rounds passed rather than running out.

**Early escalation (R3, R5, R7).**
- `loop_state()` computes, after the existing state and only from round files:
  - `stuck`: the `role: change` pairs in `last["verified"]["kept"]` that also appear in the kept list of round `last["round"] - 1`, when that round is `>= first`. Restarts and upgrades start fresh because `first` moves.
  - `untestable`: the `UNTESTABLE_RE` lines of `build/round-<last["round"]>.md`. That file is the report the last complete round reviewed, and it is already read for `## Evidence`.
- `exhausted` becomes `exhausted or bool(stuck) or bool(untestable)`, set only once the last round is complete and verified (or all `PASS`). It is fed into `read_decision()` the same way, so the existing `ESCALATE` + `RECONSIDER` rule enforces the stop with no new decision shape.
- The `rework` branch gets the extra condition `and not stuck and not untestable`. The `approve` branch already carries `exhausted`.
- `out["stuck"]` and `out["untestable"]` are added to the `verdicts` JSON. `step_text`, `stop_text` and the board read neither, so their parsing copies don't move.
- `_task()`'s `approve` branch builds on the existing `exhausted` sentence. With `stuck` set, it says: "Round N kept again what round N-1 kept: …; nothing a further round does will change it." With `untestable` set: "The builder reports these requirements can't be tested: …". Both add: "Under `## Reconsider the approach`, name the next step you'd take: a requirement to rewrite, a model to try, or an approach to change."
- `plugins/factory/agents/builder.md` documents `- UNTESTABLE:`. It is for a requirement no test the repo can run could show: one judged by eye, or one that needs a live service. It never replaces a test the builder chose not to write. The approver and then the person see it, so the only effect of a wrong claim is an escalation, never a `READY`.

**Matching "the same change" (R3, R4).**
- R3 matches by the reviewer's text as `read_verified()` resolves it, which is exact. R4 makes that match reliable: a reviewer is already told "Kept last round: <role>: <change>", and is now told to repeat an undone one word for word, as it already does for handed nits.
- A reworded repeat is missed, and the run falls back to today's cap, never to a wrong escalation.

**Retro (R8).**
- `_review_sources()` already walks each change's findings. A sibling, `_landing_catches(changes, review)`, uses the same `review` reader:
  - `n`: changes with any finding whose `by` is in `sdlc.AGENT_ROLES`.
  - `k`: those of them with a finding of rank `important`, `class` ending `landing round <n>`, and disposition in `fixed`/`recorded`.
- `_sources_text()` prints the line under its table. The rendered key stays `{{escapes}}`, so `TEMPLATE_READS` doesn't change and no `sdlc.py record` is needed.
- A factory run with no findings at all isn't in `n`, so the rate can only read high, never hide catches.

**Mid-run changes.** A run already under way when this lands picks up R1 at its next reading: a light round without `behaviour` reads incomplete, and `verdicts` says `review` with `missing: ["behaviour"]`. That costs one agent run and loses no work.

## Contracts touched

- **`verdicts` decides from the rounds alone and reads no state file but `runs/mended`.** `stuck` reads `verified.md` and `untestable` reads `build/round-<N>.md`. Both are round files `loop_state()` already reads. No `runs/` file is read.
- **Depth comes from the diff against the base branch's `[review] sensitive`, and a run never lightens.** R1 changes which reviewers the light depth expects, never which depth runs. `depth()`'s `beyond` uses `light_reviewers()`, so `behaviour` there never deepens a run, and the R1 test pins that.
- **Settings are read from the base branch, so a change can't widen or lighten its own run.** This applies to `mode`, `gate_jobs`, `[land]` and `[ui]`. `reviewers`, `rounds`, `[light]` and `[models]` are read from the checkout (`load_config()`), as today, and this change doesn't alter that.
- **A host that set `rounds`, `[light]` or `[models]` keeps it** (intent constraint). R1 sits behind `chosen`, R2 behind `cfg["models"]`, and R9 pins both.
- **The build question names the reviewers, rounds and run ceiling** (intent constraint). R10 covers it. `max_runs` is unchanged.
- **The landing's reviews stay a second look** (intent constraint). `land_verdict()` is not touched.
- **Only the current `decision.md` is a run's decision; an exhausted run must ESCALATE with `## Reconsider the approach`.** The early stop reuses that rule. It adds no new decision shape and no new state file.
- **Agents that judge have no Write; only the builder edits.** `- UNTESTABLE:` is text in the builder's own report. Reviewer prompt edits add no tool.
- **`metrics.py` trailers are a contract.** Not touched. R8 reads `findings.md` only.
- **`Sdlc-Findings` counts agents only under `agents=`** (REVIEW.md). R8 counts only `By:` factory roles, and only in its own line, never in ship's counts.
- **The scripts run on Windows.** No new subprocess call. Every new `write_text` passes `newline="\n"`.

## Alternatives rejected

- **Moving `test` into every light round.** For a Tier 1 there are no numbered requirements to read tests against, and the reviewer would judge against the intent's Approach alone. R6's table decides whether 129 needs it. If it does, that becomes a follow-up, not a guess made here.
- **A third light round, or raising `rounds`.** The misses came from rounds that passed, not rounds that ran out. A third round of the same reviewers on the same model adds cost without sight.
- **Choosing reviewers by what the diff touches, beyond `[ui] paths`.** That needs a second path list per reviewer in `factory.toml`, and a host to keep it. `behaviour` runs on any change at the landing already, so it gets no list here.
- **Running every landing reviewer in the build's light rounds.** That would be the full depth under another name. Sensitive paths already buy it.
- **Detecting "the same error" from two red gates' failing tests.** The gate is a host's command, and its output has no shape the script can parse a test name from. The gate already stops after `GATE_FIXES` red fixes in a round.
- **Matching a repeated change by its `path:line` lead.** Line numbers move with every rework. Matching by lead would escalate on two different findings at one line.
- **Letting the verifier or the test reviewer declare a requirement untestable.** Neither writes tests. The builder is the one who finds it can't write one, and its claim goes straight to the approver and the person, so trusting it can only cost an escalation.
- **Measuring first and changing no default.** This is a real choice, left to the person (open questions). R3–R5 and R7–R10 stand either way.

## Verification

```bash
uv run --group dev pytest tests/test_factory.py -q -n auto
uv run --group dev pytest tests/test_retro.py -q -n auto
./check.sh
```

Healthy output:
- The `pytest` runs pass, with the new tests named in R1–R10 among them.
- `./check.sh` passes: ruff check, ruff format --check, pytest -n auto, and `claude plugin validate --strict`.
- `uv run --quiet --script plugins/factory/scripts/factory.py start <NNN> --for build`, on a Tier 1 change in a repo with `[review] sensitive` set, shows `light.reviewers` as `["code", "behaviour"]` and `models_at.light.code` as `sonnet`, and its question names `code and behaviour`.
- `verdicts` on a fixture whose rounds 1 and 2 keep the same `code:` change, with `rounds = 3`, prints `"next": "approve"`, `"exhausted": true` and a non-empty `stuck`.

Boundaries:
- **Always:** keep a host's `rounds`, `[light]` and `[models]`, and decide the early stop from round files alone.
- **Ask first:** dropping R1 and R2 if the person wants a window of data before any default moves.
- **Never:** touch `land_verdict()`'s reviewers, `max_runs()`'s formula, the metrics trailers, or ship's `Sdlc-Findings` counts.

