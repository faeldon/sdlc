---
id: 058
slug: setup-stops-when-complete
kind: spec
created: 2026-11-16
updated: 2026-11-16
---

# 058 — Setup stops on a set-up repo before reading its first-setup steps · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1.** `sdlc.py readiness` prints `complete` beside `ready`: true only when every item is `ok`
   or `n/a`, except that `commands.build` and `commands.scan` may be `missing` (unset is a
   choice), and `drift` has nothing in `breaking`, `refresh` or `report`; false with no
   `.sdlc/config.toml`. `tests/test_readiness.py` pins each case that makes it false (a `missing`
   item, a `warn` item, a `breaking`, a `refresh`, a `report` alone such as an unknown config key,
   no config) and one true case (a set-up repo with build and scan unset).
2. **R2.** `readiness` prints `unset`: the items of R1's exception that are `missing`, which a
   complete run lists as the defaults a repo usually sets. Tested both ways.
3. **R3.** `ready`, every item, and every other key keep their meaning; the existing readiness
   tests pass unchanged; `readiness` stays in `READ_ONLY`.
4. **R4.** `skills/setup/drafts.md` holds, moved verbatim from `SKILL.md` (but for R8): Step 0's
   explanation of `drift`'s lists, the `reset <…>` text, and Steps 1–3. No frontmatter, no `WAIT`
   heading, no commit: 056's `test_a_skill_s_side_files_are_named_by_it_and_hold_no_gate` covers
   it unchanged.
5. **R5.** `SKILL.md` Step 0: when `complete` is true and there is no argument, setup says the repo
   is set up, lists `unset`, and stops without reading `drafts.md`. Otherwise (not complete, or the
   argument `product`, `project` or `reset`) it reads
   `${CLAUDE_PLUGIN_ROOT}/skills/setup/drafts.md` before going on. One pointer line stands at each
   cut. A test asserts Step 0 names `complete`, `unset` and the side file's path.
6. **R6.** Step 4 (the WAIT), Steps 5–6 and Out of scope stay in `SKILL.md`; the WAIT's literal
   question is unchanged, pinned by a test.
7. **R7.** `skills/setup/SKILL.md` is at most 150 lines (from 314), held by
   `test_setup_s_skill_stays_under_its_budget`.
8. **R8.** Nit 2026-11-03-16: Step 1 (now in `drafts.md`) reads CI workflow files
   (`.github/workflows/`) and release and install scripts, the candidates Step 2's risky-paths
   question offers. A test asserts Step 1 names them; ship retires the nit.
9. **R9.** `evals/fixtures/set-up/` holds a repo set up for the plugin: `.sdlc/config.toml`
   (`archive.target = "none"`, a `commands.check`, `git.attribution` answered), filled process and
   review docs, `AGENTS.md` and its one-line `CLAUDE.md`, `.claude/settings.json` (the allow rules
   and the attribution object) and the `.gitignore` line. `evals/scaffold.sh` commits it on `main`
   and runs `sdlc.py record`, so `.sdlc/setup.json` matches the plugin that runs the case and never
   goes stale. `tests/test_evals.py` builds it and asserts `readiness` says `complete: true`.
10. **R10.** `evals/setup/` runs `/sdlc:setup` on that fixture, graded: it asks `config`; no
    `Write` or `Edit`; no `Read` of `skills/setup/drafts.md` (`never-reads-drafts`); no commit or
    push. Tagged `setup`, so `cases` scopes it to a diff reaching the setup skill. Covered by
    `test_a_stop_case_keeps_every_never_write_grader` and
    `test_the_never_graders_match_what_they_forbid`.
11. **R11.** `prose_metrics` reports setup's `lines` as `SKILL.md`'s alone and
    `branches: {"drafts.md": …}`; `tests/test_retro.py` asserts it.
12. **R12.** `landing_reach` maps `skills/setup/drafts.md` to `skills: ["sdlc:setup"]`, a case in
    `tests/test_archive.py`.
13. **R13.** `AGENTS.md` names setup's side file and `readiness`'s `complete` beside ship's lookups
    paragraph; `docs/REFERENCE.md`'s `readiness` sentence names `complete`; `docs/CONTRIBUTING.md`'s
    `readiness()` line too.
14. **R14.** `./check.sh` exits 0; `sdlc.py run-cases 058` runs the `setup` case at ship (paid,
    under its prompt).

## Design

