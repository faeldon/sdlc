# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Statuses corrected from the draft

The doc is `draft.md` as approved, with every "captured" status checked against `scripts/retro.py`,
`scripts/metrics.py` and `plugins/factory/scripts/factory.py`. Six overstated, and now say what
the code holds:

- **Throughput:** `process.throughput` counts per week by tier, not by impact. Now *partly*; by
  impact needs S2 (by mode still S9).
- **Test health:** `retro` reports suite times (`tests.times`) and drifted tests, but never reads
  the skills' cases' scores; ship and release do (`_cases_report()`). Now *partly*.
- **Cost per landed change:** dollars live in each factory change's `runs/costs.jsonl`, summed per
  change by `run_cost()` (`factory.py ready`, the hand-back to `stage: test`, the board), but
  `retro` reports no dollars across changes. Now *partly*, needs S4.
- **Spend by role and model:** `retro`'s `spend.agents` groups runs by role and model, from
  `Sdlc-Role` lines, but counts behaviours (edits, tool errors, test runs), not dollars. Now
  *partly*, needs S4.
- **Cost per unit of output:** `spend.out_per_line` is out tokens per added code line, not dollars
  per 100 lines. Now *partly*; dollars need S4.
- **Context per run:** `prose` estimates each skill's size (bytes / 4); no trailer measures what a
  skill run read, only each change's tokens. Now *captured as an estimate*.

The rest held: `rework`, `bugs.rate`/`escapes`, `bugs.important` and recurring classes,
`bugs.days_to_fix`, the `response`/`stops`/`target` clocks, `Sdlc-Landed … unreviewed=`, `auto=`,
`Sdlc-Mode`, `Sdlc-Tool`/`Sdlc-Calls`, `unmeasured` (its three signals match `UNMEASURED`), the
architecture pass's hotspots, co-change, largest and totals, the cases' `claude` field, the
milestone verdicts, and each change's `release`.

`draft.md` stays in the folder as the approved draft the doc came from.

## Hosts (added by the person, 2026-11-18)

- [x] Hosts: the scorecard reaches hosts when S14 and S15 build it into the plugin: the numbers in → seed: 2026-11-18-105
  `sdlc.py retro` (core, language-neutral), the page in `templates/retro.md` (a host overrides it in
  `.sdlc/templates/`), the synthesis questions in a `guide/` file a host extends, and the metrics'
  meanings in `docs/REFERENCE.md`'s *Retrospectives*. This doc stays this repo's design reference.
  In a host, the Simplicity pillar means the process's overhead and workarounds there; the plugin's
  own surface (skills used, footprint, growth) is this repo's measure alone. The structural debt
  index comes from the host's own `retro.indicators`, in its language.
- [x] Hosts: lead time needs a start time in every host. Here a change's GitHub issue gives it; a host → seed: 2026-11-18-106
  on local numbering has no issue, and `intent.md`'s `created:` holds only a date. S1 has `new`
  record a timestamp.
- [x] Hosts: the skills' cases are this repo's only, so nothing about them is in a host's scorecard, → seed: 2026-11-18-107
  and a host with no factory gets the by-hand view: mode comparison and pipeline health say "no
  factory changes" rather than show zeros.
