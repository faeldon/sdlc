# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

- 2026-11-18-19 (`/sdlc:close` on a shipped card) was already in `next_action()` from 133's
  round 1; this change pins it again in `test_a_stopped_landing_is_in_needs_you` and leaves the
  code as it was.
- `/sdlc-factory:decide` refuses a run still building (`cmd_ask`), so the build-stage decision
  line names the session running `/sdlc-factory:build NNN` rather than `decide`, as the intent
  asked: a board pointing at a refusal would mislead. Raised as a default in the build report.
- [x] A shipped change whose landing rebase is stopped shows the hand-run `sdlc.py resolve` → seed: 2026-11-18-49
  line as its next step while the factory's builder is resolving the conflict (`next_action()`
  puts `rebasing` first): a landing-aware line ("its builder is resolving a conflict: wait for
  it") would be truer. Left for a change of its own, since `PRECEDENCE` and `BOTH` pin the order.
- [x] `factory.py accept` run after a rebase (inside a landing round) records no step: the track → seed: 2026-11-18-50
  stays at `gate`, which it runs beside. A `checks` position after the gate would need the record
  to say where it sits.
