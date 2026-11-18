I built all six slices of 143. Everything is uncommitted on the change's branch, waiting for `/sdlc:ship`. `./check.sh` passes: 2601 passed, 18 skipped, ruff clean, and the plugin validates. `sdlc.py drift` reports nothing.

**Slices built** (plan.md is written to the build, nothing departed from it):
1. **Security and behaviour passes.** Preflight gains a `passes` part that says whether each extra pass applies, and why not. Security applies on a deep diff, behaviour on a Tier 2 change with a filled spec, and neither on a factory run. Two new branch files: `skills/ship/security.md` and `behaviour.md`.
2. **The UI pass.**
   - `[ui]` is read only from the base branch's `.sdlc/factory.toml`.
   - `_current_shots()` lists the newest set of screenshots that finished, has every PNG, and is newer than every changed page; otherwise `why` says which of those failed.
   - New branch file `skills/ship/ui.md`. Ship never takes a screenshot itself.
3. **Findings.**
   - The new reviewers' findings are marked `ship-security`, `ship-behaviour`, `ship-ui` or `ship-ux`, and count as ship's own, never under `agents=`.
   - The trailer gains `passes=` and `passes_wrong=` after `agents=`; everything before `agents=` is unchanged.
   - The note gains four lines: `Security review:`, `Behaviour check:`, `UI review:`, `UX review:`.
   - A final `## Evidence` section is read as evidence, not as a finding.
4. **Ship's refusal and question.** `sdlc.py ship` refuses when a pass applies and its note line is missing, naming the line. A `skipped, <why>` line still ships. The question names the passes that ran in one clause and each skip with its reason. With no pass applying it is word for word what it was.
5. **The agents.** Three new read-only agents, `agents/security.md`, `ui.md` and `ux.md`, each with only `Read`, `Grep` and `Glob`. A new root `NOTICE` carries the MIT notice, since `security.md` adapts the factory's security reviewer.
6. **The rest.**
   - `SKILL.md` names the three new files and its report says which passes ran; it is still exactly 475 lines.
   - Retro lists ship's passes between `fresh` and the factory roles.
   - The findings template is updated, with the factory's copy of it kept identical.
   - The guide's *Review dimensions*, REFERENCE.md and AGENTS.md (R24) are rewritten, and `sdlc.py record` was rerun.
   - New eval case `evals/ship-behaviour/` with fixture `evals/fixtures/built-tier2/`. Scaffolding it and running preflight names `behaviour.md`.

**Tests added:** every test the spec names under R1–R23, plus four more: one for a set with a problem or a missing PNG, one that a pass that doesn't apply needs no line, one for the question through the command, and one that the core NOTICE exists. All of them failed before their code went in. The UI ones I already had code for, so I proved them by mutation: reading `[ui]` from the checkout turned `test_ui_is_read_from_the_base_branch` red, dropping the staleness check turned `test_stale_shots_are_not_current` red, and changing one `[ui]` default turned the pin red.

**Existing tests I changed**, because they pinned shapes this spec extends (also listed in `notes.md`):
- every exact trailer string gains ` passes=0 passes_wrong=0`;
- the `By:` error message and the `FINDING_BY` pin gain the four `ship-*` values;
- the record for a missing findings.md gains `passes` and `evidence`;
- the deep-diff ship test now needs a `Security review:` line too;
- `test_sdlc_loads_nothing_from_plugins` now allows the three new agents beside the reviewer;
- the factory carry test's trailer ending.

**Left in `notes.md`:**
- One unticked item: how a hand-built change gets its screenshots. `factory.py shots <NNN> --round <n> --role ui|ux` already works from the change's own worktree, but ship doesn't say so. The decision below covers it.
- The example question in `SKILL.md`, the one sentence a test pins word for word, shows no pass clause. Adding one would break the 475-line budget.

- DECISION: [default] Should ship's UI skip reason point a person at `factory.py shots` when there are no screenshots? Going ahead with no pointer unless told otherwise.
  - OPTION: no pointer — ship never names a command that starts a dev server; a person has to know the factory's command to get the UI review
  - OPTION: name `factory.py shots <NNN> --round 1 --role ui|ux` in `passes.ui.why` when sdlc-factory is enabled — the UI review is one step away; ship's text then points at a command that starts a server
  - WHY: the spec leaves how a hand-built change gets screenshots open, and the constraint that ship never starts a server argues for not steering toward one

## Evidence

$ ./check.sh
All checks passed!
279 files already formatted
2601 passed, 18 skipped in 102.57s (0:01:42)
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_preflight.py tests/test_findings.py tests/test_hand_gate.py tests/test_skills.py tests/test_retro.py tests/test_defaults.py tests/test_evals.py -n auto
840 passed in 16.25s
exit: 0

$ uv run --group dev pytest -q -m portable -n auto
469 passed, 18 skipped in 32.11s
exit: 0

$ uv run --quiet --script scripts/sdlc.py drift
{'breaking': [], 'refresh': [], 'report': []}
exit: 0

$ uv run --quiet --script scripts/sdlc.py check --strict
■ Problems: 0
    none ✅
exit: 0

$ uv run --quiet --script scripts/sdlc.py preflight 002   (in the scaffolded built-tier2 fixture)
{'security': {'applies': False, 'why': 'the diff touches no sensitive path'}, 'behaviour': {'applies': True, 'why': None}, 'ui': {'applies': False, 'why': "the base branch's .sdlc/factory.toml has no complete [ui]"}} ['behaviour.md']
exit: 0
