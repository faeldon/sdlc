# Notes

- [x] The builder's `resolve` task (`agent --task resolve`, `prompts/resolve.md`) gets no → dropped: not worth doing; the landing loop never runs the builder's `resolve` task, and `--continue` already accepts a modify/delete resolution from either task.
  `deleted` part: the landing loop only runs `train-resolve`, and the resolve prompt tells the
  builder to run no git command, which the deleted part's reads would contradict. `--continue`
  takes a modify/delete resolution from either.
