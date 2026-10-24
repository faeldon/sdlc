---
id: 007
slug: stop-target
kind: plan
created: 2026-10-24
updated: 2026-10-24
---

# 007 — Reconcile O3's two-stop target with the gates a change passes · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Context

O3 and `metrics.target_stops` (2) promise a stop count below what the process's own gates require
(3 for Tier 1, 5 for Tier 2, in `REQUIRED`, `scripts/metrics.py:98`). So the first
retrospective's stops can't be read. The spec (`work/007-stop-target/spec.md`, R1–R6) measures
each change against its own gates plus `metrics.stop_allowance` (default 1). It retires
`target_stops` through 002's `RETIRED_KEYS` (impact major), adds `allowance=` to `Sdlc-Totals`,
has retro recompute an old commit's target from its own `required=`, and rewrites O3, the process
signal, REFERENCE and M2 of the direction doc. The branch is on `main` at `a9ad7ee`.

## Files to change

- `scripts/sdlc.py`:
  - `CONFIG_KEYS["metrics"]`: `target_stops` goes and `stop_allowance: 1` comes in, with its
    comment; `INT_KEYS` follows;
  - `RETIRED_KEYS["metrics.target_stops"]`;
  - `metrics_summary(changes, allowance)`: `_target()`, `"over"` in the medians, `"target"` as the
    median;
  - `retro()` passes `cfg["metrics"]["stop_allowance"]`.
- `scripts/metrics.py`: `summarize()` and `history_summary()` set
  `target = len(required) + cfg["stop_allowance"]` and `allowance`.
- `.sdlc/PRODUCT.md`: O3's line, exactly as in R5.
- `defaults/SDLC.md`, `.sdlc/SDLC.md`: the "Where a change's time and tokens go" bullet's last
  sentence, identical in both.
- `docs/REFERENCE.md`: the config sample line (line 68), the *Metrics* paragraph (~line 410), and,
  near line 172, `metrics.target_stops` as the named example of a retired key, if the text there
  gives one.
- `.sdlc/DIRECTION.md`: M2's text and `Groups:` line (R6).
- `.sdlc/setup.json`: re-recorded with `sdlc.py record`.
- Tests:
  - `tests/test_metrics.py`: `CFG`, the `history_summary` round-trip at line 330, new target tests;
  - `tests/test_retro.py`: line 731's `target == 2` becomes the recomputed 6, plus a mixed-group
    test;
  - `tests/test_config_resolution.py`: lines 164–170;
  - `tests/test_setup_lifecycle.py`: `test_new_keys_listed` uses `metrics.stop_allowance`
    (default 1), plus a test of a host still setting `target_stops`;
- `work/007-stop-target/checks.md` (new): acceptance checks for the doc edits only a revert could
  undo (O3's wording, M2's `Groups:` line).

## Work order

1. **Config (R1, R2).** Swap the key; add the `RETIRED_KEYS` entry with `now`, `since: "2.0.0"`
   and `do` as in R2. Update `test_config_resolution.py` (default, a kept 0, `-1` warns) and
   `test_new_keys_listed`. Add `test_a_host_still_setting_target_stops_is_told`: config with
   `[metrics]\ntarget_stops = 2`; `load_config` warns `unknown key metrics.target_stops`; `drift`'s
   `breaking` has it with `now == "metrics.stop_allowance"`. `test_retired_keys_point_at_live_keys`
   now runs over the entry.
2. **Close (R3).** In `summarize()`, after `required` is built, set
   `"target": len(required) + cfg["stop_allowance"]` and `"allowance": cfg["stop_allowance"]` in
   `totals`. Do the same in `history_summary()`. Update `CFG` to `{"idle_minutes": 30,
   "stop_allowance": 1}`, and line 330's expected totals to `required: 5, target: 6, allowance: 1`.
   Tests: Tier 1 manual 4; Tier 1 with a plan-mode exit 5; Tier 2 6; allowance 0 gives
   `target == required`; `trailers()` → `parse_trailers()` keeps `allowance` and `target`.
3. **Retro (R4).** `metrics_summary(changes, allowance=CONFIG_KEYS["metrics"]["stop_allowance"])`.
   For each measured change, `t = totals["target"] if "allowance" in totals else
   totals.get("required") + allowance` (None when `required` is missing). `over = stops - t` when
   both are ints. Add `"over"` to the per-group medians and set `"target"` to the median of the
   `t`s. `retro()` passes the configured allowance.
   - Update `test_retro_reads_what_close_measured…`: its old-style trailers (`required=5
     target=2`) read as target 6, and `median.over` is `7 - 6 = 1`.
   - Add `test_old_and_new_trailers_read_against_their_own_targets`: one old commit (`required=5
     target=2`, no allowance) and one new one (`required=3 target=4 allowance=1`) in groups, each
     with the right target and `over`.
4. **Docs (R5, R6).**
   - O3 in `.sdlc/PRODUCT.md`, verbatim from R5.
   - The signal sentence, in both copies: "…stops above the gates are the loop circling." becomes
     "…each change's stops are measured against its gates plus `metrics.stop_allowance`, and
     those above that are the loop circling."
   - REFERENCE: line 68 becomes `stop_allowance = 1   # the default: the stops beyond a change's
     gates its person should expect`; the Metrics paragraph says "against the gates the way of
     running requires plus `metrics.stop_allowance`"; the retired-key text may name
     `metrics.target_stops` as its example.
   - M2 in DIRECTION.md, per the R6 diff.
   - M2's `Groups:` holding `007` is an acceptance check (only a revert of this edit could fail it),
     so it goes in `checks.md`, not the suite: `sdlc.py retro` piped to a `python3 -c` assert that
     M2's groups are `007` and the one seed, with no direction `problems`.
   - Run `sdlc.py record`; `drift` should report nothing.
5. **Dogfood and gate.**
   - Write `work/007-stop-target/checks.md`:
     - O3 names the gates per tier (`grep -Fq 'at the gates its tier passes and at most one more'
       .sdlc/PRODUCT.md`);
     - M2 groups 007 (the `retro` JSON check above);
     - no `target_stops` left in `scripts/` except `RETIRED_KEYS`
       (`grep -c target_stops scripts/sdlc.py` = 1 and none in `scripts/metrics.py`).
   - Run `sdlc.py checks 007`, then `sdlc.py accept 007`.
   - Run `./check.sh`.
   - Run the spec's verification line to see this repo's groups with their targets and `over`.

## Tests

- **R1:** `test_config_resolution.py` metrics tests (default 1, kept 0, `-1` warns)
- **R2:** `test_retired_keys_point_at_live_keys` (now non-vacuous),
  `test_a_host_still_setting_target_stops_is_told`
- **R3:** `test_target_is_the_gates_plus_the_allowance` (parametrized: T1 4, T1+plan 5, T2 6,
  allowance 0), `test_allowance_round_trips_in_the_trailer`, `test_history_summary_…` updated
- **R4:** `test_retro_reads_what_close_measured…` updated,
  `test_old_and_new_trailers_read_against_their_own_targets`
- **R5:** `test_defaults.py` own-copy tests; `checks.md` (O3 wording)
- **R6:** `checks.md` (M2 groups 007, no problems)
- **Gate:** `./check.sh`

## Rollback

`git revert` restores everything: the config key, the docs and this repo's `.sdlc/setup.json`. It
doesn't cover:
- **Hosts that already moved to `stop_allowance`:** under the old code it's an unknown key with a
  warning, and `target_stops` falls back to 2.
- **`Close` commits written with `allowance=`:** the old code ignores the unknown field and reads
  `target=` as written.
- **Issue #7's body.**
