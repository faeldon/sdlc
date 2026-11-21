
- **Resolved: "An intent opened by `new` with no person's yes: what does its record say?"**
  `opened_by: autopilot` in frontmatter, written in place (R12), with the call in
  `runs/autopilot.md`. `origin:` stays its own key (`ORIGINS = ("host", "self")`, `sdlc.py:168`).
  Getting `vet` to accept the new key is part of this change.
- **Resolved: "The commands the harness asks before today (`accept`, `cases`)."** I resolved this
  in the design, but it's your call to confirm. `accept` runs only when every check passes
  `read_only_command()` (`landing.py:881`). Cases never run, and a change with cases in scope is
  held (R19, R21). The alternative is allowing both for the run: that loosens the harness prompts
  the intent keeps, and spends money outside the dollar cap's reach (cases have their own cap).
- **Resolved, for you to confirm: "A script-drawn line for breaks a contract."** Paths in
  `[autopilot] guards` (default: the policy doc, the review doc and `[review] irreversible`), plus
  `- CONTRACT:` / `- RELAX:` reply lines, plus an approver ESCALATE with *Reconsider the approach*
  or a `gate` reason (R19). Reading AGENTS.md's invariants or the invariant tests by name was
  rejected: the first needs a model to judge, and the second holds nearly every change, since most
  touch a tested file.
- **Left open: one change or a batch?** The spec is written in four parts (A–D) so it can split
  along them. One change lands it whole but makes a very large Tier 2: likely four or more build
  rounds and a long landing review, touching `landing.py` (sensitive) and core's metrics. As a
  batch, A (`by=autopilot`, the lock, `answer`) lands first and is useful on its own to the board
  seed (2026-11-21-34). B depends on A, and C and D depend on B. Each is smaller and reviewable,
  at the cost of three more landings.
- **Left open: push and sync, or local until you read the summary?** As designed, landings push as
  `git.push` says, the same as `/sdlc-factory:land`, with a pushed landing weighed double in
  change risk. Choosing local adds `--no-push` to `land --close` and `sdlc.py close` (narrowing
  only). That's safer while you're away, but the base branch drifts ahead of the remote until you
  push, and in a GitHub-numbered repo the opened issues stay open until then. No `sync` runs
  either way.
- **Left open: the weights and default limits.** As designed: debt `default` 1, `look` 2,
  `blocking` 3, `spec` 2, `intent` 1, limit 40; risk per R26, limit 30; `parallel` 3; `wait` 30
  minutes. These are guesses for you to set. How the retrospective checks them: as written, it
  reads the run's summary and the `by=autopilot` landings, then counts afterwards how many of
  autopilot's calls you overturned (a revert, or a seed citing the change) per unit of debt or
  risk spent. That figure isn't specified as a requirement here. Add it now, or file it as a seed
  once autopilot has run a few times.
- **Left open, needs your explicit yes: specs and intents built on without being seen.** Under
  autopilot, a Tier 2's spec is copied and built on with only the run's yes. That changes the
  factory README's *The approvals* promise, and AGENTS.md has to say so (*Contracts touched*,
  first entry).
