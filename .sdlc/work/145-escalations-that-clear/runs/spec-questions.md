
I read the three seeds in `.sdlc/work/inbox.md` and made each a requirement:

- **R25** (seed 2026-11-18-49): while the factory's builder resolves a landing's conflict, the card says to wait for it, not to run `sdlc.py resolve` by hand.
- **R26** (seed 2026-11-18-50): an `accept` run after the landing's commit records its own step, `recheck`. The track gains a seventh position, `checks`, between gate and review.
- **R27** (seed 2026-11-18-47): `_no_verdict()`, `NO_DECISION`, the landing review's message and the board's copies now say a reply "holds no … the script reads". The tests that check those words change with them.

The new parts can be found under **Seeds folded in**, in the Design and Alternatives sections, and in the Verification test list.

**Resolved (unchanged from the first draft):**

- *How does the approver mark each reason's kind?* One line per reason, as `- ESCALATED:` is today. A default keeps `D<n>`; anything else is `gate:` or `look:` (R1, R2). An unknown word reads as `look`, so it still needs the person.
- *Which reasons can a green gate clear?* Only the ones the approver marks `gate`: a red gate, or a failing test or lint that `[commands] check` runs. A green check proves nothing about anything else, so those are `look` (R1).
- *Does an acknowledged item need words?* No: a plain `seen` is enough, and the person's words are kept when they type them (R12). Asking for words every time would turn a minute's look into a form. (Your call if you'd rather require them.)
- *Does a cleared change still count as escalated in `measure` and retro?* Yes, from the code: `_factory_files()` reads `decision.md`, which is never rewritten, so the trailer still says `ESCALATE` (R14).
- *Where do a landing step's durations come from?* A new record, `runs/land-times.jsonl`, written by `_record_land()` and amended into the change's commit. `runs/land-step.md` keeps only the current step, so history has nothing else to read (R19, R20).

**Left for you:**

- *Should `status` group its sections by the same five states?* This spec leaves `status` as it is: the intent's Outcome asks only that a cleared change leaves `■ What needs me`.
  - **Yes:** one vocabulary everywhere, but it reshapes `status`'s output for every host, and that is a change of its own.
  - **No:** the board and `status` keep different headings.
- *A hand change in Ready: review written **or** gate green (this spec, R16, today's Test rule), or **and** (the intent's wording)?*
  - **"And"** keeps a host with no `[commands] check` from ever reaching Ready, since the hand gate refuses to run there.
  - **"Or"** lets a change reach Ready on one of the two checks, but never while its gate is current and red.
- *The policy edit in Contracts touched:* the hand gate would accept a factory run at `stage: test`. It needs your yes with the spec.
- *The intent's Affected section doesn't name the three seeds.* Nothing marks them as taken in. The register only retires `[nit]` entries named in `## Requirements` when a change lands, and these are `[idea]` entries. You may want them retired when 145 lands, or recorded in the intent.
