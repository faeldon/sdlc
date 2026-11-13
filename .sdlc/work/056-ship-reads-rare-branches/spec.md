---
id: 056
slug: ship-reads-rare-branches
kind: spec
created: 2026-11-13
updated: 2026-11-13
---

# 056 — Ship reads its rare branches only when preflight says they apply · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. Six branch files exist beside `skills/ship/SKILL.md`: `factory.md` (agent verdicts, Steps 0 and
   4), `undone.md` (undone items, Steps 4 and 6), `closes.md` (issues it closes, Steps 4 and 6),
   `recover.md` (How to recover, Step 4), `fresh.md` (the fresh-context review, Step 3) and
   `cases.md` (the skills' cases, Steps 1 and 3), each holding that branch's text for every step it
   touches, under one `## Step N` heading per step.
2. `SKILL.md` keeps the one `WAIT` heading, Step 5 as it stands (flags, answers, the full sample
   question), the preflight part list, and every rule that binds every run: Pre-existing bugs,
   nits, `fixes:`, acceptance checks and the fix-first flow. Where a branch was cut, one line names
   the file that holds it.
3. `skills/ship/SKILL.md` is at most 475 lines, down from 543; `notes.md` records the final line and
   byte counts.
4. No branch file holds frontmatter or a heading containing `WAIT`, and none runs `git commit` or
   `sdlc.py ship`.
5. `preflight <NNN>` prints a `branches` part: the files that apply, in R1's order. `factory.md` when
   `decision.md` exists in the change's folder, `undone.md` when `undone.items` is non-empty,
   `closes.md` when `closes.closes` is, `recover.md` when `risk.irreversible` is, `fresh.md` when
   `risk.deep` is true, `cases.md` when `cases.available` and its `scope` is non-empty. A plain change
   gets `[]`. `tests/test_preflight.py` has one case per file and the plain one.
6. Step 0 of `SKILL.md` says to read each file `branches` names, at
   `${CLAUDE_PLUGIN_ROOT}/skills/ship/<file>`, before going on, and no other; the skill never decides
   for itself whether a branch applies.
7. `SHIP_BRANCHES` in `sdlc.py` is the one table of file → condition; a test fails when its keys
   differ from the files in `skills/ship/` other than `SKILL.md`.
8. `tests/test_skills.py` reads each skill as its `SKILL.md` plus every other `*.md` in its folder:
   every bash command across them has an `allowed-tools` rule in the frontmatter, every rule is used
   in them, every script call goes through `uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/…`,
   and `accept` and `run-cases` get no rule.
9. Every side file is named by its own `SKILL.md`, and every file `SKILL.md` names exists: a stray or
   a dangling name fails.
10. The existing ship tests (agent verdicts, issues it closes, the reviewer spawn, nits, attribution,
    context) keep their assertions, reading the file the text moved to, and also assert `SKILL.md`
    names that file at the step it came from. The text-wide checks in `test_work_folder.py` and
    `test_defaults.py` glob `skills/*/*.md`, so a side file can't escape them.
11. `prose_metrics()` reports a skill's `lines`/`bytes`/`est_tokens` for `SKILL.md` alone (what every
    run reads), adds `branches` with each side file's sizes, and counts `commands` and
    `script_calls` across all its files, so retro's skill size keeps its meaning and gains the split.
12. `landing_reach()` reads `skills/ship/undone.md` as `sdlc:ship`, so close says `/reload-plugins` and
    `cases` scopes ship's evals; a test pins it.
13. The `ship` eval case on the plain `built` fixture gets a grader failing on any `Read` of a file
    under `skills/ship/` but `SKILL.md`; `ship` and `ship-open-finding` pass a `run-cases` run of
    ship's scope.
14. `AGENTS.md`'s skills invariant says a skill's side files are part of it for its rules and its one
    WAIT; `./check.sh` passes.

## Design

