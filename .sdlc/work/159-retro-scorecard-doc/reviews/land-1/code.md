VERDICT: PASS

The new `## Hosts` section is in `docs/RETRO-SCORECARD.md`, between *Insights* and *Seeds to build it*. It covers each part of the request:
- **Where the parts go:** numbers in core `sdlc.py retro`, the page in `templates/retro.md` (a host overrides it), the questions in a `guide/` file a host extends, and the meanings in REFERENCE.md's *Retrospectives*. The doc stays the design reference.
- **Two figures that read differently in a host:** Simplicity means the process's own overhead, and the structural debt index comes from the host's own `retro.indicators`.
- **Lead time:** a host on local numbering has no issue and `created:` holds only a date, so S1 has `new` record a timestamp.
- **What a host's scorecard leaves out:** the skills' cases, and it says "no factory changes" rather than showing zeros.

The seed references check out against the seeds table: S1 is lead time, and S14 and S15 are the scorecard and the Insights questions. The edit touches the doc only, and its wording avoids naming any host project, so the nothing-local rule isn't at risk.

## Notes
- Done well: the section is short, keeps to the design-reference role, and ties the lead-time need to S1, where the work will happen.
- NIT: docs/RETRO-SCORECARD.md:443: "the mode comparison and pipeline health" names parts the doc calls S9 and S10 and doesn't define under those exact words, so a reader may not know which sections are meant. Name the seeds, or the figures. {docs S low}
- Ran no tests. I read the builder's evidence in `build/land-1.md`, which shows the acceptance checks and `test_nothing_local` passing, and I checked the section's seed references and wording against the doc.
