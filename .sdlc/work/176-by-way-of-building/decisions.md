# Decisions

- [x] D1 (builder round 1, default): Keep R5's "at least 1/7 week" floor for `by_way.throughput`, as specified. Going ahead with it unless told otherwise. → settled by the approver: the approved spec's R5 sets the window's floor at "at least 1/7" week, and the build does exactly that; `test_by_way_gives_every_figure_for_each_way_with_its_n` covers it. The default departs from nothing the person approved. Moving to a one-week floor or a null `per_week` would change R5, so that idea goes forward as a seed (below) rather than being decided inside this change.
  - OPTION: keep the one-day floor — matches the spec; a retro run just after the last one shows inflated per-week figures
  - OPTION: floor at one week — calmer figures early in a window; understates throughput in a short window
  - OPTION: `per_week` null under a week — never misleads; no figure until a week has passed
  - WHY: the spec's R5 sets the floor at 1/7, and changing it is the person's call