**The files.** Each branch file opens with a `# ` title naming the branch and a sentence saying
when `preflight` names it, then a `## Step N` section for each step it adds to, holding today's text
moved verbatim (only "Step 3"/"Step 4" cross-references adjusted). In `SKILL.md`, each cut leaves a
line like "**Undone items:** in `undone.md`, when `preflight` names it." This keeps the step order
legible and lets a person following the skill by hand see what was cut.

**The trigger.** `cmd_preflight()` builds `branches` from the parts it already holds plus
`(path / "decision.md").exists()`, through `ship_branches(parts, path)`, which returns
`[f for f, cond in SHIP_BRANCHES.items() if cond(parts, path)]`: no judgment, fixed order, so the
reads are too.

**Reading them.** Step 0 reads every named file before Step 1, so a branch with text in Step 1
(`cases.md`) or Step 3 (`fresh.md`) is in context when that step comes. Steps 4 and 6 then take
each branch's section in place. Rules the script enforces stay enforced whether or not the file was
read: a deep diff without the `Fresh review:` note line, or a cases scope without `Skill evals:`, is
refused; `ship` refuses an unticked undone item; the question names every `closes:` issue, every
sensitive path and every skip.

**Tests.** A helper `_skill_files(skill)` gives `SKILL.md` plus its folder's other `*.md`; the rule
tests run over their joined text, frontmatter read from `SKILL.md` only.

**Size.** About 82 lines leave `SKILL.md` and about 10 pointer lines come in: about 470 lines, a
plain run reading about 15% less, with about 100 lines across the files read only when they apply.

## Contracts touched

- **A skill's WAIT step** (always Tier 2): what it approves and when are unchanged. The heading, the
  question, its flags and what each answer does stay in `SKILL.md`. A branch file only adds what
  Step 4 shows before the WAIT, when it applies, as today's branch text does.
- **Narrow `allowed-tools`**: rules stay in `SKILL.md`'s frontmatter. R8 makes the tests read side
  files' commands, so a command can't go unruled, or a rule stale, by moving. `accept` and
  `run-cases` still have no rule.
- **Every script call through `uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/…`**: R8 covers side
  files.
- **Ship's lookups through `preflight`**: `branches` is a new part, not a new command; an additive,
  read-only output.
- **Mechanism vs. judgment**: which branch applies is the script's (`SHIP_BRANCHES`); the skill reads
  what it is told.
- **`sdlc` loads nothing from `plugins/`**: untouched; the files are in `sdlc`'s own `skills/ship/`.

## Alternatives rejected

- **The skill reads the parts and decides** ("read `undone.md` if `undone.items` is non-empty"): six
  conditions in prose for the model to evaluate, against "risk stays the script's call", and a
  misread condition silently skips a rule.
- **One file per step instead of per branch**: every run reaches every step, so nothing is saved.
- **A `branches/` subfolder**: flat files in the skill's folder are how Claude Code lays out a skill's
  supporting files, and the tests' glob stays simple.
- **Also moving Pre-existing bugs, nits and `fixes:`**: the bugs' trigger is the review itself, after
  `preflight`, needing a second trigger source; nits apply on any Nit finding; `fixes:` is 4 lines.
- **Relative paths resolved against the skill's base directory**: `${CLAUDE_PLUGIN_ROOT}` is the form
  every script call already uses, and the harness substitutes it.

## Verification

- `./check.sh`: ruff, the tests (the new `test_preflight.py` cases, the side-file rule tests, the
  `landing_reach` pin), and `claude plugin validate --strict`, which shows whether it accepts extra
  `.md` files in a skill folder.
- `wc -l skills/ship/SKILL.md` prints at most 475.
- `sdlc.py preflight 056` from this change's worktree shows `branches: []` for its own diff (no
  undone items, no `closes:`, no sensitive or irreversible path), or `["cases.md"]` if `cases`
  scopes ship.
- `sdlc.py run-cases 056` (paid, under its prompt at ship): `ship`, with the new no-side-file-read
  grader, and `ship-open-finding` pass.
