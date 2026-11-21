# Decisions

- [x] D1 (builder round 1, default): Raise ship's `SKILL.md` line budget from 475 to 480. Going ahead with 480 unless told otherwise. → decided: the assumed default, confirmed when landing
  - OPTION: 480 — the preview clause and the `--preview` call apply on every ship run, so they belong in `SKILL.md`; the budget gives up 5 lines
  - OPTION: keep 475 and move a part only some runs need (say **Bugs fixed**) into a branch file — the budget holds, but `SHIP_BRANCHES` and `preflight`'s `branches` change, outside this change's scope
  - WHY: I tightened Step 5's own prose and it is still 3 lines over (478); the overage is all this change's required text
- [x] D2 (builder round 1, default): For an upgraded run, `start`'s preview gives `spec.md`'s Requirements only once `spec.md` is filled in; while it is still the template `upgrade` wrote, it says the spec-writer's draft holds them. Going ahead with that unless told otherwise. → decided: the assumed default, confirmed when landing
  - OPTION: as built — the preview never shows template prompts as requirements, and the draft's requirements reach the dialog through `agent`'s `preview`
  - OPTION: R6 to the letter, always quoting `spec.md`'s Requirements — matches the spec's wording exactly, but at that point the dialog would show the template's `<…>` prompts
  - WHY: `upgrade` writes `spec.md` as the template, and the spec-writer drafts afterwards, so R6's literal reading would show template text
