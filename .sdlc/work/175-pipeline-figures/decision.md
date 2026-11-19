DECISION: READY

**Why.** All four reviewers in round 1 (code, security, test, behaviour) gave `VERDICT: PASS`. The gate record shows `./check.sh` green: 3253 passed, 29 skipped, and both plugin validations passed. The test reviewer matched every requirement R1–R15 to a test that fails without it, or to the comment and doc work the spec says needs no test. The plan's *As built* section explains each place the build left the spec, and none of them suggests the spec was wrong:
- R13's timing test runs in a child process, not a thread, because Python's regex engine holds the GIL while it matches.
- `unreviewed` gained coverage reporting.
- `bisections` is reported as `{"total": n}`.

**Open items**
- None. The only finding is code's F1 (`[nit]`, `bisections` and `accept_stops` have no `per_change`). It is optional, the spec doesn't ask for it, and it is already filed as `recorded` in `findings.md`.

**Decisions to confirm**
- No blocking decision is open. R1 (the person's revise) is ticked.
- SETTLED: D1: the intent's Constraints already answer it ("A figure a record doesn't hold for an older change is missing, counted in the trust band, never zero"), and so does the spec's R1/*Contracts touched* rule "missing, never zero". The security reviewer agreed in round 1, since counting such a landing as `none` would claim a review no record shows. The behaviour run on this repo confirms it: `unreviewed not recorded: 24`, with `n: 0`.

**For the person at ship**
- **Look first at** `scripts/factory_records.py: pipeline_counts()` and `scripts/retro.py: _pipeline()`. These hold the new reads and the "missing, not zero" handling. On this repo, `wait.n`, `depth` and `unreviewed` all start at `n: 0`, as the spec expects.
- **Record formats you already approved:** the `Waited:` line in both gate writers (`factory.py cmd_gate()` and `sdlc.py cmd_gate()`), and the `DEPTH:` line in `step_text()`/`read_step()`. They are named in spec R3/R6 and in *Design* (*Records first*), and the hand gate's shape pin masks `Waited:` (`tests/test_hand_gate.py`).
- **Moved and shared names you already approved:** `LAND_TRAIN` moved from `landing.py` into `factory.py`, and `WAITED_RE`, `DEPTH_RE`, `TRAIN_GATE_RE` and `LAND_ACCEPT` were added. `sdlc.conflicts_resolved()` now reads `conflicts.md` through `factory_records.resolved_files()`. This is approved in spec R10 and *Contracts touched* (core reads run records only through `factory_records.py`, pinned copies).
- **New `pipeline` key in `retro`'s JSON:** approved in spec R1/R15 and documented in `docs/REFERENCE.md` *Retrospectives*. Per-change figures appear only with `--metrics` (R11).
- **Gate regex:** `_none_reason()`'s new regex `(\s+[^\s=]+=\S*)+$` is spec R13. It behaves differently from the old one only on a token that starts with `=`, and close never writes one.

- IMPACT: minor — a host's retrospective JSON gains a `pipeline` key (gate, train, depth and unreviewed-landing figures), and factory gate and step records gain `Waited:` and `DEPTH:` lines. Readers match by line, so older readers and records are unaffected.

**Undone items:** none. The change folder has no `notes.md`, and the builder reports nothing left.

**How to recover:** the prompt names no irreversible paths. The plan's Rollback is a `git revert`. It leaves the `Waited:` and `DEPTH:` lines in records already written, which every reader skips over.
