# Decisions

- [x] R1 (person, revise): ill follow 1 and 2 defaults. go with c [the options they answer, as the supervisor put them: 1 and 2 keep the draft's defaults, a hand-built change's ready time is its ship commit and a filed issue's lead time starts at `new`; c drops R16, the unit tests alone prove the arithmetic; and the reply comes unfenced, its open questions after a bare `---` line]
- [x] D1 (builder round 1, default): A factory change with neither timed run rows nor factory sessions records `lead` and `landing` only, with no `ready_wait`. Going ahead with that unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: leave `ready_wait` out — nothing in git says when the approver finished, because the factory commits the change once, at landing; but the line is shorter than R10's wording
  - OPTION: use the tip's author date as ready — the line always has a `ready_wait`; but it would be about 0 and wrong, since the tip is written at landing
  - WHY: R5 says a part that can't be known is left out, never invented
- [x] D2 (builder round 1, default): When the first agent run or edit comes before `opened`, it is clipped to `opened` and the split is kept. Going ahead unless told otherwise. → settled by the approver: The spec's Design and R16 say lead time starts at `new`, so time before `opened` is outside lead time by definition. Clipping the first mark to `opened` is pure arithmetic inside `metrics.lead_time()`. It keeps the parts summing to `lead`, as R4 requires, and `test_agents_before_opened_are_clipped_to_it` pins it. It doesn't change the trailer's shape.
  - OPTION: clip to `opened` — a hand-built change whose `/sdlc:intent` session ran `new` still gets its split, with `queued` at 0; but the minutes before `new` aren't counted anywhere
  - OPTION: treat it as out of order and keep `lead` alone — strict; but almost every hand-built change with transcripts would lose its split
  - WHY: the spec says lead time starts at `new`, so time before it is outside lead time by definition
- [x] D3 (builder round 1, default): When `opened` is after the close, there is no line and the coverage says `lead=bad-opened`. Going ahead unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: `lead=bad-opened` — reuses a word the spec already defines; but it lumps a clock fault in with a malformed value
  - OPTION: a new word such as `lead=clock` — more precise; but it's one more word for retro to know
  - WHY: R5 returns nothing in this case, and R11 has no word of its own for it
- [x] D4 (approver round 1, look): This extends the host-facing contract. It adds `opened:` to every new `intent.md`, adds an `Sdlc-Lead` trailer and new `lead=` coverage words to the metrics format, adds `process.lead` to retro's JSON, and adds `started`/`ended`/`since` keys to the factory's run rows. The edits sit in `scripts/closing.py`, which is `[review] sensitive`. The person should confirm the extension as documented in `docs/REFERENCE.md` *Metrics* and *Retrospectives*. → decided: seen
