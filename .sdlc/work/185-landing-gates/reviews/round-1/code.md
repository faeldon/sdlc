Status: I've read the whole diff and its design, and I'm now writing the review.

VERDICT: CHANGES

- CHANGE: [correctness] plugins/factory/scripts/factory.py:4431: `judged = landing.checks_sha(folder)[:16]` raises `TypeError` when the change's `checks.md` was removed after `--begin`. `checks_clearance()` then names step `checks` (`record is None or sha is None`), so `_land_task` doesn't refuse and `cmd_agent` crashes on `None[:16]`. The loop wouldn't reach this, because `land_verdict` counts a missing file as PASS. A hand-run `agent --task land-checks` would reach it, and it should be a refusal, not a traceback. Fix: make `checks_clearance()` return `step: "accept"` (nothing to judge, not clear) when `sha is None`. Or refuse in `_land_task` when `checks_sha(folder)` is None. Add a case to `test_land_checks_refuses_outside_a_changed_train_change`.

## Notes
- NIT: AGENTS.md:263: the edited factory paragraph has two lines over the file's ~100-column wrap (`change calls for it (build_due()). Landing, in …`, and `approver and the read-only list together, …`). Re-wrap them. {docs S low}
- NIT: plugins/factory/skills/land/SKILL.md:~266: the stops sentence has one very long line (`commit whose before names …`). Re-wrap it. {docs S low}
- NIT: plugins/factory/scripts/landing.py:1900: `_train_begin` calls `_preflight` once per change at begin, as the spec says. Where preflight can't be read, it records `checks: []` with a hash. This is safe, since every check then counts as changed, but a one-line comment saying so would help. {docs S low}
- Decisions: I agree with the builder's defaults on D1, D2 and D3. I raise nothing new.
- Done well:
  - `read_only_command()` is a small scanner that refuses by default.
  - It rejects a glued short-option value, a `--output` and a symlink out of the checkout.
  - The clearance is recomputed just before `accept` runs (R9).
  - A HARMLESS record never overrides the allow-list (R8).
  - `_run_check()` stays the single place a host command runs.
  - The state keys default to "nothing approved", so an old train state stops as before.
  - The spec's named tests all exist.
- Ran and read: the gate record `build/round-1.gate.md` (PASS, `./check.sh`, tree unchanged). I confirmed each spec test name exists with grep. I ran no tests myself.
