# Notes

- [x] A `unit` that is literally `—`, or a `name` or `unit` with leading or trailing spaces, is → seed: 2026-11-19-39
  accepted by `host_rows()` but reads back from the report as a different key (`""`, or
  stripped), so it gets no `last`. R1 doesn't forbid either; rejecting them would be a one-line
  rule in `host_rows()` if it ever matters.
- [x] `sdlc.py retro` from a change's worktree runs the main checkout's `.sdlc/function-heat.py` → dropped: it resolves itself when the change lands. It is a note about verifying from a worktree, not work left to do.
  (`main_root()`), so the spec's `retro` verification line shows rows only once this lands.
