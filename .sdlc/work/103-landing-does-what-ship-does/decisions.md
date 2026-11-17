# Decisions

- [x] D1 (builder round 1, default): Keep the `resolve` counter-only conflict fix in this change, or split it into its own? Options: keep; split. Recommend keep: R13's batch of three can't land without it, and it's about 10 lines in the landing's own `cmd_resolve`, plus the skill's Step 3 split. → decided: keep the resolve fix in this change
