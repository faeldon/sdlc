Still reviewing: I've read the diff, and I'm confirming that a fix the builder calls "already made" can't let a landing pass itself.

VERDICT: PASS

## Notes

**Trust boundaries in the diff.**
1. **The land-fix builder's report.** This is model output. Before this change, an empty fix always stopped. Now the train goes on when the report starts with `FIX: ALREADY MADE` and has an `## Evidence` section that `read_evidence()` accepts.
2. **The text of `intent.md` and `spec.md`.** This is change-authored text. It decides which register nits a landing retires.

**STRIDE, briefly.**
- **Spoofing and elevation of privilege (boundary 1).** A builder that wrongly or falsely says `FIX: ALREADY MADE` can't get the change landed unreviewed:
  - `land-<n>.ask.md` is never removed. `landing.py:568` still adds `LANDING_FIXED` as a signal, and `landing.py:1253` still stops a `by=auto` close for the person.
  - The train still runs the gate and the landing review afterwards (`_train_fix(..., done=True)`, then the gate).
  - So the prompt isn't the only boundary, and a false answer costs at most one landing-review round. The safe answer is still the default: no report, no `FIX:` line, a different answer, or two answers that disagree all keep today's refusal (`_not_already_made()` uses `opening()` with the wider `FIX_RE`, as D1 chose).
- **Tampering (boundary 2).** The change narrows what can be retired. Before, any id anywhere in Approach or Requirements was retired; now only ids on a `Nits taken in:` line are. Ids are still matched whole against open register entries. Retirement still happens only inside the `Close` commit, from `entries.md`, and nothing is inferred from the diff. That meets the intent's constraint and lowers the risk of wrongly retiring entries.
- **Denial of service.** `TAKEN_RE` and `FIX_RE` run on one line at a time, with only bounded lazy matching. No ReDoS risk worth worrying about on files this size.
- **Information disclosure and repudiation.** Nothing new is logged or sent anywhere. The new `already_made` field in the JSON output records what happened.

**Other checks.** No new dependency, no shell, no `eval`, no path built from input. `_dirty()` counts untracked files, so an "already made" claim with a stray new file outside the folder goes down the amend path, not the empty path. The change adds no destructive operation: the empty path amends nothing.

**Gate.** `build/round-1.gate.md`: attempt 1 failed on a network error ("Request failed after 3 retries") in `test_adoption.py`, unrelated to this change; attempt 2 passed.

- NIT: plugins/factory/scripts/factory.py:4699: `taken_lines()` counts every indented line after a `Nits taken in:` line as part of it, so an indented sub-bullet that names an id to say it's left out would retire that nit. Only the change's own author can write this, and the intent asked for an explicit marker, so the risk is low. Stopping continuation at a line that starts a new `-` bullet would tighten it {robustness S low}

**Checked, nothing to raise.**
- The diff of `factory.py`, `landing.py` and `land-fix.md`, read against intent R1–R6.
- How `_dirty()` and the signals work: `LANDING_FIXED` at `landing.py:568` and the close stop at `landing.py:1253`.
- `decisions.md` D1, which I agree with.
- I ran nothing beyond read-only `git diff`/`grep`/`sed`.
