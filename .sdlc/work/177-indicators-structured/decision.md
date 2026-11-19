DECISION: ESCALATE

**Why.** The last round passed for all three reviewers, the gate is green (3184 passed, `./check.sh` exit 0), and every requirement from R1 to R12 has a test the test reviewer checked can fail. The one important finding (F1, a very large integer crashing `host_rows`) is fixed and covered by a test. I'm escalating only because the change touches published interfaces. The person needs to confirm these before the change reaches `main`, even though the approved spec names them:
- the indicator row shape that hosts will write to;
- a new heading the script reads from a host's `retro.md` override;
- the end of the "the report runs no host command" rule.

**Open items**
- None. F1 (code) is fixed. F2 (code) was set `minor` and is carried in `notes.md`. F3 (test, no test for the OSError path) is recorded as a nit.

**Decisions to confirm**
- None. The change has no `decisions.md`, and the prompt names no open default or blocking line.

**Other reasons to escalate**
- ESCALATED: look: `retro_report()` and `retro-commit` now run the host's `retro.indicators` commands, and `test_retro.py`'s pin is split to allow it. Until now the report ran no host command (see the spec's *Contracts touched*). Confirm that the spec approval covered this. R7's test still checks that `retro.evidence` and `retro.test_times` never run.
- ESCALATED: look: there are now two published contracts:
  - The JSON Lines indicator row shape (R1), documented in `docs/REFERENCE.md` *Retrospectives*.
  - `TEMPLATE_READS["retro.md"]` gains `Indicators` / `{{indicators}}`. As a result, `drift` reports every host override of `templates/retro.md` as `breaking` until the host adds the section. Confirm the wording in REFERENCE.md and that `minor` is the right release impact.

**For the person at ship**, look first at:
1. `scripts/retro.py`: `retro_report()` and `_indicator_rows()`. Check that only `retro.indicators` runs, that `last` is read from the newest `Retrospective` commit's report, and that raw output and stderr never reach the report.
2. `scripts/indicators.py`: `host_rows()`, `report_rows()` and `cell()`, the round trip between writing the table and reading it back.
3. `docs/REFERENCE.md` *Retrospectives* and *After an update*, where the new contract is described to hosts.

- IMPACT: minor — hosts can now have indicator commands print JSON rows and get a table with a trend in the retrospective report. Plain-text output still passes through unchanged. A host with its own `retro.md` override gets a `drift` `breaking` notice and adds `## Indicators` to see the table; nothing they have stops working.

**Undone items**
- UNDONE: A `unit` that is literally `—`, or a `name` or `unit` with leading or trailing spaces, is accepted by `host_rows()` but reads back from the report as a different key (`""`, or stripped), so it gets no `last`. R1 doesn't forbid either; rejecting them would be a one-line rule in `host_rows()` if it ever matters. → seed: Reject indicator names and units that don't read back from the report
- UNDONE: `sdlc.py retro` from a change's worktree runs the main checkout's `.sdlc/function-heat.py` (`main_root()`), so the spec's `retro` verification line shows rows only once this lands. → dropped: it resolves itself when the change lands. It is a note about verifying from a worktree, not work left to do.

**How to recover**
- RECOVER: templates/retro.md: `git revert` of the change's commit removes the `## Indicators` section, its `TEMPLATE_READS` entries and the re-recorded `setup.json` hash together. Reports that `Retrospective` commits wrote in the meantime keep their table as history, which nothing reads after the revert. If a host has already added `## Indicators` to its override because `drift` asked, fix forward: a follow-up change makes the script ignore that section, so the host's copy stays harmless, and runs `sdlc.py record`.
