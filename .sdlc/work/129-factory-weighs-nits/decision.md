DECISION: ESCALATE

**Why.** The code and test reviewers both gave `VERDICT: PASS` in round 1, and they found code and a test for every requirement from R1 to R13. The gate passed `./check.sh` (2351 passed) and `drift` is clean. But the build rests on two decisions, D1 and D2, that nobody has confirmed: both are still unticked defaults in `decisions.md`. The change also alters published interfaces: the reviewers' `- NIT:` line format, the landing question, the `land` output (it now returns `filed_nits`), and `templates/inbox.md`.

**Open items**
- No change requests are unresolved. The code reviewer raised three nits; `findings.md` records them as F1–F3 with `minor`:
  - F1 (code): `zip(ids, seeds, strict=False)` at `factory.py:4242` no longer checks lengths. The reviewer's fix is `zip(ids[: len(seeds)], seeds, strict=True)`.
  - F2 (code): `land_signals()` re-reads every round only to count the nits past the cap.
  - F3 (code): a nit that the cap or the no-path rule turns `minor` keeps its theme, cost and value.
- The test reviewer also left one NIT, but it isn't in `findings.md`: rerunning `test_a_landing_rerun_files_each_nit_once` calls `_dispose()` directly. It never reruns `cmd_land` after a failed commit.

**Decisions to confirm**
- D1: only a nit that will be filed gets `Theme:`/`Cost:`/`Value:` lines in `findings.md`. `L` and `high` nits get a `Reason:` instead.
- D2: a cheap nit counts as handed to the builder when its round kept a change and the next build isn't the first round of a restart or upgrade. That includes a round built from a blocking decision's answer instead of a rework.

**For the person at ship**
- Look first at `_dispose()` in `plugins/factory/scripts/factory.py`, around line 4242. Check the ids from the one `next-entry` call, the order (seeds, then bugs, then nits), the `strict=False` zip from F1, and the rerun skip in `filed_nit()`.
- Then read `agent_findings()`, where the weights become a disposition. Check that no agent finding can end up `fix` or `open`, and that the cap of 5 and the no-path rule apply last.
- Two departures from the spec are written into `plan.md`: `_dispose()` now returns a tuple, and `land_parts()` takes optional `root`/`cfg`. A third is not: filed nits store `Paths:` without the line number.
- The reviewers in round 1 ran the old prompts, so their nits had no weights. A real weighed nit has never gone through this run end to end. It would be worth doing the by-hand scratch check from the spec's Verification section.

- IMPACT: minor — a factory landing can now file `[nit]` entries in the register on the person's yes, and the reviewers' nits are weighed and handed to a rework. Runs from before this change, whose nits carry no weights, behave as before.

There are no undone items: `notes.md` doesn't exist, and the builder reports nothing was left there.

**How to recover**
- RECOVER: templates/inbox.md: `git revert` restores the template's note for new registers. Fix forward for the rest: a revert can't reach the copies hosts already started from this template, which keep the extra mention of the factory's landing. It is harmless text that each host can edit by hand. A follow-up change would correct the template wording if it turns out wrong. Any `[nit]` entries a landing has already filed in a host's `.sdlc/work/inbox.md` are ordinary entries. Retire each by shipping a fix, or delete its section by hand (as `plan.md`'s Rollback says).
