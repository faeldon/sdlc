
**Resolved**

- *Does the run keep its rounds and its round limit, or start the count again after the spec?* It
  starts again from the upgraded round `P`, as a restart does (R6). Earlier rounds were judged
  against the Tier 1 Approach, and keeping the count could send a change to the approver with no
  round reviewed against its spec. The cost shows again in Step 2's upgraded question.
- *Is the builder's plan so far kept as `plan.md`, or rewritten against the new spec?* An existing
  `plan.md` is never written over by `upgrade`. The resumed builder rewrites it against the
  approved spec as round `P`'s first act, keeping what still holds (R1, R8). A missing one is
  scaffolded, and `check` excuses the scaffold only while that build is live (R12).
- *Can a run go back down a tier, or is the change one-way?* One-way, and once (R5), matching the
  intent's "no second promotion". A downgrade is left out, as a possible idea of its own.
- *The name* (your revision): "promote" becomes "upgrade" throughout. That covers the command
  (`sdlc.py upgrade`, `factory.py upgrade`), the `verdicts` step, the record
  (`build/round-<P>.upgraded.md`, `UPGRADED: D<n>`), `start`'s `upgraded` and the answer's prefix
  (`upgrade to Tier 2`). The intent's title and the change's slug keep the word "promote", because
  the frontmatter and heading are left as scaffolded.
- *Scope* (your revision): the core command stays in `sdlc.py`, renamed, along with the widened
  `factory_first_build()` and the AGENTS.md map line.
- *The board* (your revision): as drafted. The step track shows `upgrade` and `spec` as pauses,
  and the card's tier turns to 2. There is no "upgraded at round P" line and no "approve its spec"
  need while the draft is in `runs/`.

**Left for the person**

- **Upgrading by hand:** `guide/process.md` still says "a Tier 1 that grows can be promoted by
  editing `tier:` and running `/sdlc:spec`", and `/sdlc:spec` still offers "to promote it".
  Pointing both at `sdlc.py upgrade`, and at the new word, would touch the guide (so
  `sdlc.py record` too). This spec leaves it for a follow-up seed unless you want it in this
  change.
