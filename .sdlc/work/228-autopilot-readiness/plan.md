---
id: 228
slug: autopilot-readiness
kind: plan
created: 2026-11-22
updated: 2026-11-22
---

# 228 — The autopilot loop is tested end to end before anyone runs it unattended · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`: a new `unfenced_lines(text)` beside `split_draft()`,
  sharing `FENCE_MARK_RE`, which `unbuilt_defaults()` reads a builder report through (R8);
  `cmd_agent()` moves `record_closes()` ahead of the sessions append and `_record_land()` (R6);
  docstrings of `cmd_answer()`, `cmd_decisions()` (R5) and `recorded_closes()` (R7). No other
  code changes; `autopilot.py` and `landing.py` are untouched.
- `plugins/factory/README.md`: the `- BUILT: D<n>` sentence (line 606) says "outside a code fence".
- `tests/train_driver.py`: `FAKE_CLAUDE` logs a `markers` field (R2) and takes a `once` entry
  (`then_reply` after the first call, so a resumed builder raises its line once).
- `tests/test_factory_decisions.py`: four fenced cases in the `- BUILT:` parametrize (R8).
- `tests/test_autopilot.py`: R3's `take_markers()` test, R4's refused half through `_claude()`,
  R5's ledger-writer overlap test, R7's read-count test, R8's hold test, and the new
  `# ---- the whole loop, as it runs` section with R1/R2's test and the marker-names pin.
- `tests/test_land.py`: R6's refused-agent test, beside the land-fix test whose helpers
  (`_gated()`, `_ready()`, `_asked()`) it reuses, rather than in `test_autopilot.py`.

Reused, not re-derived: `FENCE_MARK_RE` and `split_draft()`'s close rule; `train_driver.fake_claude()`;
`factory_helpers._change()`, `_build_report()`, `_ledger()`, `needs_uv`; `ap.autopilot_lock()`;
the in-process `Steps` stand-in and `_repo()`/`_begin()`/`_loop()` for R5.

## Work order

1. **Fenced `- BUILT:` (R8).** Red: the four parametrized cases and the hold test against today's
   `BUILT_RE` scan. Green: `unfenced_lines()` and `unbuilt_defaults()` reading through it. README
   sentence.
2. **A refused agent records nothing (R6).** Red: the refused-agent test (land-step.md exists).
   Green: the move in `cmd_agent()`.
3. **One read of the closes (R7).** The count test (green on today's code, it pins the count),
   and the docstring.
4. **The ledger's writers (R5).** Docstrings, and the in-process overlap test through `Steps`.
5. **`take_markers()` (R3).** Its portable test.
6. **The refused half through `_claude()` (R4).** Replace the direct `subprocess.run`.
7. **The whole loop (R1, R2).** `FAKE_CLAUDE`'s `markers` and `once`; the scratch host; the
   real `autopilot --begin` and `--run`; assertions read from history.

Each step ends with its own tests run by name; the gate runs the suite.

## Tests

- R1, R2: `test_autopilot_run_lands_a_seed_through_real_subprocesses`;
  `test_fake_claudes_marker_names_are_the_factorys`.
- R3: `test_take_markers_moves_both_markers_out_of_the_env` (portable, two cases).
- R4: `test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does`, its refused half now
  through `factory._claude()`.
- R5: `test_no_ledger_writer_runs_beside_another_step_of_its_change`.
- R6: `test_an_agent_refused_on_its_closes_leaves_nothing_recorded`.
- R7: `test_an_agent_run_reads_the_closes_once`, which pins **two** reads, not the spec's one:
  `run_state.loop_state()` reads the closes through `intent_closes()` as well as
  `record_closes()`. The docstring says so; no code changed (raised as a default).
- R8: `test_ask_says_ship_once_a_later_builder_report_built_it`'s four new cases;
  `test_a_fenced_built_line_still_holds_autopilot`.
- R9: every existing test, unedited but for R4's half and the fake's log field; the gate.

## Departures from the spec's design, as built

- R2's host check is plain `sh` (`env > <dir>/check-$$.env`), not a Python script: the gate's
  record holds the command, and `sys.executable` under a home directory is a shape
  `forbidden_lines()` refuses, so the approver's step held the change.
- R6's test is in `tests/test_land.py` and runs `land-fix`, a resumed task, so it shows the
  landing step unwritten and the sessions file unchanged; the reorder also moves the fresh
  session's append past the refusal.
- R5's test uses two seeds (S1, S3) with three review roles each; it was seen to fail when the
  loop's `read` step ran `decisions` and `verdicts` together.

## Rollback

`git revert` covers it all: the change writes nothing outside the repo, no state file, no data
a host holds. The `closes:` row's earlier append (R6) writes the same row as before.
