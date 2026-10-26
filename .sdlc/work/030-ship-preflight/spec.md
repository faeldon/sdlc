---
id: 030
slug: ship-preflight
kind: spec
created: 2026-10-27
updated: 2026-10-27
---

# 030 — One preflight call for ship's lookups · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1.** `sdlc.py preflight <NNN>` prints one JSON object holding `change`, `tier`, `stage`,
   `folder`, and the parts `undone` (what `undone <NNN>` gives), `nits` (what `nits --change
   <NNN>` gives), `closes` (what `closes <NNN>` gives, its `unavailable` reason included),
   `checks` (what `checks <NNN>` gives) and `context` (what `context` gives from the change's
   checkout). A test asserts each part equals its single command's output on the same fixture
   change.
2. **R2.** Each single command and `preflight` build their part from one shared function per part,
   so they can't drift. `undone`, `nits`, `closes`, `checks` and `context` keep their output and
   exit codes; their existing tests pass unchanged.
3. **R3.** `preflight` writes nothing (a test asserts `git status --porcelain` and the change
   folder are unchanged after it). It exits 1 when any part reports problems (nits' or checks'
   `problems`), printing every part regardless, and exits 1 with a `⚠` line for an id naming no
   change.
4. **R4.** `preflight <NNN> --question [--context] [--nits] [--closing N]… [--split N]…` prints
   Step 5's question as plain text, word for word, with the clause rules in code:
   `, with the context update shown` only with `--context`; `, the nits shown recorded in
   <work.rel>/inbox.md` only with `--nits`; `closing #N and #M when it lands` only with
   `--closing`; `and splitting #K off as a seed` (`seeds` for several) only with `--split`;
   `, then update its issue` only when `archive.target` isn't `none`. A parametrized test pins
   each rule, and one pins the full sentence with every clause in.
5. **R5.** `--question` refuses (exit 1, a `⚠` line, no question) when a `--closing` or
   `--split` number isn't on the change's `closes:` line, when one number is given to both, or
   when a `closes:` number is given to neither: ship asks about every issue, so the question
   never leaves one out. One test per refusal.
6. **R6.** `READ_ONLY`, so `ALLOW_RULES` and setup's proposed rules, gains `preflight` and `nits`.
   `test_readiness` still finds no writer among them. This repo's `.claude/settings.json` gets
   both rules.
7. **R7.** `skills/ship/SKILL.md`: Step 0 runs `base <NNN>` then `preflight <NNN>` in place of
   `undone`, `nits --change`, `closes` and `checks`; Step 1 shows the checks from `preflight`'s
   `checks` (`accept` still named in prose only); Step 3 takes the context pass's list from
   `preflight`'s `context`; Step 5 runs `preflight <NNN> --question …` and asks exactly what it
   prints, and its clause-omission paragraph is gone. `allowed-tools` loses `undone`, `nits`,
   `closes`, `checks` and `context`, and gains `preflight`; the used/covered rule tests pass.
8. **R8.** The skill is shorter: `wc -l skills/ship/SKILL.md` and the count of `sdlc.py` commands
   it runs are both below today's (412 lines; the commands counted in the plan), with the before
   and after in the ship commit.
9. **R9.** `docs/REFERENCE.md` names `preflight` where it describes ship's lookups and the
   read-only commands setup allows. `tests/test_adoption.py` keeps passing with `preflight` run
   by `uv run --script` in its scratch repo, adding that run if it doesn't already exercise
   ship's lookups.

## Design

**One part per function.** `cmd_undone`, `cmd_nits`, `cmd_closes`, `cmd_checks` and
`cmd_context` each build a dict and print it today. Each splits into a
`_<part>_report(root, path, …) -> dict` that builds it and the `cmd_*` that prints it with its
current exit code. `cmd_preflight(root, ident)` resolves the change once (`_one_change()`), calls
each report with that path, and prints:

