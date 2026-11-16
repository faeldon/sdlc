---
id: 059
slug: lean-retro-release-output
kind: spec
created: 2026-11-16
updated: 2026-11-16
---

# 059 — Leave each change's measured numbers out of retro's and release's output · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1.** `sdlc.py unreleased` prints each change without its `metrics` key by default;
   `--metrics` prints it as before. Tests pin both.
2. **R2.** `sdlc.py release` (with `--check` and a real run) prints its report's `changes` without
   `metrics`; `--metrics` restores it. Tests pin both.
3. **R3.** `sdlc.py retro` prints `changes` and `dropped` without `metrics`; `--metrics` restores
   them. Tests pin both.
4. **R4.** `unreleased()` and `retro()` still return the full records: the key is left out only
   when printing. Retro's printed output with and without `--metrics` is identical apart from the
   per-change `metrics` keys, the top-level `metrics` summary, `dropped_cost` and `bugs`
   included, pinned by a test.
5. **R5.** `unreleased` on this repo goes from about 105 KB to at most 45 KB; the before and after
   figures for `unreleased` and `retro` are recorded in `notes.md`.
6. **R6.** The retro and release skills read no per-change `metrics` (their text checked, a test
   asserting neither names `changes[].metrics`); they run the commands without the flag, and
   their `allowed-tools` are unchanged. `docs/REFERENCE.md` and `AGENTS.md`'s metrics paragraph
   name `--metrics`.
7. **R7.** Nit 2026-10-25-15: `next_up()` walks `closed_changes(home, None, …)` at most once per
   call; `_milestone_verdicts()` takes the history its caller already holds. A test counting the
   calls (monkeypatch) fails on a second walk.
8. **R8.** Nit 2026-10-26-2: `mark_issues()` takes one listing of open issues with their labels
   and comments from the tracker, and skips a recorded issue already labelled `triaged`, not
   `needs-info`, with its marker in a comment, and whose record names no `parent` and no `close`:
   no `gh issue view` for it. A tracker without the new listing keeps today's behaviour. A
   fake-`gh` test counts the views: none for an issue already marked, one for an unmarked one and
   for one with a parent. The tracker still never reads `.sdlc/`.
9. **R9.** Nit 2026-10-27-8: `_inbox_commit` takes at most four parameters, or is folded into
   `cmd_inbox_commit` under its lock; a signature test, and every existing `inbox-commit` test
   passing unchanged.
10. **R10.** Nit 2026-11-12-1: each `hotspots()` entry carries `gone`, from
    `git ls-tree -r --name-only` on the base branch: `lines` is `None` with `gone: false` for a
    binary or empty file, `gone: true` once it's deleted. The docstring says so. Tests in
    `tests/test_indicators.py`: a binary file, an empty one, a deleted one. `indicators.py` stays
    pure: `sdlc.py` hands it the listing's text.
11. **R11.** `./check.sh` exits 0.

## Design

**Printing.** One helper, `_lean(changes, metrics)`, returns each record without `metrics` unless
the flag is set. `cmd_unreleased` applies it to `changes`, `cmd_release` to `report["changes"]`,
`cmd_retro` to `changes` and `dropped`. Each subparser gains `--metrics` ("each change's measured
numbers too"). Aggregates are computed inside `unreleased()` and `retro()` first, so nothing
upstream changes; `status`'s use of `unreleased()` is untouched.

**R7.** `next_up` reads history lazily through a small closure, `history()`, cached on first use,
and passes it to `_milestone_verdicts(home, items, open_names, trunk, history=None)`, which walks
only when given none. `retro()`'s call passes `None` (its window differs).

**R8.** `GithubTracker` gains `open_marks(limit)`: one
`gh issue list --state open --json number,labels,comments`, returning
`{number: {"labels": set, "comments": [bodies]}}` or `None`. `mark_issues` prefers it (falling back
to `open_numbers` when a tracker lacks it) and skips each record R8's rule says is already done.
`mark()` is unchanged for what it does run.

**R9.** `cmd_inbox_commit` gathers its state into a dict, and `_inbox_commit(root, home, state,
report)` reads it: a mechanical move, no behaviour change.

**R10.** In `_architecture()`, `sdlc.py` runs one more read,
`git ls-tree -r --name-only <trunk>`, and passes the path set to `hotspots(…, present=…)`.

## Contracts touched

- **Metrics trailers are a contract**: untouched; only the printed JSON loses a key; parsing
  unchanged.
- **Trackers never read `.sdlc/`; core decides, the tracker sets**: `open_marks` only lists; core's
  `mark_issues` decides what to skip, from `recorded_issues()`.
- **`scripts/trackers/` is sensitive** (`review.sensitive`): ship runs the deep review, with the
  fresh-context reviewer and the build check (none configured).
- **`indicators.py` is pure** (no subprocess, no import of `sdlc.py`): it still receives text.
- **Windows**: the new subprocess goes through `_git` / `self._gh`, which already pass
  `encoding="utf-8"`; no new `write_text`.
- **`READ_ONLY` and `ALLOW_RULES`**: unchanged; `unreleased` and `retro` are run without the flag,
  so no rule is needed for it.
- **`test_release_publish_and_measuring_never_read_the_register`**: untouched; the `mark_issues`
  change is intake, not release.

## Alternatives rejected

- **Not computing the per-change metrics by default**: retro's summary needs them; leaving them out
  is a printing decision.
- **Dropping `changes` from `release --check`**: release's report shows what the release holds;
  without metrics the list is small.
- **A small per-change summary (stops, elapsed)**: no skill reads one; `--metrics` gives the whole.
- **Trimming per-change `findings` too**: 5 KB, and retro's bug pairing and review figures are
  built from them: little to gain for the risk.
- **Skipping issues with a parent from the listing**: `gh issue list` can't return the parent, and
  a wrong skip leaves a parent unset.

## Verification

```bash
uv run --group dev pytest -q tests/test_retro.py tests/test_release.py tests/test_archive.py tests/test_indicators.py tests/test_inbox.py
uv run --quiet --script scripts/sdlc.py unreleased | wc -c            # ≤ 45000 (from ~105000)
uv run --quiet --script scripts/sdlc.py unreleased --metrics | wc -c  # ~105000, as before
./check.sh                                                            # exit 0
```
