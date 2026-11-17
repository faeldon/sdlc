DECISION: ESCALATE

## Why

The rounds ran out with one finding still open. `_up()` (`factory.py:4250-4251`) still counts a port as "lost" when the server answered and then exited. It never checks whether the port is actually held, so a server that crashes after coming up gets three starts and a false `retries` record. The run can't be marked ready while rounds ran out, and the build also relies on two defaults (D1, D2) that the person hasn't confirmed. Apart from this, the rest of the change is done and reviewed. The `_resolve()` wording, the spec skill's `fresh`, `fixture` in the build skill, and the docs all passed both reviews. The round-2 gate passed (`./check.sh`: 2195 passed, 9 skipped).

## Open items

- code (round 2, kept by the verifier): `factory.py:4250-4251`. When the port answered and `proc.poll()` then shows the server exited, `_up()` returns `True` without the `_binds()` check. It should return `not _binds(host, port)`, with a direct `_up()` test using a stub process. The reviewer cited line 4246, but the verifier placed the defect at 4249-4251, and the code confirms that.

## Decisions to confirm

- D1: retry the UI server on a new port, instead of having `[ui] serve` report the port it bound (`{port}` = 0). The build assumed retry, which needs nothing from the host's serve command.
- D2: the spec skill shows `behind` and what `fresh` did next to the draft, not inside the approval question. The build assumed next to the draft, as the build skill does, so the question's wording is unchanged.

## Reconsider the approach

What came back each round was always the same thing: deciding whether a failed serve means the port was **lost** or the server **failed on its own**.

- **Round 1:** every exit before answering counted as lost. The plan's wording ("the server exits before answering") was looser than the intent's "fails to bind", and the builder followed the plan as written.
- **Round 2:** that path got the `_binds()` check, but the path just after the loop ("answered, then exited") was missed and still hard-codes `True`.

Each round fixed one place where "lost" is decided and left another. Both reviewers also noted that the retry design can't fully close the race: there is a window between the "already answers" check and the serve's own bind, and the bind check runs only after the exit. That is inherent to retrying, as the intent's open question (now D1) anticipated.

A third round of the same work isn't what's needed. Two choices for the person:

- **Keep the retry approach (D1 as built):** the remaining fix is one line plus one test. It should be made by putting the "lost or own failure" decision in one place, a single helper that every exit path in `_up()` calls, rather than patching each branch. Then no further branch can drift. The plan's description of the retry should say "only a port that won't bind is lost" for every case.
- **Change D1 to "report":** the classification goes away entirely. The cost is a new optional placeholder and cooperation from each host's serve command, which the intent's constraints allow.

The rest of the change (three of the four gaps) doesn't depend on this choice. Another option is to land it now and carry the port fix forward as a seed (below).

## For the person at ship

1. Look first at `_up()` and `_serve()` in `plugins/factory/scripts/factory.py` (around lines 4225-4310): the post-loop `return ..., True` at 4251, and the `retries` and `problem` bookkeeping in `_serve()`.
2. Then check that `plugins/factory/skills/spec/SKILL.md` runs `fresh`:
   - it must be the exact call and `allowed-tools` rule the build skill uses;
   - it must come after `start`'s refusals and before the spec-writer;
   - it must stop on a refusal.

   This adds a new place for one of the named writes before a WAIT, and `AGENTS.md`'s *Writes before a WAIT* was changed to say so.
3. Neither reviewer ran the new port tests on Windows. They use real sockets and aren't marked `portable`, so CI's Windows job won't run them.

- IMPACT: patch — factory runs behave better: the spec skill drafts on an up-to-date branch, a UI server whose port is taken gets a new one, and landing problems name `land-<n>`. Nothing a host writes or does changes.

## Disposition of undone items

- UNDONE: code: plugins/factory/scripts/factory.py:4246: when the server answers and then `proc.poll()` shows it has exited, `_up()` returns `True` (lost) without probing the port. That breaks the rule this round asked for: only a port that won't bind is lost. A server that answers and then dies on its own, while the port is free, gets three starts and a false "lost" record, the same bug the kept finding named. The fix: in that branch, return `(why, not _binds(host, port))`, so a port that binds reads as the server failing on its own. Add a test that drives `_up()` directly with a stub process whose `poll()` returns 1 after a listener on the port is closed, and asserts `lost` is False. → seed: Decide a lost UI port in one place, after the server answered and exited too

## How to recover

No irreversible paths were named. `plan.md`'s Rollback holds: `git revert` undoes everything, since nothing is written outside `.sdlc/reports/` and no host key is renamed.
