
**Open questions resolved**

- *Does the core plugin get its own security, behaviour, ui and ux agents, or borrow the factory's?* Its own, for security, UI and UX: `sdlc:security`, `sdlc:ui` and `sdlc:ux`, read-only, in `findings.md`'s shape. The behaviour check is ship's own, with no agent. The factory's reviewers return `VERDICT:` and `CHANGE:` lines that `factory.py` files into rounds a hand-built change doesn't have, two of them carry Bash, and `test_sdlc_loads_nothing_from_plugins` keeps the core from leaning on `plugins/`.
- *Does running the spec's path at ship replace `checks.md`, or sit beside it?* Beside it. `checks.md` is rerun by `accept` on every later ship, with the tree judged by the script (`acceptance()`). The behaviour check is a one-time walk of the spec's path. The factory's `reviewer-behaviour` likewise reads `checks.md` and never runs it.
- *What counts as a "trust boundary" for the security pass?* `review.sensitive`, which the script already matches from the base branch. Risk must be matched by the script, never judged by a skill, and a second list would mean the same thing. The person may still want a separate key (below).

**Left for the person**

- **R24, the policy edit.** `AGENTS.md` would say the core has four agents, not one, and that `sdlc` also reads the base branch's `[ui]` and `.sdlc/reports/shots/`. Yes means the design as written. No means the UI and UX passes come out (R4, R6, the `ui.md` part of R7, R16, R20), and security and behaviour still land.
- **Who takes the screenshots for a hand-built change.**
  - The person runs `factory.py shots NNN --round 1 --role ui` (and `--role ux`) before ship. This is the recommendation: nothing in the factory changes, and the round label is a misnomer.
  - The factory gains a `--label ship` form for hand-built changes. This is a factory edit, and its tests change.
  - The core takes its own screenshots. Rejected above, but it is the only way without the factory installed.
- **How much paid review ship should add by default.** As written: on a deep diff, one more agent beside the fresh reviewer, and on a `[ui]` diff with current screenshots, two more. That is at most three extra agent calls, and none on a plain change. Two other choices:
  - an opt-out setting (`[review] passes = [...]`), which is cheaper for hosts that want it, but one more setting that setup asks about and `drift` tracks;
  - putting security into the existing fresh reviewer, which costs nothing extra but is a shallower security pass.
- **A separate trust-boundary key.** Only if the person wants a security pass on paths that shouldn't also force the deep build check and the fresh review.
