DECISION: READY

**Why:** `EXIT_RE` now reads a space-separated note after the code. `exit: nonzero`, `exit: not run` and `exit: 2x` still fail, as the intent's constraint requires. Both reviewers passed the round, and the new parametrised test (6 cases), the one check in `checks.md` and the gate all passed. The only leftover is a note in `notes.md` that is outside this change's scope.

**Open items:**
- NIT (code reviewer): `plugins/factory/agents/resolver.md:58` has the same `exit: <n>` wording and no hook-refusal sentence, so it can meet the same stop. It is minor and not in `notes.md`.

**Decisions to confirm:**
- SETTLED: D1: `plan.md` puts the hook-refused command under `## Notes` because the behaviour reviewer's prompt has no *Not run* section and Notes already holds "anything you couldn't run and why". The behaviour reviewer's third grep check confirms the sentence is in the prompt, and the script doesn't read that heading.
- SETTLED: D2: the intent's Constraints say an `exit:` with no number still fails, so `exit: blocked` is not read. `EXIT_RE` and the parametrised test, which still rejects `exit: nonzero` and `exit: not run`, bear this out.

**For the person at ship:**
- Look first at `EXIT_RE` in `plugins/factory/scripts/factory.py` (line 322) and the one new sentence in each of `reviewer-behaviour.md` and `builder.md`.
- The regex is deliberately narrower than the intent's `\d+\b.*`. It needs whitespace after the code, so `exit: 2(note)` is still flagged. The plan explains this, and the code reviewer and the behaviour reviewer both accepted it.
- No published interface is touched. The mend remains once per role.

- IMPACT: patch — a behaviour check or build report that writes a note after its exit code now passes where it used to stop; nothing anyone must do differently.

**Undone items:**
- UNDONE: `scripts/sdlc.py`'s `EVIDENCE_EXIT_RE` (`^exit:\s*(-?\d+)\s*$`), which reads ship's own behaviour check in `findings.md`, is as strict as `EXIT_RE` was: an `exit: 2 (note)` there is not read as evidence. Out of this change's scope (the factory's reading); widen it the same way in a change of its own if ship's check meets it. → seed: Widen `EVIDENCE_EXIT_RE` in sdlc.py to accept a note after the exit code
