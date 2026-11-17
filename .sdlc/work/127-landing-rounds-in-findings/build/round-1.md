The landing now writes its own review rounds into `findings.md`, and the full gate passes (2337 passed, 13 skipped). Everything is uncommitted, ready for `/sdlc:ship`.

The intent says Tier 1 and its Approach touches more than a couple of files, so I wrote a short `plan.md`. I've updated it to match what was built.

**Slices built**
1. **The landing writes its rounds at `land --close`.**
   - `read_rounds()` now reads the landing's `reviews/land-<n>/` folders too, with the same parsing as a build round.
   - `agent_findings()` and `finding_section()` handle both kinds. A landing finding's `Class:` reads `<role> review, landing round <n>`, and its `Evidence:` falls back to `reviews/land-<n>/<role>.md`.
   - `cmd_land_close()` calls `write_findings()` over the build rounds plus every landing round that has a review. It does this after its `by=auto` refusals and before the record is recorded and amended in, so the file lands in the change's commit.
   - With no landing review, the file `carry` wrote is left alone.
   - `land_message()` is unchanged, so the landing commit still has no `Sdlc-Findings`.
2. **Rerun.** `write_findings()` already rewrites only the sections an agent raised. A second `land --close` (after the base branch moves) rewrites those and keeps ship's own section as written.
3. **Docs.** `plugins/factory/README.md` and `docs/REFERENCE.md` now say the landing adds its rounds.

**Test added:** `test_a_landing_writes_its_rounds_findings_into_its_commit` in `tests/test_land.py`. One landing round holds a kept change, a dropped change, a new pre-existing line, and a pre-existing line a build round already raised. The base branch moves, so `land --close` runs twice before the change lands. The test proves that:
- each finding appears once, with its landing-round `Class:`: the kept change `fixed`, the dropped one `wrong` with the verifier's reason, the pre-existing one `recorded`;
- the line raised in both a build round and a landing round is counted once;
- the second run changes only the kept change's disposition, and ship's own section stays;
- `sdlc.py`'s parser reads the file with no problems;
- the landed commit has no `Sdlc-Findings`.

I first saw it fail for the expected reason: no landing finding was in the record.

**Changes to `plan.md`:** I didn't add the separate `test_factory.py` unit test the plan named. The landing test already covers the rerun end to end through the base-moved path.

**Left in `notes.md`:** one unticked line. The note at the top of `templates/findings.md` (and its copy `FINDINGS_HEAD`) still names only `carry` as a writer. Changing it affects a file shipped to hosts and needs `sdlc.py record`, so I kept it out of this change.

- DECISION: [default] Which landing step writes it? Options: `land --close`; `land-verdicts` at `pass`. Going ahead with `land --close`: `land-verdicts` only reads, and `land --close` already adds the landing's record to the commit on every run, including after the base moves.
- DECISION: [default] Is a finding a reviewer raised in both a build round and a landing round one or two? Going ahead with one, the first time it was raised: that matches how the build rounds are already de-duplicated by role and text. A fault worded differently is still a separate finding, as the file's note says.
- DECISION: [default] What does the record say for a change the verifier kept in the last landing round, with no later round after it? Going ahead with `recorded`, never `fixed`: no one fixed it. Once a later landing round follows, it reads `fixed`. In the normal flow a kept landing change stops the landing, so `land --close` only meets this when the person closes anyway.

## Evidence

$ uv run --group dev pytest -q tests/test_land.py -k writes_its_rounds   (before the code)
E       Right contains 3 more items, first extra item: ('fixed', 'behaviour review, landing round 1', None)
1 failed, 56 deselected in 12.43s
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -k writes_its_rounds
1 passed, 56 deselected in 7.59s
exit: 0

$ ./check.sh
All checks passed!
2337 passed, 13 skipped in 165.14s (0:02:45)
✔ Validation passed
✔ Validation passed
exit: 0
