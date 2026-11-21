Change 210 is built and left uncommitted on its branch for `/sdlc:ship`. Every WAIT's yes options now carry what that yes writes as their dialog `preview`. The full gate passes: 3763 tests, lint clean, plugin validation OK.

**What was built**, in the order of `plan.md`:
1. **The 40-line cut (R4).** `sdlc.py` and `factory.py` each get `PREVIEW_LINES = 40` and the same `_preview_cut()`. Past 40 lines it ends `… <k> more lines in <path>`, or `…, shown above` when no file holds the rest. I made one line singular (`… 1 more line`); the spec left that to the plan. A test checks the two copies are identical.
2. **`preflight <NNN> --preview` (R7, R12).** It prints each finding as `F<n> <rank> → <disposition>: <title>` (or `Findings: none`), every path the diff touches (a rename as `R old → new`), and the stamp line. It writes nothing and refuses a bad `findings.md` with the same message `--question` gives. Using it together with `--question` is refused. `--question`'s output is byte-for-byte unchanged, and so is `preflight`'s JSON: I pulled the diff reading and the findings refusal into two shared helpers, `_diff_rows()` and `_readable_findings()`.
3. **The spec draft's preview (R5).** The JSON `agent --task spec` returns, including after `--recheck` and `--revise`, gains `preview`: the draft's `## Requirements`, cut against `runs/spec-draft.md`.
4. **`start`'s preview (R6).** `start --for build` gains `preview`: the gate, each depth's rounds and reviewers, `max_runs`, every role's model at each depth, and a restart's archive and round or an upgraded run's record. `--for spec` and any refused start give `preview: null`.
5. **The 20 WAITs (R1–R3, R8–R10).** Each gets the preview clause, naming what its yes writes per R9's table, the cut sentence, and the text fallback "right after what the preview holds". Retro says "The rating has no preview". Ship, the factory's spec and build, and land each point at their script's output. Ship's Step 5 now also runs `preflight <NNN> --preview`.
6. **Docs (R13).** `AGENTS.md`'s *Skills* invariant, `docs/CONTRIBUTING.md`'s **One approval per writing skill**, and `docs/REFERENCE.md`'s `preflight` paragraph. The factory's build and spec skills now name the new `preview` keys where they describe the JSON.

**Tests added**, each seen failing for the expected reason before the code went in:
- R1–R3: `test_every_wait_asks_in_a_dialog`, widened.
- R8–R9: `test_every_wait_names_its_preview` and `test_every_gated_skill_names_its_preview`.
- R10: `test_retros_rating_has_no_preview`.
- R4: `test_preview_cut_keeps_forty_lines` and `test_preview_cut_is_a_pinned_copy`.
- R7, R12: six `test_preflight_preview_*` tests.
- R5: `test_spec_agent_reply_previews_requirements` and `test_a_long_spec_preview_is_cut`.
- R6: five `start` preview tests in `test_factory_depth.py`.

The existing question, answer, metrics and evals tests pass without edits (R11), except that `test_ship_s_skill_stays_under_its_budget` moved from 475 to 480 lines (see below). `checks.md` has two acceptance checks: no quoted question line changed (R11), and the docs' sentences are present (R13). I ran both blocks directly rather than through `accept`: both exit 0 and leave the tree unchanged.

**Where the build departed from `plan.md`** (the plan is updated to match): the helper names; `build_preview()` takes a third argument, the upgraded run's spec text, from a new `_upgraded_spec()`; ship's budget; and the factory skills' JSON wording.

**`notes.md`:** one unticked item. `AGENTS.md`'s list of WAIT skills leaves out `update`, which the tests already count. That gap was there before this change, so I left it.

- DECISION: [default] Raise ship's `SKILL.md` line budget from 475 to 480. Going ahead with 480 unless told otherwise.
  - OPTION: 480 — the preview clause and the `--preview` call apply on every ship run, so they belong in `SKILL.md`; the budget gives up 5 lines
  - OPTION: keep 475 and move a part only some runs need (say **Bugs fixed**) into a branch file — the budget holds, but `SHIP_BRANCHES` and `preflight`'s `branches` change, outside this change's scope
  - WHY: I tightened Step 5's own prose and it is still 3 lines over (478); the overage is all this change's required text
- DECISION: [default] For an upgraded run, `start`'s preview gives `spec.md`'s Requirements only once `spec.md` is filled in; while it is still the template `upgrade` wrote, it says the spec-writer's draft holds them. Going ahead with that unless told otherwise.
  - OPTION: as built — the preview never shows template prompts as requirements, and the draft's requirements reach the dialog through `agent`'s `preview`
  - OPTION: R6 to the letter, always quoting `spec.md`'s Requirements — matches the spec's wording exactly, but at that point the dialog would show the template's `<…>` prompts
  - WHY: `upgrade` writes `spec.md` as the template, and the spec-writer drafts afterwards, so R6's literal reading would show template text

- UNTESTABLE: none

## Evidence

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 210
All checks passed!
3763 passed, 29 skipped in 223.73s (0:03:43)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_modules.py -k preview
3 passed, 32 deselected in 0.43s
exit: 0

$ uv run --group dev pytest -q tests/test_preflight.py
61 passed in 16.87s
exit: 0

$ uv run --group dev pytest -q tests/test_factory_agent.py -k "preview or spec_draft"
4 passed, 97 deselected in 4.98s
exit: 0

$ uv run --group dev pytest -q tests/test_factory_depth.py -k "preview or question"
21 passed, 35 deselected in 7.91s
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py -k "wait or gate or preview or publish or bug_shows or ship"
164 passed, 309 deselected in 0.25s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_metrics.py tests/test_evals.py
261 passed in 3.98s
exit: 0

$ sh -c '! git diff "$(git merge-base HEAD main)" -- skills plugins/factory/skills | grep -E '"'"'^[-+]> `'"'"''
exit: 0

$ sh -c '<checks.md R13 block: four grep -q lines over AGENTS.md, docs/CONTRIBUTING.md, docs/REFERENCE.md>'
exit: 0
