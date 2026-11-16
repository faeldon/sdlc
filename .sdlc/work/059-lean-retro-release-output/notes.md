# 059 — Leave each change's measured numbers out of retro's and release's output · notes

## Sizes (this repo, 18 changes since v1.7.0, as printed)

- `sdlc.py unreleased`: 105,217 bytes with `--metrics` (as before), 26,105 without (R5's bar was
  45,000).
- `sdlc.py retro`: 173,394 bytes with `--metrics`, 89,255 without.

## Departures from the spec

- **`open_marks()` reports `triaged` and `needs_info` as booleans**, not the label set the spec's
  design named: the label names stay the tracker's, so core never spells GitHub's labels.
- **The path listing for `gone` uses git's default quoting**, as the numstat the hotspots' paths
  come from does, so a non-ASCII path compares (F1: `core.quotePath=false` here called a present
  `café.py` gone). A listing that fails leaves `gone` None (F5).
- **`mark_issues` uses the one listing only on a full pass** (close, `mark-triaged`); `sync`'s pass
  over a change's own `closes:` lists the numbers alone, as before, and a failed marks listing falls
  back to the numbers (F3).
- **The retro skill's `hotspots` line** now says what `lines: null` with `gone` means (R10 named the
  skill only if needed: it described `hotspots` without saying).
