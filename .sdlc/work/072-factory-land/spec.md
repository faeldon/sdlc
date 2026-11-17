---
id: 072
slug: factory-land
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 072 — Land a batch of ready factory changes with one stop, or none when nothing is risky · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. R1. `factory.py sdlc-path` finds the `sdlc` plugin's `scripts/sdlc.py` of the factory's own
   version: the clone's `scripts/sdlc.py` when the factory is read from a clone
   (`plugins/factory/` inside it), else `<cache>/sdlc/sdlc/<version>/scripts/sdlc.py` beside the
   factory's cached copy. It refuses a missing copy, or one whose `plugin.json` version differs.
   Every landing step runs that script through `uv run --quiet --script`, so `base`, `ship`,
   `close` and `config` keep one implementation. A test pins both lookups and the refusal.
2. R2. `/sdlc-factory:land` takes the changes `factory.py ready` lists (or the ids named, a subset
   of them) as one batch, in its order (dependencies first, then by id), at most `land.batch`
   changes (default 5), each from its own worktree. The person starts it in a session of its own
   in the main checkout.
3. R3. Land has one WAIT, asked once per batch, naming every change in the batch with its decision
   and any risk signal. `factory.py land-check` gives each change's signals, read-only: a
   `[review] sensitive` or `irreversible` path in its diff (`sdlc.py preflight`'s `risk`);
   `impact: major`; an ESCALATE decision; a blocking or still-assumed decision in `decisions.md`;
   a `checks.md`; a non-empty `closes:` (it came from a public issue); a conflict resolved while
   landing; the base branch's `land.auto` off. When every change in the batch has none, the WAIT
   passes itself, without asking. A change with any signal is asked about, and with it the batch.
4. R4. A new `.sdlc/factory.toml` key, `land.auto` (default `true`), read from the base branch, so a
   change can't turn it on for itself.
5. R5. For each change in turn, through sdlc's own commands: `sdlc.py ship <NNN>` (after land sets
   `impact:` from the approver's decision, which proposes it, shown at the gate, and ticks no
   undone item: a change with one is a signal, R3); a commit whose message `factory.py
   land-message <NNN>` composes (the intent's title, its Problem's first sentence, the folder,
   `Refs #N`, and `Sdlc-Landed: auto|person`, with no `Sdlc-Findings`); `sdlc.py base <NNN>`;
   when `main` moved, one `reviewer-behaviour` round on the rebased change, which runs the gate
   and the spec's path; then `sdlc.py close <NNN>`, which merges, archives, removes the folder,
   worktree and branch, and pushes as `git.push` says. A refusal at any step stops that change and
   every change after it, and reports what landed.
6. R6. When `base` refuses a rebase on a conflict, `factory.py resolve <NNN>` starts that rebase
   and leaves it conflicted, listing the files; `factory.py agent <NNN> --task resolve` resumes
   the change's builder session to resolve them; `factory.py resolve <NNN> --continue` stages and
   continues. Then every reviewer at the change's depth reviews the resolution in one round,
   verified as any round is; a `CHANGES` verdict the verifier keeps, or a second conflict, stops
   the change. The builder rebases nothing itself: `factory.py` runs every git step.
7. R7. `findings.md`'s note says `Fresh review: skipped, the factory's rounds stand in` on a deep
   diff, which ship's refusal needs; `Sdlc-Landed` says who passed the gate.
8. R8. `metrics.py` counts an auto-passed gate as `auto=1` on the change's `Sdlc-Stage: ship`
   line, read at close from the commit's `Sdlc-Landed: auto`: never a `gate`, never in `stops`.
   `GATES` gains `sdlc-factory:land: "first_approval"`, and `_supervised()` keeps the land
   dialogs naming the change. A change landed by land owes `intent, run, land` (`REQUIRED`), with
   no separate ship or close gate. `happy()` marks close `auto` when the gate passed itself, which
   retro already ignores. Pinned by tests.
9. R9. `AGENTS.md` and the factory README say: `factory.py` runs its own version's `sdlc.py` for
   landing, and only for landing; a factory skill commits (land) and closes; a gate may pass itself
   on a clear batch; "only the named steps push" still holds, the push being close's own
   `_push()`. `test_only_the_named_steps_push` and the factory's "nothing commits" text change to
   match.
10. R10. `./check.sh` passes, with tests for `sdlc-path`, `land-check`'s signals, `land-message`,
    `resolve` with a fake conflict, a batch where the second change's rebase conflicts, and a
    batch stopped by a refusal.

## Design

`land`, a new factory skill: Step 0 runs `factory.py ready` and `land-check`; Step 1 shows the
batch, or says it passes itself; Step 2 is the WAIT, skipped when clear; Step 3 lands each change
in order through R5's steps; Step 4 reports landed, stopped (and why), and not reached. Every
`sdlc.py` command goes through `factory.py`, so the skill names only its own script.

`factory.py` gains `sdlc-path`, `land-check`, `land-message`, `resolve` and `agent --task resolve`,
and keeps no landing logic of its own.

## Contracts touched

**Policy edits, loud:**

- **"`factory.py` doesn't call `sdlc.py`"** (its docstring, `AGENTS.md`): it now runs its own
  version's `sdlc.py` as a subprocess for landing. It still never imports it, and a version
  mismatch is a refusal.
- **"Nothing commits" in the factory:** land commits, through `sdlc.py ship`'s staging and its own
  composed message only.
- **One WAIT, confirm before writing, never standing:** land's WAIT passes itself on a clear
  batch, a standing approval set by `land.auto` on the base branch and recorded as
  `Sdlc-Landed: auto`. Every risk signal brings it back.
- **Ship's review as the person's check:** the factory's rounds stand in for factory changes
  landed by land; no `Sdlc-Findings` on their commits, which retro reads as unanswered, never
  clean.

**Kept:**

- **Only the named steps push:** the push is close's own `_push()`, behind `git.push`.
- **Close only fast-forwards and never forces:** close is unchanged.
- **Nothing lost (O2):** a resolution is reviewed and verified before it lands; a stopped change
  keeps its worktree and branch.
- **`accept` under a prompt:** a change with `checks.md` is a signal, so it is asked about, and
  land doesn't run `accept`; such a change is shipped by hand.
- **Agents that judge have no Write:** unchanged; the builder edits the resolution and runs no git.
- **`disable-model-invocation`:** untouched; land invokes no skill.

## Alternatives rejected

- **`/sdlc:land` in core.** The person chose the factory, with sdlc's logic reused, not copied.
- **Copying ship and close into `factory.py`.** Duplicates the riskiest code.
- **Ship's review per change in the batch.** The person chose the factory's rounds.
- **Landing inside the supervisor.** It would keep it busy; the person chose a session of its own.
- **Off by default until the real run.** The person chose on from the start.
- **Running `accept` inside a batch.** It needs a prompt by policy; a change with checks is asked
  about, and shipped by hand.

## Verification

- `uv run --group dev pytest tests/test_factory.py tests/test_metrics.py tests/test_skills.py -q`,
  then `./check.sh`.
- Manual (paid): two ready scratch factory changes touching one file; `/sdlc-factory:land`. Expect
  no question when both are clear, the second resolved by its builder and reviewed, both closed
  and pushed, `Sdlc-Landed: auto` on each and `auto=1` on each `Close`.
