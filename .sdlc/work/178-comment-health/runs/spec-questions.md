
Resolved:
- *How is a narration comment told from a useful one without a model call?* A comment block of at most 2 lines is narration when at least half of its words (3+ letters, identifiers split, stopwords removed) appear in the code line it describes. Comments are found with `tokenize`, and the rule is pinned by examples both ways (R7). It is deliberately narrow, because the figure is read as a trend.
- *Where does "the comment share of agent input tokens" come from?* An estimate from the files themselves: comment and docstring bytes over all bytes of the base branch's scripts, plus est. tokens at bytes/4 as `prose_metrics()` uses (R8). Transcripts are rejected: they are per machine, outside the repo, and no record keeps per-file reads (`metrics.py` records edits only).
- *"Trend across the window"* is the report's existing `Last retrospective`/`Change` columns from 177. It needs no code beyond stable names and units (R4).

Left for the person:
- **"The retrospective shows them in the Quality pillar."** The report has no pillars until S14, so this change shows the rows under `## Indicators`. There are three options:
  - (a) Accept that, and let S14 place them. This is what the spec assumes.
  - (b) Add a `"pillar": "quality"` extra key to each row now, so S14 can group by it. That is a small step toward a row-shape convention that 177 didn't set.
  - (c) Hold this change until S14.
- **Thresholds.** `LONG = 30`, `BAND = 0.10–0.40` (both from the seed), `NARRATION_OVERLAP = 0.5` and `NARRATION_MOST_LINES = 2` (mine). Stricter narration values mean fewer false flags and a smaller share. Looser ones catch more, but would flag "why" comments that happen to reuse an identifier.
- **The repo-wide density.** As written, it pools lines across all files, so `sdlc.py` dominates. A median of the per-file densities would weight each file equally instead.
