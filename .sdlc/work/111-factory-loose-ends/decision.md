DECISION: ESCALATE

## Why

All four gaps are built and tested. Round 4 is `VERDICT: PASS` and its gate passed (`./check.sh`: 2204 passed, 9 skipped). The bug about how a lost port is judged, which kept coming back in earlier rounds, is now decided in one helper (`_lost()`), and tests cover it, including a test that uses a real TIME_WAIT connection. Even so, the build rests on two defaults the person hasn't confirmed (D1, D2), and the rules say that alone means escalate. The change also adds a second place where `fresh`, one of `AGENTS.md`'s named writes before a WAIT, runs. That deserves a look from the person.

## Open items

- None. Round 4 passed with no CHANGE, and the code reviewer's last finding (TIME_WAIT read as held, from round 3) is fixed and covered by a test.

## Decisions to confirm

- D1: the UI review's server retries on a new port, up to 3 tries (`SERVE_TRIES`). It does not have `[ui] serve` report the port it bound (`{port}` = 0). Retry needs nothing from a host, but it can't fully close the race: a process can still take the port between the "already answers" check and the serve's own bind (notes.md).
- D2: the spec skill shows `behind` and what `fresh` did next to the draft, not inside the approval question. The question's wording stays as it was.

## For the person at ship

1. Look first at `_binds()`, `_lost()`, `_up()` and `_serve()` in `plugins/factory/scripts/factory.py`, around lines 4220–4310:
   - `SO_REUSEADDR` is set on POSIX only. The Windows branch rests on the docstring's reasoning: the port tests use real sockets and aren't marked `portable`, so CI's Windows job never runs them.
   - Check that every way a server can end goes through `_lost()`.
   - Check that a timeout, or a serve that fails on its own, is not retried.
2. Then look at `plugins/factory/skills/spec/SKILL.md`, Step 0 (lines 12, 47–58):
   - It must be the same `fresh` call and `allowed-tools` rule the build skill uses.
   - It must run after `start` refuses nothing and before the spec-writer.
   - It must stop on a refusal.
   - `AGENTS.md`'s *Writes before a WAIT* and *The factory* must say the same.
3. A known quirk, noted and not raised as a finding: when a `[ui] serve` shell exits while a child it spawned still holds the port, the retry is recorded as "lost to another process". `_binds()` also always opens an IPv4 socket, so an IPv6 `[ui] url` host is judged by the wrong family (a nit from round 3).

- IMPACT: patch — factory runs behave better: the spec skill drafts on an up-to-date branch, a UI server whose port is taken gets a new one, and landing problems name `land-<n>`. Nothing a host writes or does changes.

## Disposition of undone items

`notes.md` has no unticked `- [ ]` items. The only checklist item, the round-2 `_up()` finding, is ticked and done in round 3. Its two other bullets are notes, not undone items.

## How to recover

The prompt names no irreversible paths. `plan.md`'s Rollback holds: `git revert` undoes everything, because nothing is written outside `.sdlc/reports/` and no key a host writes is renamed.
