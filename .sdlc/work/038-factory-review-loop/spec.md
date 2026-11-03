---
id: 038
slug: factory-review-loop
kind: spec
created: 2026-11-04
updated: 2026-11-04
---

# 038 — The factory's review rounds verify, converge and scale to risk · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1. A verify step.** When a complete round has any `VERDICT: CHANGES`, `factory.py verdicts`
   says `next: verify` before `rework`; the skill spawns `sdlc-factory:verifier` with the round's
   `CHANGE:` lines and writes its reply to `reviews/round-<N>/verified.md`, each line `- KEPT:
   <role>: <change>` or `- DROPPED: <role>: <change> — <why>`. `verdicts` stops when a `CHANGE:` of
   the round isn't listed exactly once, or a listed line names no `CHANGE:`. Tests cover the step,
   a missing and an extra line.
2. **R2. Only kept changes are reworked.** `rework` follows only when `verified.md` keeps at least
   one; a round whose changes are all dropped goes to `approve` as a pass would. The builder's
   message names `verified.md`'s `KEPT` lines alone; `carry` carries only the last round's kept,
   still-open lines.
3. **R3. The verifier agent.** `plugins/factory/agents/verifier.md`: tools `Read, Grep, Glob,
   Bash` (it may run tests, no `Write` or `Edit`), a description that says when not to use it, told
   to run nothing that writes. A test pins its tools and that it never edits.
4. **R4. Round snapshots.** A new `factory.py snapshot <NNN> --round <N>` writes
   `build/round-<N>.files`: one `<sha256>  <path>` line per path changed against the base branch,
   untracked included, writing only in the change's folder. `verdicts` gives `reworked`: the paths
   whose hash changed since the previous round's snapshot (every changed path in round 1).
5. **R5. Later rounds review the rework.** From round 2, a reviewer that reviewed an earlier round
   is prompted with `reworked`, the round's kept `CHANGE:` lines and `settled` (every earlier
   `DROPPED` line, and every `KEPT` line the next round no longer raises); a reviewer new to the
   run reviews the whole change. The reviewer agents are told never to raise a settled point again,
   and `verdicts` lists a `CHANGE:` whose text repeats a settled one as `repeats` for the verifier.
6. **R6. Pre-existing is never a `CHANGE:`.** Reviewers return code the change didn't touch as
   `- PREEXISTING: <path:line>: <what>` lines. `verdicts` lists a `CHANGE:` whose path isn't in the
   change's diff as `untouched`, and the verifier is told to drop it as pre-existing. `carry` writes
   each `PREEXISTING` line to `notes.md` as `- [ ] pre-existing: …`, so `/sdlc:ship` must give it a
   disposition.
7. **R7. At the cap, step back.** When `verdicts` reports `exhausted`, the approver is prompted that
   the rounds ran out with changes open, and its `decision.md` must be `DECISION: ESCALATE` with a
   `## Reconsider the approach` section; `verdicts` stops on an exhausted run's decision lacking
   either.
8. **R8. Risk from the diff.** `factory.py` reads the base branch (`.sdlc/config.toml`'s
   `[git] base`, else `main` when it exists) and `[review] sensitive` from that branch's config
   (`git show <base>:.sdlc/config.toml`), so a change can't lighten its own review, and matches the
   diff's paths with a copy of `risk_paths()` a test pins to `sdlc.py`'s. `verdicts` gives `depth`
   (`light` or `full`), `sensitive` (the matched paths) and `why`.
9. **R9. The depth rule.** With no `sensitive` list, every run is `full`, exactly as today. With
   one, a run whose diff touches none is `light`; once a round has run `full` or the diff touches a
   sensitive path, it stays `full` (never lightens). `light` uses `[light]`'s `reviewers` and
   `rounds` (default `["code"]`, `2`); `full` the existing `reviewers` and `rounds`. A deepened
   run's `missing` names the full reviewers who haven't reviewed.
10. **R10. Config.** `factory.toml` accepts `[light]` with `reviewers` and `rounds`, validated like
    the top level (a bad key a warning, never silently ignored); `config` and `start` print it.
11. **R11. The question states the worst case.** `max_runs` counts the verifier
    (`2 + rounds × (reviewers + 2)`, at the full depth). The WAIT reads: `Run the factory on
    NNN-<slug>: the builder plans and builds it, <full reviewers> review it in up to <rounds> rounds
    (or <light reviewers> in up to <light rounds> when the diff touches no sensitive path), a
    verifier checks each round's changes, the approver decides, at most <max_runs> agent runs, all
    left uncommitted at stage: test? (yes / change the reviewers or rounds / no)`, the parenthesis
    left out with no `sensitive` list. A test pins both forms.
