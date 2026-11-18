# Notes

- [x] `_no_verdict()` and `NO_DECISION` still say "doesn't open with VERDICT…/DECISION…", which → seed: 2026-11-18-47
  the spec kept so the board's and status's problem text doesn't move. Since `opening()` now reads
  an answer after prose, the words now mean "holds no answer the script reads". A rewording
  would change the board's and status's text together, and their pins with it.
- [x] `tests/fixtures/stream-two-replies.jsonl` keeps only the type, subtype, ids and task fields → dropped: this explains a deliberate trim, not leftover work; the parser reads only `assistant` and `result` events, and the behaviour reviewer accepted it.
  of its `system` and `rate_limit_event` lines. A real `init` event lists the machine's plugins,
  skills and MCP servers, which name local projects. The `assistant`, `user` and `result` lines
  are whole, with paths replaced by `<path-to-clone>` and `<home>`.
