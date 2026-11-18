VERDICT: PASS

I checked all 60 open register entries against the new *Waves* section. Each is named exactly once, with none missing and none duplicated.

## Notes

- Each outcome item is covered:
  - **Waves:** the *Waves* section replaces *Suggested order*, with waves 0–6 in order.
  - **Done waves:** waves 0 and 1 are marked done, with the change numbers 160–164 beside each seed or refactor.
  - **Wave 1½:** it takes bug -95 with idea -91, and bug -103 with idea -66.
  - **Wave 6:** it holds the backlog outside the scorecard.
  - **S17:** the row sits after S13 in the *Data* table, and its S8 dependency is noted.
  - **S5:** its row names the feature map, 2026-10-25-3.
  - **Rest of the doc:** the diff touches only `docs/RETRO-SCORECARD.md`, and only those two places.
- The doc names ids only and never copies an entry's text. It has no machine path and no bare `work/NNN` citation.
- Decision D1 is a `[default]` that the builder raised: put 2026-11-19-1 and -2 under R6. The plan words it as "retires them as answered", which fits that default.
- NIT: `docs/RETRO-SCORECARD.md` (the S17 row): the row runs well past 100 columns, but the neighbouring table rows do the same, so it is consistent. {style S low}
- I ran no tests. The gate record `build/round-1.gate.md` says PASS. I compared the ids in the doc against `inbox.md` by script, and I read `sdlc.py status --all` for the table of open entries.
