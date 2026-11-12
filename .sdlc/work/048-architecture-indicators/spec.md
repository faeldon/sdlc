---
id: 048
slug: architecture-indicators
kind: spec
created: 2026-11-12
updated: 2026-11-12
---

# 048 — Architecture indicators for the retro loop · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. `sdlc.py retro` prints a new top-level `architecture` block; every other key keeps its shape and
   meaning (`changes[].files` and `lines` included). A test pins the existing keys.
2. **Size per change.** Each closed change in `changes` gains `added`, `deleted` and `by_kind`
   (`code`, `tests`, `docs`, each `files`, `added`, `deleted`), from the numstat `retro()` already
   runs; null where `files` is null today. `architecture.size` gives, per tier, the change count and
   the median `added`, `deleted` and `files`, overall and by kind. A test with one change per tier
   pins the numbers.
3. **Kinds.** A path is `tests` when a directory in it is `test`, `tests`, `spec` or `__tests__`,
   or its name matches `test_*`, `*_test.*`, `*.test.*` or `*.spec.*`; `docs` when it ends `.md`,
   `.rst`, `.adoc` or `.txt` or sits under a `docs/` directory; else `code`. `retro.test_paths` and
   `retro.doc_paths`, when set, replace that kind's conventions: lists of `dir/` prefixes or globs,
   matched by `risk_paths()`, tests checked before docs. `architecture.kinds` prints which rule each
   kind used. Tests cover each convention and each key's override.
4. **Hotspots.** `architecture.hotspots`: the 10 files touched by the most landed changes in the
   look-back, ties by more lines changed; each `file`, `changes`, `lines_changed` and `lines` (on the
   base branch now, null once deleted). Change folders and the register are left out; dropped
   changes are not counted.
5. **Look-back.** Hotspots and co-change read the last 30 closed changes on the base branch's
   first-parent line (`ARCH_LOOKBACK`), past the retrospective's boundary, or all when fewer;
   `architecture.lookback` gives the count and the first and last change. Size (R2) and growth (R6,
   R7) stay on the retrospective's window.
6. **Co-change.** `architecture.co_change`: up to 10 pairs of files touched together by 3 or more
   look-back changes, each with the pair, `together`, and each file's own count, ranked by
   `together`, then by its share of the rarer file's count. With no pair at 3 the list is empty,
   never padded. A test pins the threshold.
7. **Largest.** `architecture.largest`: the 10 largest text files on the base branch by lines,
   each with its lines at the last retrospective's commit (null when it didn't exist, or there is
   no retrospective) and `growth`. Binary files are skipped. Lines come from `git grep -I -c ''` at
   each ref, never a blob read per file.
8. **Suite and totals.** `architecture.totals`: `files` and `lines` per kind on the base branch now
   and at the last retrospective, so the suite's growth reads off `tests`. No gate runtime is
   computed: git can't tell it, and retro never runs the gate.
9. **Host indicators.** `retro.indicators`, a new list of commands, unset by default, each run
   through `_evidence()` (same timeout, cap and failure rows) whether or not a product doc exists;
   their rows are `architecture.host`. Unset, nothing runs and `host` is `[]`. A test pins both.
10. **Bounded.** `architecture` holds no per-file row beyond its capped lists: a test on a fixture
    repo with 200 files and 40 changes asserts the block stays under 8 KB.
11. **Home.** The counting lives in a new `scripts/indicators.py`: pure functions over git's output
    text and a `kind` callable, loaded by path like `metrics.py`, no import of `sdlc.py`, no
    subprocess. `sdlc.py` makes the git calls and assembles the block. A test asserts
    `indicators.py` imports neither `subprocess` nor `sdlc`.
12. **Config.** `test_paths`, `doc_paths` and `indicators` join `CONFIG_KEYS["retro"]` and
    `LIST_KEYS` (`indicators` in `COMMAND_LISTS`); `config` prints them; `.sdlc/setup.json` is
    re-recorded from this checkout so `sdlc.py drift` reports nothing here.
