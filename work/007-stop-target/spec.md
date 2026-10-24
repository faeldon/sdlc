---
id: 007
slug: stop-target
kind: spec
created: 2026-10-24
updated: 2026-10-24
---

# 007 — Reconcile O3's two-stop target with the gates a change passes · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1. The allowance replaces the flat target.** `CONFIG_KEYS["metrics"]` gains `stop_allowance`
   (a whole number, at least 0, default 1: the stops beyond a change's gates its person should
   expect), and loses `target_stops`. `INT_KEYS` follows. `config` prints `stop_allowance`. Tests:
   the `metrics` section resolves to `{"transcripts": True, "idle_minutes": 30, "stop_allowance":
   1}`, a host's `stop_allowance = 0` is kept, and `-1` is a warning.
2. **R2. The old key is retired, loudly.** `RETIRED_KEYS["metrics.target_stops"]` holds:
   - `now`: `metrics.stop_allowance`;
   - `since`: `2.0.0`;
   - `do`: "Delete it. A change's target is now its gates plus `stop_allowance` (1 by default);
     set that instead if you want a different allowance."

   A host still setting `target_stops` gets `load_config`'s unknown-key warning, and `drift`
   reports the key as breaking with that fix. The existing `test_retired_keys_point_at_live_keys`
   now runs over a real entry, and a test sets `target_stops = 2` in a host and finds both.
3. **R3. Close measures each change against its own target.** In `summarize()` and
   `history_summary()`:
   - `totals["target"]` is `len(required) + cfg["stop_allowance"]`, so `required` and `target`
     move together, `plan` included for a Tier 1 change that used plan mode;
   - `totals["allowance"]` is the allowance used;
   - `Sdlc-Totals` gains `allowance=`, and `target=` keeps its name, meaning the target this change
     was measured against.

   Tests:
   - a Tier 1 change by hand is 3 + 1 = 4;
   - one that used plan mode is 5;
   - Tier 2 is 6;
   - an allowance of 0 gives the gates alone;
   - the trailer round-trips through `parse_trailers`.
4. **R4. Retro reads old and new commits alike.** For each change, the target is its trailer's
   `target` when the trailer has `allowance=`, else its `required` plus the configured allowance,
   so an old `target=2` is never used. Each group reports:
   - `target`: the median of the per-change targets, replacing "the last change's";
   - `median.over`: the median of `stops − target`.

   Tests: one old-style trailer (`required=5 target=2`, no allowance) reads as target 6; a group
   mixing old and new commits gives the right medians.
5. **R5. The words agree.**
   - **`.sdlc/PRODUCT.md` O3** becomes: "O3. **Few stops.** Each change stops its person at the
     gates its tier passes and at most one more (Tier 1 by hand: intent, ship and close, plus plan
     when plan mode ran; Tier 2: intent, spec, plan, ship and close). Measured by: the stops above
     that target close records per change, by tier and way of running". The rest of the doc is
     untouched.
   - **The process doc's "Where a change's time and tokens go"** signal, in `defaults/SDLC.md` and
     `.sdlc/SDLC.md` word for word, says stops are measured against the change's gates plus
     `metrics.stop_allowance`.
   - **`docs/REFERENCE.md`:** the config sample line, the *Metrics* paragraph, and the
     after-an-update section's retired-key example if it has one.
   - **This repo's `.sdlc/setup.json`:** re-recorded.
6. **R6. The direction doc tracks this change by its number.** In `.sdlc/DIRECTION.md`, M2 changes
   in two places:
   - Its `Groups:` line names the change as `007` instead of the quoted title. A quoted entry is
     read as a seed, and with no seed or `idea:` behind it, the next retrospective would report it
     "vanished" (`_milestone_verdicts`).
   - Its text names `metrics.stop_allowance` instead of the retired `metrics.target_stops`.

   M2's id, heading and status don't change, and nothing else in the doc is touched. A test
   asserts that `sdlc.direction_items()` finds `007` in M2's changes and no seeds besides "Ship
   does its own landing edits", and that the doc has no `problems`.

## Design

`summarize()` already builds `required` per change (`REQUIRED[(way, tier)]`, plus `plan` for
Tier 1 in plan mode). The target becomes one more line beside it:
`target = len(required) + cfg["stop_allowance"]`. `history_summary()` does the same from its own
`required`.

`metrics.py` stays pure: `cfg` is the `metrics` section, passed in as now. The trailer writer emits
every key of `totals`, so `allowance` appears with no change to `trailers()`, and
`parse_trailers()` reads any `key=value`.

In `metrics_summary()`, a helper `_target(m, allowance)` returns `m["totals"]["target"]` when
`"allowance" in m["totals"]`, else `required + allowance`, with `allowance` from the current
config. `"over"` is computed per change from that and joins the medians; `"target"` becomes their
median. Nothing reads `target_stops` after this.

## Contracts touched

- **The trailer format is a contract: extend, never redefine.** `allowance=` is a new field.
  `target=` keeps its meaning, "the stop target this change was measured against": the value is
  now computed per change rather than taken from one config number. Old commits parse unchanged,
  and retro recomputes their target from their own `required=`, so their `target=2` isn't compared
  against new ones.
- **A config key's meaning changes (Tier 2), and a key is renamed.** This is **`impact: major`**:
  a host that set `target_stops` has to change its config (the process doc's impact table:
  "something renamed, removed or moved"). The next release is 2.0.0. `RETIRED_KEYS` is the
  mechanism 002 built for exactly this: "Rename or drop a config key … and that table gets the
  entry in the same change" (`AGENTS.md`).
- **Not a shim.** Nothing reads `target_stops` any more, so the registry from 003 gets no entry
  (`AGENTS.md`: a retired key "is not a shim").
- **Measuring never refuses:** a missing or bad `stop_allowance` falls back to the default, with
  `load_config`'s warning.
- **The defaults and this repo's copies:** the signal edit lands in both, word for word.
- **The product doc:** only O3's line changes, as approved here.
- **The direction doc is the retrospective's.** `retro-commit` writes it each run and refuses one
  that drops an open id. This edit keeps M2's id and status, changes only how M2 names its change
  and the renamed key, and lands in this change's commit, so the next retrospective reads it from
  history like any other version.
- **Nothing local:** fixtures use neutral numbers.

## Alternatives rejected

- **Keep `target_stops` as a shim until 2.0.0:** a minor release now, but two meanings for one
  number for a release cycle. The person chose to retire it.
- **Redefine `target_stops` as the allowance:** a host's 2 would silently change meaning.
- **A per-tier allowance:** configuration nobody has asked to set. One allowance at every tier
  covers the design question Tier 2's spec usually asks.
- **Count permission prompts as stops:** they depend on a host's settings, and close already
  reports them apart.
- **Lower the gates to meet a target of 2:** rejected at intent; the gates stay.

## Verification

```bash
./check.sh                                                          # all pass
uv run --group dev pytest tests/test_metrics.py tests/test_retro.py tests/test_config_resolution.py tests/test_setup_lifecycle.py -q
uv run --quiet --script scripts/sdlc.py retro | python3 -c "import json,sys; print({k: (g['target'], g['median']['over']) for k, g in json.load(sys.stdin)['metrics']['groups'].items()})"
# this repo's six closed changes: tier 1 target 4 (or 5 with plan mode), tier 2 target 6, and the stops over it
```
