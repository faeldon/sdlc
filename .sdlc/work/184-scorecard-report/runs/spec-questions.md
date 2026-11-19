
Resolved from the code:
- **One new layout, or new placeholders in the current one?** A new layout: Scorecard first, then one section per pillar. Only `{{scorecard}}` and its heading are required (`TEMPLATE_READS`), because the next retrospective reads its table back. An override that doesn't have it renders as it does today (R10), because `render_report()` already leaves alone a placeholder that isn't in the template.
- **Which figure is each pillar's headline and guardrail?** The ones in the table under *Design*. Each is chosen from what `retro` already computes. The design-debt index stays in the host's indicators. A guardrail that is another pillar's headline is a line under the table, not a row repeated.
- **Nit 2026-11-19-35.** Each command already ran `_cost` only once. The duplication was two code paths, which `report_figures()` removes. `retro` and `retro-commit` remain two processes.

Left for you:
- **Pooled or split headlines.** As drafted, lead time, response time and dollars are one row per way or per tier, because the JSON has no pooled median and the intent rules out new figures. If you'd rather have one row per pillar, `process.lead`, `process.time` and `cost.per_change` each need a pooled median: small, but new figures.
- **Seed 2026-11-19-59.** Drafted as `per_week` null under seven days, with its reason. The seed's other option is a one-week floor, which understates a short window.
- **Missing pillar placeholders in `drift`.** Drafted as not breaking; `drift`'s existing `changed` note covers them. Say if you want `drift` to name each missing pillar placeholder anyway, as a new non-breaking report class.
