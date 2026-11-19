DECISION: READY

**Why.** All three round-1 reviewers returned `VERDICT: PASS` with no Critical, High or Required findings. The gate is green on build `da7c20be44804a70` (`./check.sh`: 3331 passed, 29 skipped, `claude plugin validate --strict` passed). The test reviewer found a named test for each of R1–R19, with R17, R20 and R21 covered by `checks.md`, the gate and the review. The behaviour reviewer ran the JSON line and saw R4, R13 and R18 work: 15 scorecard rows, `per_week: None` with `why: 'window under a week'`, and `bisections` carrying `per_change`. `drift` shows `breaking: []` and the stale REFERENCE.md sentences are gone. Where the build departs from the plan, `plan.md` explains it, and nothing in the reviews suggests the spec was wrong.

**Open items**
- None. Three nits are recorded in `findings.md` and none needs a change before landing:
  - F1 (code): `_trend` compares the unrounded value with the rounded `last`.
  - F2 (code): `_minutes` rounds a median response to a whole number.
  - F3 (test): the Speed pipeline terms are matched as bare substrings.

**Decisions to confirm**
- None. This change has no `decisions.md`, so there are no blocking decisions and no open defaults.

**For the person at ship**
- **Look first at `scripts/retro.py`.** Check `report_figures()`, the single path that `retro()` and `retro_report()` now share. Then check `scorecard()`, `_trend()` and `render_report()`'s fallback: when an override has no `{{scorecard}}`, `{{window}}` keeps the Value band, the coverage lines and the by-way table.
- **Then look at `templates/retro.md`.** It has the new layout and is an irreversible path.
- **Contract you already approved: `TEMPLATE_READS["retro.md"]` and `drift`'s `breaking`.** The change adds only the `Scorecard` heading and the `{{scorecard}}` placeholder. You approved this in spec.md *Contracts touched* (R11). A host whose override lacks the two will now see them under `breaking` in `drift`.
- **Contract you already approved: `retro`'s JSON.** It gains `scorecard`, `by_way.throughput[way].why`, and `per_change` on `pipeline.landing.bisections` and `accept_stops`. All of these are additions. You approved them in spec.md R4, R13 and R18.
- **Contract you already approved: `indicators.host_rows()` is stricter.** It now rejects a `—` unit, and a name or unit with stray spaces. You approved this in spec.md R15.

- IMPACT: minor — a host's retrospective now opens with the scorecard and `retro`'s JSON gains new fields, while an existing override still renders as before. The one thing a host may need to do is add `## Scorecard`/`{{scorecard}}` to its override, since `drift` will list them under `breaking` until it does.

**Undone items**
- UNDONE: `render_report()` now takes eight positional blocks and five keyword ones. One figures dict (`report_figures()`'s) passed whole would read better, but the tests' many `render_report(template, process)` calls would all change with it, so it stays out of 184. → seed: Pass report_figures() to render_report() as one dict
- UNDONE: A scorecard row whose block has no `missing_because` (response by tier, autonomy, the workarounds) says `none in the window` when null, even when the window held changes that just weren't measured: R5's rule as written. A per-row reason would need those blocks to carry one. → seed: Give response, autonomy and workarounds blocks a missing_because so scorecard rows name their real reason

**How to recover**
- RECOVER: templates/retro.md: `git revert <the change's commit>` restores the old template, `TEMPLATE_READS` and `.sdlc/setup.json` together. What a revert can't undo is the reports hosts committed while this version was out. Those stay in their history in the new layout, and an older `report_rows()` still reads their indicator table by its own header, so nothing is misread. A host that copied the new template into `.sdlc/templates/` keeps its copy and must remove it by hand. If that copy needs undoing, fix forward: a follow-up change that makes `{{scorecard}}` optional again in `TEMPLATE_READS` and runs `sdlc.py record`.
