DECISION: READY

**Why:** In round 1 both reviewers (`code` and `behaviour`) gave `VERDICT: PASS`, and the gate is green (`./check.sh`, exit 0, 2934 passed, `test_nothing_local` included). The new doc and the CONTRIBUTING row match what the intent asks for. The builder checked every "captured" status against the code and corrected the six that overstated, as the intent's constraint requires. `notes.md` records each correction, and the behaviour reviewer confirmed that the doc differs from the approved `draft.md` only in those status lines. Nothing in the reviews suggests the intent was wrong. The doc changes no code and no rule.

**Open items**
- None. No CHANGE is open in either review, and `findings.md` lists no findings.

**Decisions to confirm**
- None. This change has no `decisions.md`, no blocking line and no open default.

**For the person at ship**
- Read the six corrected statuses in `docs/RETRO-SCORECARD.md` first: Throughput, Test health, Cost per landed change, Spend by role and model, Cost per unit of output, and Context per run. They are the only place the doc departs from the draft you approved. The reviewers spot-checked just two of them (`out_per_line` and `throughput`) against `scripts/retro.py`.
- Check the new Layout row in `docs/CONTRIBUTING.md`.
- `draft.md` stays in the change folder on purpose, as the approved source. Close removes it along with the folder.

- IMPACT: none — only `docs/RETRO-SCORECARD.md` (new) and a row in `docs/CONTRIBUTING.md` change. `docs/` isn't copied into a host, and no script, skill or rule reads either file.

**Undone items**
- UNDONE: Hosts: the scorecard reaches hosts when S14 and S15 build it into the plugin: the numbers in
  `sdlc.py retro` (core, language-neutral), the page in `templates/retro.md` (a host overrides it in
  `.sdlc/templates/`), the synthesis questions in a `guide/` file a host extends, and the metrics'
  meanings in `docs/REFERENCE.md`'s *Retrospectives*. This doc stays this repo's design reference.
  In a host, the Simplicity pillar means the process's overhead and workarounds there; the plugin's
  own surface (skills used, footprint, growth) is this repo's measure alone. The structural debt
  index comes from the host's own `retro.indicators`, in its language. → seed: Scorecard in hosts: how S14 and S15 split it across core, template, guide and REFERENCE
- UNDONE: Hosts: lead time needs a start time in every host. Here a change's GitHub issue gives it; a host
  on local numbering has no issue, and `intent.md`'s `created:` holds only a date. S1 has `new`
  record a timestamp. → seed: `new` records a start timestamp so every host gets lead time (fold into S1, 2026-11-18-94)
- UNDONE: Hosts: the skills' cases are this repo's only, so nothing about them is in a host's scorecard,
  and a host with no factory gets the by-hand view: mode comparison and pipeline health say "no
  factory changes" rather than show zeros. → seed: Scorecard in a host leaves out the skills' cases and says "no factory changes" rather than zeros
