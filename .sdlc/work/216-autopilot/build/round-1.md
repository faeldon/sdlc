# Build report — 216-autopilot, round 1

Autopilot is built across all 28 requirements, in five slices, and the full gate is green: 3931 passed, 29 skipped, ruff clean, plugin validate passed. Nothing is committed; `HEAD` is still `9b4eadd`.

A testing caveat: the end-to-end test drives the loop in process, with `run_step` stood in for and a real worktree per seed. That is how the train's own tests work. No test runs the loop's real subprocesses with a fake `claude`.

## Slices built

1. **Who decided (R1–R5, R23).**
   - The lock: `AUTOPILOT_RUN_LOCK`, `AUTOPILOT_RUN_ENV`, and `autopilot_running()`.
   - `--by autopilot` is refused on `land`, `train --begin`, `write-spec` and the new `answer` unless the run's lock is held by another process. The refusal comes before any write.
   - The new `answer` command writes `→ decided by autopilot:`. It works out its own answer: the kept answer for a default, "seen" for a look, the first option for a blocking call. It refuses a blocking call with no option, or one recommending `upgrade to Tier 2`.
   - `read_ledger()` now says who decided each line (`decided_by`).
   - `by=autopilot` is a third value, kept apart from `auto` and `person`, in closing, metrics, retro and factory_records.
2. **Signal kinds and budgets (R24–R26).** `land_signals()` now gives each signal's kind (`SIGNAL_KINDS`), and `land-check` prints them as `signal_kinds`. `review_debt()` and `change_risk()` are computed by the script.
3. **Config, preview, begin (R8–R10, R28).** `[autopilot]` is read from the base branch only. `--preview` writes nothing; `--begin` has the refusals the spec lists; `candidates()` takes only the ready group.
4. **The loop (R11–R19, R21, R22, R27).**
   - New module `autopilot.py` holds the loop. Two new read-only agents (`autopilot-planner`, `intent-writer`) run through `agent --task wave|intent`.
   - Seeds are opened with `idea:` and `opened_by: autopilot`. `vet` reads the key and `status` shows it.
   - The other pieces: waiting on dependencies, `AUTOPILOT_STEPS`, escalations answered and recorded, holds, landing as a train, cancel and resume, and the summary.
5. **Prompts, skill, docs (R6, R7, R20).**
   - A `## autopilot` prompt part for spec, build and approve, sent only under the lock.
   - The `/sdlc-factory:autopilot` skill, with one WAIT. The decide skill lists autopilot's calls.
   - Docs: README, AGENTS.md, REFERENCE.md, FEATURES.md, PROCESS.md.
   - This repo's `[review] sensitive` now lists `autopilot.py`.

## Tests added

Every test the plan names is in `tests/test_autopilot.py` (47 tests), plus:
- `test_landed_by_autopilot_is_its_own_value` (test_metrics)
- `test_auto_landed_counts_autopilot_apart` (test_retro)
- `test_only_autopilot_names_by_autopilot` and `test_autopilot_grants_no_other_skills_writes` (test_skills)
- an autopilot entry in each of test_modules' placement, loading and binding tests
- five golden prompt cases with their recorded copies

Several were not seen red first: R6, R7, R24 and R26 were green on arrival, because the code was written before them. R4's grep was checked against the base branch's code, where it finds 6 matches.

Existing tests I edited: test_retro's `auto_landed` and ledger-count dicts, and test_factory_decisions' ledger record, each to add the new key. The train, land and metrics tests are unchanged.

## Named runs

- `tests/test_autopilot.py`: 47 passed.
- Skills, modules, prompts, metrics, retro, decisions, feature-map and surface tests: 1228 passed.
- Gate (`factory.py check 216`): 3931 passed, 29 skipped.
- `vet --strict`: 0 problems.

## plan.md and notes.md

plan.md now names everything as built, with a **Departures** paragraph. In particular, `autopilot_lock` moved into `autopilot.py` because only it uses the lock, and the landing commands are `TRAIN_COMMANDS`, since `LAND_STEPS` was already taken.

notes.md lists the departures and four open items:
- The board doesn't show autopilot's changes yet (seed 2026-11-21-34 covers that).
- The cheap-nits lines have no seed id, so autopilot never takes them.
- No test runs the loop's real subprocesses.
- The retro's overturn rate is left for a later seed.