```json
{"change": "030-ship-preflight", "tier": 2, "stage": "build", "folder": ".sdlc/work/030-ship-preflight",
 "undone": {...}, "nits": {...}, "closes": {...}, "checks": {...}, "context": {...},
 "problems": ["nits: …", "checks: …"]}
```

`problems` gathers each part's problems prefixed with the part, and is what the exit code reads.
`context`'s report runs from `checkout_of(path)` against `git.base`, as ship runs it today from
inside the worktree.

**The question.** `--question` takes a separate path through `_ship_question(change, cfg,
context, nits, closing, split) -> str`, a pure function but for reading `closes:`, building the
sentence from R4's clauses in order and joining numbers as `#12`, `#12 and #15`,
`#12, #15 and #18`. Tests call the function directly, and once through the CLI. Validation (R5)
runs before rendering.

**Not handed off.** `preflight` is read-only, so it stays out of `OWN_SCRIPT_CMDS`, like `undone`
and `checks`. Until this change lands, ship in this repo runs whichever copy the session loaded,
as for every read-only command.

**Factory files unchanged.** Ship still reads `decision.md`, `decisions.md` and the reviews
itself: they are prose evidence, not lookups.

## Contracts touched

- **Narrow `allowed-tools`:** ship's rules shrink to the commands it still runs, each written
  exactly as run; the used/covered tests enforce it.
- **One `WAIT` heading, and the WAIT stays the person's:** the script drafts the question; the
  skill still asks it and commits nothing before the answer. The heading is unchanged.
- **`base` is the one write before the WAIT:** unchanged, still its own call, first.
- **`accept` never gets an allow rule:** `preflight` only lists checks, as `checks` does;
  `test_no_skill_lets_accept_run_unasked` and `test_acceptance`'s `accept not in READ_ONLY` hold.
- **Only publish pushes:** `preflight` runs no git write.
- **Setup's allow rules (`ALLOW_RULES`):** grow by two. A host set up earlier sees `permissions:
  missing` in `readiness`/`status` until `/sdlc:setup` runs, which is the existing nudge;
  `uninstall` removes what `ALLOW_RULES` lists, so it covers the new ones.
- **Mechanism vs. judgment:** the clause rules move into the script; which nits, context edits and
  issues are resolved stay the person's and the skill's, passed in as flags.

## Alternatives rejected

- **`ship --check` as a flag on `ship`.** No allow rule could cover it without also covering
  `ship <NNN>`, which stamps and stages, so it could never be read-only.
- **Folding `base` into `preflight`.** It would make it a write; a rebase hidden in a "check" is
  the surprise the named exception exists to keep visible.
- **Folding `check --strict` in.** It is the gate, with its own pass/fail in Step 1; bundling it
  blurs which failure stops ship.
- **Removing the single commands.** Intent and spec run `nits --touching`, and people run them by
  hand; `preflight` composes them.
- **Facts only, the clause rules left in prose.** Rejected by the person: it leaves untested the
  part the retro flagged.
- **Rendering the question in the first call.** Three clauses depend on Step 4's decisions.

## Verification

- `uv run --group dev pytest -q tests/test_sdlc.py -k "preflight or question"`: R1–R5.
- `uv run --group dev pytest -q tests/test_skills.py tests/test_readiness.py tests/test_acceptance.py tests/test_adoption.py`:
  R6, R7, R9 and the allowed-tools tests.
- `./check.sh` passes.
- From this change's worktree, `uv run --quiet --script scripts/sdlc.py preflight 030` prints
  every part, and `… preflight 030 --question --context` prints the sentence without the nits or
  closing clauses (`closes:` is empty).
- This change's own `/sdlc:ship` runs on the new Step 0, and the ship commit gives the skill's
  line and command counts before and after.
- After it closes, `Sdlc-Stage: ship … permission=` on the next few `Close` commits is the O3
  evidence the retrospective reads, against the commits before.