13. **The skill reads them.** `/sdlc:retro`'s Step 0 describes `architecture`; its architecture pass
    has each finding cite the indicator behind it (a hotspot, a co-change pair, a file's growth, a
    kind's totals, a host row), weighs a split for a hotspot or growing file that `rework_common` or
    a coupled pair backs, and says when a finding rests on reading alone. Skill invariants hold
    (`tests/test_skills.py`).
14. **Docs.** `docs/REFERENCE.md` documents the three keys in its config block and the
    `architecture` fields under Retrospectives; `guide/process.md`'s retro loop names the
    indicators; `AGENTS.md`'s map names `scripts/indicators.py`.

## Design

`retro()` already runs numstat per change in its window. R2 extends that loop: each row's lines
split into `added` and `deleted` (numstat's columns), and the path goes through `kind(path)`, a
closure `sdlc.py` builds from `risk_paths()` and the two keys, falling back to
`indicators.CONVENTIONS` for an unset key. `indicators.size_by_tier(changes)` takes the medians.

A new `_architecture(home, cfg, since, changes)` in `sdlc.py`, called once from `retro()`:

- the look-back: `closed_changes(home, None, trunk, read=False)[-ARCH_LOOKBACK:]`, each record's
  files from `_change_base()` and `diff --name-only` (or `diff-tree` on the change's commit without
  a base, as size already falls back);
- `git grep -I -c '' <trunk>`, and at `since["sha"]` when there is a retrospective;
- hands those texts to `indicators.hotspots()`, `co_change()`, `largest()`, `totals()`;
- `_evidence(home, cfg["retro"]["indicators"])`.

`indicators.py`'s functions take strings and lists and return dicts, so their tests need no repo.
`sdlc.py` loads it with a loader like `_load_metrics()`.

Edges: no retrospective yet, the `then` values and growth are null; no landed changes, empty
lists; no base branch, `architecture` is null, as `retro` treats the rest; a rename counts as
`--no-renames` already does in `retro`; a file deleted since stays in hotspots with `lines: null`.

## Contracts touched

- **`retro` is read-only but for host commands, run only in `_evidence()`.** The new key runs
  through `_evidence()`, so it stays the one place. `retro` stays out of `READ_ONLY`, as now.
- **Mechanism vs. policy.** The conventions are mechanism; the two path keys are a host's policy;
  no language or runner is assumed, and language-specific measures come through `retro.indicators`.
- **Config keys.** Three new keys whose defaults change nothing (unset: conventions, nothing runs).
  No `RETIRED_KEYS` or `TEMPLATE_READS` entry. `drift` reports them as `new` in hosts, which is what
  that class is for.
- **Loaded by path, never imported.** `indicators.py` follows `metrics.py`.
- **Windows.** No platform module, no writes; the new git call goes through `_git()` (encoding set);
  its tests are marked `portable`.
- **Release, publish and measuring never read the register.** Untouched.
- No policy changes.

## Alternatives rejected

- **Timing the gate in close (an `Sdlc-Gate` trailer from transcripts).** A new trailer contract and
  `metrics.py` work for one number a host can print itself; a seed of its own if hosts want it.
- **Growing `sdlc.py`.** It is the hotspot this change sets out to measure, and M9 wants retro's
  readers out of it.
- **Counting test functions.** Needs a language. Lines and files of the `tests` kind are what git
  tells for any repo.
- **Hotspots over the retro window only.** Seven changes make every file a hotspot or none.
- **Generated or lock files treated specially (`linguist-generated`).** No host has asked; a lock
  file in `largest` is visible and the retrospective judges it.
- **One `kinds` table key.** The loader types keys as lists, strings, ints or bools; two list keys
  fit it and `risk_paths()` with no new value type.

## Verification

- `./check.sh` passes: ruff, format, pytest (the new `tests/test_indicators.py` and retro tests),
  `claude plugin validate --strict`.
- `uv run --quiet --script scripts/sdlc.py retro | python3 -c 'import json,sys;
  a=json.load(sys.stdin)["architecture"]; print(len(json.dumps(a)), [h["file"] for h in
  a["hotspots"]][:3])'` prints a size under 8000 and `scripts/sdlc.py` among this repo's top
  hotspots.
- `uv run --quiet --script scripts/sdlc.py drift` reports nothing after `record` reruns.