- DECISION: [default] Name the weight tables `[autopilot.debt_weights]` and `[autopilot.risk_weights]`; the limits stay `[autopilot] debt` and `risk`. Going ahead unless told otherwise.
  - OPTION: `*_weights` tables — keeps R24/R26's limit names; the table names differ from the spec
  - OPTION: rename the limits to `debt_limit`/`risk_limit` and keep `[autopilot.debt]` — the spec's table names; its limit keys change instead
  - WHY: TOML can't hold `[autopilot.debt]` beside `[autopilot] debt = 40`, so the spec can't be built as written
- DECISION: [default] Don't rerun the approver after autopilot answers open calls at `done` (R17); the landing reads the answered ledger. Going ahead unless told otherwise.
  - OPTION: no rerun — no new gate in `agent`; READY stays the approver's word before the answers
  - OPTION: let `agent --task approve` run again under the lock — R17 to the letter; loosens `TASK_STEP` for one mode
  - WHY: `agent` refuses `approve` once `verdicts` says `done`, which is the same path `/sdlc-factory:decide` follows
- DECISION: [default] A spent debt or risk budget stops new waves, intents and trains, but changes already opened go on to `stage: test`; a spent dollar cap or hours starts no agent session at all. Going ahead unless told otherwise.
  - OPTION: as built — matches the spec's `debt = 1` dry run
  - OPTION: no build round after any limit — R27's "no build round" to the letter; contradicts the dry run
  - WHY: R27 and the dry run disagree; the dry run is the concrete case
- DECISION: [default] `--level` is the highest tier autopilot opens (1 or 2, default 2). Going ahead unless told otherwise.
  - OPTION: highest tier — a real bound the script can check
  - OPTION: drop `--level` — fewer bounds; leaves "the level" unexplained
  - WHY: the intent names a level without defining it
- DECISION: [default] Autopilot disposes of undone notes and nits as the approver proposed, as the person's landing yes does. Going ahead unless told otherwise.
  - OPTION: dispose as proposed — `ship` can go ahead; the dispositions are under autopilot's run yes
  - OPTION: hold any change with undone notes — stricter; holds many changes
  - WHY: `sdlc.py ship` needs each note disposed of, and the yes for this one run covers what the approver proposed
- DECISION: [default] R13 reads `Close` commits through `factory.closes()`, not a `sdlc.py` command. Going ahead unless told otherwise.
  - OPTION: `factory.closes()` — the factory's own reader of the base branch's first-parent line
  - OPTION: add a `sdlc.py` command that prints closed changes — the spec's wording; more surface
  - WHY: no `sdlc.py` command prints them

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q -n auto tests/test_autopilot.py
47 passed in 63.98s (0:01:03)
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_skills.py tests/test_modules.py tests/test_prompts.py tests/test_metrics.py tests/test_retro.py tests/test_factory_decisions.py tests/test_feature_map.py tests/test_surface.py
1228 passed in 93.02s (0:01:33)
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 216
All checks passed!
343 files already formatted
3931 passed, 29 skipped in 244.69s (0:04:04)
✔ Validation passed
exit: 0

$ uv run --quiet --script scripts/sdlc.py vet --strict
■ Problems: 0
    none ✅
exit: 0

$ for f in scripts/closing.py scripts/metrics.py scripts/retro.py plugins/factory/scripts/factory.py plugins/factory/scripts/landing.py; do git show HEAD:$f | grep -cE "\(\s*[\"']auto[\"']\s*,\s*[\"']person[\"']\s*\)"; done
1
1
1
2
1
exit: 0

$ sh -c "grep -q '\"plugins/factory/scripts/autopilot.py\",' .sdlc/config.toml" && echo check1 ok
check1 ok
exit: 0

$ sh -c "test -f plugins/factory/skills/autopilot/SKILL.md && grep -q '^## Step 2 — WAIT for explicit approval\$' plugins/factory/skills/autopilot/SKILL.md" && echo check2 ok
check2 ok
exit: 0

$ git log --oneline -1
9b4eadd Close 215-evidence-exits
exit: 0