12. **R12. Measured.** `sdlc.py`'s `_factory_files()` counts each role's `dropped` from every
    `verified.md`; `Sdlc-Review` gains `dropped=`; older trailers read without it. A test pins the
    new regex copies against `factory.py`'s.
13. **R13. Ship reads them.** `/sdlc:ship` Step 0 names `reviews/round-<N>/verified.md` among the
    factory's evidence; a dropped `CHANGE:` ship's own passes confirm is a finding like any.
14. **R14. Docs.** `plugins/factory/README.md` (the loop, depth, `[light]`, the verifier),
    `docs/REFERENCE.md` (`factory.toml`'s `[light]`, `Sdlc-Review`'s `dropped`), `AGENTS.md`'s
    factory paragraph.
15. **R15. Seeds.** At ship, 2026-11-03-9 leaves through `idea:`; -10 and -11 deleted by hand, and
    -12's `After: 2026-11-03-11` line removed.

## Design

- **The loop's states.** `verdicts` gains `verify`: `build` → `review` → (`verify` → `rework` |
  `approve`) → … → `approve` → `done`, plus `depth`, `sensitive`, `why`, `reworked`, `settled`,
  `repeats`, `untouched`. `read_rounds()` reads `verified.md` beside the reviews, and each review's
  `PREEXISTING` lines; the reviewers a round expects come from the depth, not `cfg["reviewers"]`.
- **Depth without memory.** `verdicts` writes nothing, so `full` when the current diff touches a
  sensitive path or any recorded round holds a review from a reviewer outside `[light]`'s list;
  else `light`. The round limit follows the depth, so a run that deepens at round 2 gets the full
  rounds.
- **Snapshots.** `snapshot` hashes each changed file (`hashlib`): `git diff --name-only
  <merge-base>` plus `git ls-files --others --exclude-standard`, leaving out the change's own
  folder. The skill runs it after writing each builder report.
- **Untouched.** A `CHANGE:` starts `path:line:`; its path (before the first `:`) against the
  changed paths.
- **Agents.** The reviewers get a later-rounds section (`reworked`, `settled`, never raise again)
  and the `PREEXISTING` line; the approver the exhausted rule; a new verifier; the builder's rework
  reads `verified.md`.
- **Skill.** Step 0 shows the depth rule; Step 2's question per R11; Step 3 adds `snapshot` after
  every report, `verify` with the verifier, and the rework message naming `KEPT` lines. One new
  `allowed-tools` rule, `factory.py snapshot`.

## Contracts touched

- **Agents that judge have no `Write`; only the builder edits:** the verifier has `Bash` to run
  tests, like the reviewers, and is told to write nothing.
- **Nothing commits, nothing under `.git/` or on the shared stash:** snapshots are files in the
  change folder; `verdicts` still stops on a moved `HEAD`.
- **The factory's cached copy has no `sdlc.py`:** `factory.py` reads `[git] base` and `[review]`
  itself and copies the matcher, pinned by a test, as `NOTES_HEAD` and the regexes are today.
- **One WAIT, worded literally; narrow `allowed-tools`:** the question changes and one rule is
  added; the skill tests are updated, never loosened.
- **Metrics trailers extend, never redefine:** `dropped=` is a new key on `Sdlc-Review`.
- **`sdlc` loads nothing from `plugins/`:** unchanged; the verifier lives in
  `plugins/factory/agents/`.
- **Risk read from the base branch (036):** the same rule here.

## Alternatives rejected

- **The builder verifies its own critics:** the anchoring the post warns about.
- **Two verifiers voting:** double the per-round cost before the numbers show one isn't enough.
- **Depth from the spec's named paths, up front:** a build straying outside them is reviewed
  lighter.
- **`git write-tree` or `git stash create` snapshots:** they write objects under `.git/`, and the
  stash route sits beside the shared stack.
- **Lightening a run once its diff stops touching a sensitive path:** a path reverted in round 2 was
  still risky in round 1; a run never lightens.

## Verification

- `./check.sh`, its exit code read directly.
- `uv run --group dev pytest tests/test_factory.py tests/test_metrics.py tests/test_skills.py -q`,
  cases for R1–R2, R4–R12.
- `factory.py config` prints `light`; `factory.py verdicts` in a scratch change shows `depth` move
  from `light` to `full` when a sensitive path appears, and never back.
