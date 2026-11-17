# Decisions

- [x] D1 (builder round 1, default): Should the plan hint read only list-item lines of `## Files to change`? Options: every line, as the spec says; list items only. Going ahead with every line. It is loose in practice: this change's own plan counts 14 "files" because wrapped lines contribute dotted names like `progress.fraction`. I'd recommend list items only as a follow-up. → decided: list items only, fixed before 088 lands
