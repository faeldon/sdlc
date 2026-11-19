
Open questions resolved:

- **Is a change built by the factory but shipped by hand factory or hand?** The code already
  decides this. Close records `Sdlc-Mode: factory` whenever the branch's tip holds the change's
  `decision.md` (`closing.measure_change()`), however it was shipped. So it is factory. A change
  whose factory run never reached a decision is manual. The spec reads that record and never
  re-decides it (R1).
- **Should cost compare in dollars, with hand-built changes missing, or in tokens for both?**
  Answered from the code: `Sdlc-Totals` tokens include every factory agent's session, so tokens
  compare on both sides by the same measure. The spec does both. Tokens are the comparison, and
  dollars are given per way with the hand side counted missing as `built by hand` (R6). If you'd
  rather show tokens alone, drop R6's `usd` part. Nothing else depends on it.

Decided in the spec, for the person to confirm:

- **Nit 2026-11-19-15:** drop the `.sdlc/setup.json` skip rather than document it (R12). The skip
  only ever moved a setup-only change out of `process`. Keeping it would be one line of docs and a
  test instead.
- **What a milestone whose grouped seeds were all retired reads:** `dropped`. With at least one
  closed or shipped row and the rest retired, it reads `done` (R11). `status` keeps calling every
  such milestone done.
- **Where the comparison shows in the report:** one table at the end of *Window*, with no new
  template section (R8). S14's scorecard will move it.

Left open: none.