**Script.** `cmd_readiness()` already calls `drift(root)` for its `drift` item, which counts only
`breaking` and `refresh`. Keep `found` and compute:

```python
UNSET_IS_A_CHOICE = ("commands.build", "commands.scan")
unset = [i["name"] for i in items if i["name"] in UNSET_IS_A_CHOICE and i["status"] == "missing"]
complete = (
    cfg_file.is_file()
    and all(i["status"] in ("ok", "n/a") or i["name"] in unset for i in items)
    and not (found["breaking"] or found["refresh"] or found["report"])
)
```

`complete` and `unset` go into `out` after `ready`. No new command runs; the `drift` item's own
status is unchanged.

**Skill.** `SKILL.md` keeps the intro, Step 0's bash and a one-line reading of `readiness`,
`config` and `drift`, then the branch: complete with no argument, report and stop; otherwise read
`drafts.md`, then Step 1. Then `## Step 4 — WAIT`, `## Step 5`, `## Step 6`, `## Out of scope`.
`drafts.md` takes the drift explanation, the `reset` paragraph, and Steps 1–3 under their
`## Step N` headings, as 056's side files do. Frontmatter unchanged: every command stays in
`SKILL.md`.

**Who decides.** The script decides whether the repo is complete; the skill decides only the
argument, the person's own input. A table like `SHIP_BRANCHES` isn't worth it for one file and one
condition.

**Fixture.** `scaffold.sh` gains a mode: a fixture with a `main` file (no `branch`) has its
`change/` copied onto `main` and committed, then
`uv run --quiet --script "$here/../scripts/sdlc.py" record`, then a second commit. `--sandbox`
already readies uv before it. `tests/test_evals.py`'s `test_every_fixture_passes_check` takes the
new fixture as is.

## Contracts touched

- **Skills invariant** (`AGENTS.md`): side files are part of their skill, named by `SKILL.md`, hold
  no gate, frontmatter or commit, their commands covered by the rules. `drafts.md` runs no command
  and is named by path; setup's one WAIT stays in `SKILL.md`.
- **Confirm before writing**: nothing moves before the WAIT; a complete run writes nothing and asks
  nothing, as today's prose already says.
- **`readiness` read-only** (`READ_ONLY`, `test_it_writes_nothing`): two computed keys, no new
  command.
- **Always Tier 2: a skill's WAIT step.** The question and what it approves are unchanged (R6).
- **Ship's lookups paragraph** ("whether a branch applies is the script's call"): kept for the
  repo's state (`complete`); the argument stays the skill's, which the `AGENTS.md` edit says for
  setup.
- **Evals** (`test_the_gate_and_ci_never_run_the_skills_cases`): the new case is never run by the
  gate or CI; `test_evals.py` only builds the fixture and runs `readiness` and `check`.
- **Windows rules**: no new subprocess in the script; `scaffold.sh` is sh, as now; the fixture
  test is not `portable`, like the others.

## Alternatives rejected

- **A `setup` lookup combining `readiness` and `drift`**, like `preflight`: `readiness` already
  runs `drift`, so a second command adds a rule and a call for nothing.
- **A `SETUP_BRANCHES` table and a `branches` part**: one file, one condition, and the argument
  isn't something the script sees without a `readiness --arg` flag for a check the skill makes in
  one sentence.
- **Moving Steps 5–6 too**: they follow the WAIT and bind every writing run; side file → WAIT in
  `SKILL.md` → side file again reads worse than the 30 lines it saves.
- **Treating a notes-only `report` as complete**: errs towards true. Today's rule stops only on an
  empty `report`, and a wrong true silently skips a host's setup.
- **Marking unset `commands.build` and `scan` `ok` or `n/a`**: changes what an existing item says;
  `unset` names them instead.
- **A static `setup.json` in the fixture**: stale on every edit to `defaults/`; the scaffold
  records it fresh.

## Verification

```bash
uv run --group dev pytest -q tests/test_readiness.py tests/test_skills.py tests/test_evals.py tests/test_retro.py tests/test_archive.py
uv run --quiet --script scripts/sdlc.py readiness | jq '{ready, complete, unset}'   # this repo: true, true, ["commands.build","commands.scan"]
wc -l skills/setup/SKILL.md                                                       # ≤ 150
./check.sh                                                                        # exit 0
uv run --quiet --script scripts/sdlc.py run-cases 058                             # at ship, paid: the setup case passes
```
