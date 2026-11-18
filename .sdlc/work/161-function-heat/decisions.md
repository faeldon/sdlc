# Decisions

- [x] D1 (builder round 1, default): Output stays a plain-text table now, with JSON left to S8. Going ahead unless told otherwise. → settled by the approver: The intent's Outcome says the output is "a plain-text table", which answers its own open question about the format. The output is read only by this repo's `retro.indicators`, so it is no published interface. Both reviewers found it consistent with the intent (code.md Notes, behaviour.md Notes).
  - OPTION: plain text now — matches the Outcome and reads fine in `architecture.host`; S8 changes the output format
  - OPTION: JSON from the start — S8 wouldn't need a format change; harder to read in the report today
  - WHY: the intent's Outcome says "a plain-text table"
- [x] D2 (builder round 1, default): Rank by commits, then size, with size shown beside it (not commits × size). Going ahead unless told otherwise. → settled by the approver: The intent's Outcome says "ranked by commits then size", the same order as the hand-run analysis it cites. The code reviewer confirmed the ranking against Outcome 1, and a test pins "commits, then size, cut to the top N" (build/round-1.md).
  - OPTION: commits, then size — matches the hand-run analysis and the Outcome
  - OPTION: commits × size — one score, but a huge function changed once can outrank a small one changed often
  - WHY: the Outcome says "ranked by commits then size"
- [x] D3 (builder round 1, default): Count a commit only if it still owns some of a function's lines (blame), so a commit whose lines a later commit rewrote isn't counted. Going ahead unless told otherwise. → settled by the approver: The intent's Approach specifies `git blame --line-porcelain` and counts the distinct commits after the boundary within each function's range. The builder implemented exactly that, and the code reviewer marked the porcelain parsing as done well. Choosing a more exact diff walk instead would be a new approach, not a gap in this one.
  - OPTION: blame-based — what the Approach names, and fast; undercounts functions that were rewritten again and again
  - OPTION: walk each commit's diff (`git log -L` or similar) — exact count; much slower and more code
  - WHY: the Approach specifies `git blame --line-porcelain`
