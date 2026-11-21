DECISION: READY

**Why:** All 13 requirements are built. The code, test and behaviour reviewers each returned PASS in round 1, and the gate record is green (3763 passed). The only findings are low-severity nits. The spec's one policy widening, the AGENTS.md *Skills* invariant, was approved with the spec and was built as approved. Nothing in the reviews suggests the spec was wrong.

**Open items**
- NIT (code): `--preview` accepts the clause flags but ignores them without saying so. It should refuse them or say so in its help text.
- NIT (code): ship's commit message counts toward the 40-line preview cut, but `SKILL.md` doesn't say so.
- NIT (test): the `PREVIEW_NAMES` words are matched by substring, so a short word like `path` matches loosely.

**Decisions to confirm**
- CONFIRM: D1: The build assumed ship's `SKILL.md` line budget moves from 475 to 480. The 5 lines are this change's required preview text, which applies on every ship run. The alternative is a `SHIP_BRANCHES` move outside this change's scope. It is a small, easily reversed repo constant, so the person's yes at the landing is enough.
- CONFIRM: D2: For an upgraded run, `start`'s preview shows `spec.md`'s Requirements only once `spec.md` is filled in. While it is still `upgrade`'s template, the preview says the spec-writer's draft holds them. This departs slightly from R6's wording. The code and `agent`'s `preview` show the draft's Requirements, so the dialog never shows template `<…>` prompts. The person can weigh that from the landing's question.

**For the person at ship**
- Look first at `build_preview` and `cmd_start` in `plugins/factory/scripts/factory.py`.
- Then look at `cmd_ship_preview` in `scripts/sdlc.py`.
- Then look at ship's Step 5 in `skills/ship/SKILL.md`, which now has the preview clause and the `--preview` call.
- The widened *Skills* invariant in `AGENTS.md` (the yes options carry the draft as their `preview`) was approved in `spec.md` under *Contracts touched*, and was built as approved.
- No question or answer text changed. Check 1 in `checks.md` shows this, and the reviewers expect it to pass.

- IMPACT: minor — every WAIT's yes options now show the draft as their preview, and `preflight --preview` and the `start` and `agent` previews are new. Nothing anyone holding the previous release needs to do differently.

**Undone items**
- UNDONE: AGENTS.md's *Skills* invariant lists the skills that write and owe a WAIT, but leaves out `update`, which `tests/test_skills.py`'s `GATED` includes. Found while building 210; left as it was, since naming it is a separate edit to the list. → seed: Add `update` to AGENTS.md's Skills invariant list of WAIT skills
