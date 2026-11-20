# Direction

> Rewritten by `/sdlc:retro` each time it runs; history keeps every earlier version. It says where
> the repo is headed, not what is being built: the changes are in `.sdlc/work/`, the seeds in
> `.sdlc/work/inbox.md`.
>
> Every goal and milestone has an id that carries from one retrospective to the next, and ends
> done, dropped or revised, never silently gone: `sdlc.py retro-commit` refuses a doc that drops
> an open one. The forms, which `sdlc.py retro` reads:
>
> ```
> - G1. No one loses a draft
> - ~~G2. Drafts shared between accounts~~ Dropped: nobody has asked for it
>
> ### M1. Drafts reopen where they were left
>
> What's true when it's done.
>
> Groups: 006, 2026-10-01-2
>
> ### ~~M2. Drafts sync every hour~~ Revised → M3: on every save, not on a timer
>
> ### M3. Drafts sync on every save
>
> Groups: 009
> ```
>

## Since the last retrospective

- G7 carried: the factory built 43 of this window's 44 changes, and landed every one through a
  train after the person's yes. No pilot project has run it yet, so there is still no evidence from
  a second repo.
- G8 carried: factory changes stop a median 3 times against a target of 4, at both tiers (n=17 and
  26). A landed change costs a median $2.03 at Tier 1 and $7.30 at Tier 2. The gate takes twice as
  long as it did: 158.5 seconds a round, against 86.5.
- G9 carried: 185 ended the landing's stops for acceptance checks it had already approved (35 such
  stops in 17 changes before it). Escapes rose from 0.02 to 0.20 per change, and 7 of the 9 came
  from the factory's landing and reply-reading code.
- M13 carried: its one seed shipped as 070, so `retro` counts the milestone done. But no change has
  run in the pilot project yet, and that is what M13 says.
- M16 done: 153 moved close, the push, the lock and the landing into modules of their own, and
  `[review] sensitive` names them.
- M17 done: 155. Agents' test runs take a `gate_jobs` slot.
- M18 done: 156. A failed case says which step the skill took and which it skipped. No grader was
  answered `wrong` this window.
- M19 done: 191 and 173 paid down the two nit themes, 192 looked at the drifted tests again, and
  166 stopped agents calling commands the harness refuses.

## Where we are

Forty-four changes closed in three days (155–197), and all were measured. None has been released:
v1.10.0 is still the latest tag. The models changed underneath this window (this is the first
window with versions recorded), so read every trend below as a hint.

- **Delivery:** the median factory lead time is 166 minutes (n=33): 51 at Tier 1 and 173 at
  Tier 2. A quarter of it is queued and a fifth is waiting at ready. The median cycle is 34.5
  minutes at Tier 1 and 75.5 at Tier 2. The agent's share of the clock is 0.96.
- **Tiers and stops:** 18 at Tier 1, 26 at Tier 2. Factory changes stop at 3, one under target.
  Defaults the agents assumed were kept 18 of 18 times. Nine changes stopped for a fault in the
  process itself: 7 at build and 2 at landing. Bugs 186, 188, 196 and 197 fixed those faults.
- **Review and escapes:** 9 escapes in 44 changes (0.20), up from 2 in 86. Four of them are in
  `landing.py`'s git handling (097, 104, 139, 196), and one open bug, 2026-11-20-27, is the same
  class. Three of the nine have no review on record.
- **Bugs:** each one reported this window was fixed within a day. One is open.
- **Code:**
  - `scripts/retro.py` grew from 1,710 to 4,399 lines, and 13 of the last 30 changes touched it.
  - `factory.py` shrank from 7,910 to 6,039, and `sdlc.py` from 10,729 to 9,884: the splits are
    holding.
  - Tests went from 37,776 to 48,537 lines, and the serial suite takes 41 minutes. The slowest
    tests are `test_train`'s, at 25 to 40 seconds each.
- **Nits:** 37 are open. `tests` has 26, and `robustness` 5, both at the process doc's threshold.
- **Users:** one person runs the plugin, here. Hosts filed no issues.

## Goals

- G7. The factory takes a change from intent to `main` with a supervisor agent deciding what it can
  and calling the person only for what needs them, with trust kept. Its first evidence comes from
  a pilot project, the plugin's first host besides this repo (O1, O3, O6)
- G8. A change costs little: its person's stops within O3's target, its host's context small, and
  its review quick (O3, O5)
- G9. Trust in the factory rests on evidence: a landing stops only for what needs its person, and
  its escapes and stops are read beside the hand-built changes' (O6)

## Milestones

### M13. The factory builds a change in the pilot project

A supervisor agent runs one change in the pilot project from an approved intent to ship's
question. It hands build, review and verification to the factory's agents and calls the person
only for a gate, a blocking decision or an ESCALATE. The change's `Close` numbers (stops, time and
any escape) sit beside this repo's manual medians.

Groups: 2026-11-17-5

Serves: G7

### M20. A landing stages only what its change owns

`resolve --continue` and the landing's commits refuse any staged path outside the change's own,
its conflicted files and its records. The landing's records can't be written by an agent in the
change's folder, and the review knows the class of git-state bug that escaped four times this
window.

Groups: 2026-11-20-27, 2026-11-19-69, 2026-11-20-40

Serves: G9, O2

### M21. The gate stays quick as the suite grows

The slowest train tests share their setup, the drifted tests are looked at again, and the `tests`
and `robustness` nit themes are paid down. The gate's round median is back near 90 seconds.

Groups: 2026-11-20-41, 2026-11-20-42, 2026-11-20-43, 2026-11-20-18

Serves: G8

### M22. A default the person keeps never stops them

An escalation whose only reason is an assumed default goes to the landing's one question instead of
a separate decide, and the next window shows whether the approver can run on Sonnet without a
worse decision.

Groups: 2026-11-20-36, 2026-11-20-38

Serves: G9, O3

### M23. The scorecard reads true

Every scorecard row names its real reason when it is null. Workarounds give every block its `n`,
the surface measure stops reporting keys every change reads as unused, and the rating's dialog is
confirmed from a real transcript.

Groups: 2026-11-20-15, 2026-11-20-24, 2026-11-20-31, 2026-11-20-39

Serves: O4

### ~~M16. The deep review can name the risky code~~ Done: 153

### ~~M17. Agents' test runs share the machine with the gate~~ Done: 155

### ~~M18. The skills' cases tell what a skill did~~ Done: 156; no `wrong` grader answers this window

### ~~M19. The suite and the nits stay small~~ Done: 191, 173, 192 and 166

### ~~M10. A Tier 2 change stops within its target~~ Done: 069; factory Tier 2 at 4 stops (n=34), hand-built still 8 (n=9)

### ~~M11. The review knows the window's escapes~~ Done: 078; escapes 2 of 86

### ~~M12. Each rule is said once~~ Done: 090

### ~~M14. A review reads only the code it touches~~ Revised → M16: 068 shipped; the risky code is what the review must name next

### ~~M15. Every goal answers to an outcome~~ Done: 092

## Next major release

None planned. M20 tightens what a landing accepts but changes no command a host runs. M22 moves
one question, and the change that makes it decides whether that is minor.

## Dropped findings

- **Adding `factory.py` to `[review] sensitive`.** 4 of the 9 escapes touched it, but every factory
  change touches it, so every run would go to full depth. The models changed underneath, and the
  new review-doc class (2026-11-20-40) is cheaper. The next window will show whether it is enough.
- **Splitting `scripts/retro.py`** (1,710 → 4,399 lines, 13 of the last 30 changes, 12 of them
  together with `docs/REFERENCE.md`). No escape traces to it, and the scorecard work (waves 0–5)
  that grew it is done. The next retrospective weighs a split if it keeps growing.
- **Rework questions:** the large ones are planned follow-ups. 153's modules were what 155 and 156
  built on, and 160's registry was what later changes registered in. The 9 declared links are the
  window's rework.
- **Register entries restored** (3, in 63e1700): a landing dropped them before 181 made it hold
  entries for close to file. None was restored after 181.
- **Spend outliers:**
  - 166 (out per line 4.5×, tools per line 4.9×) and 173 (comment share 3.2×) were paydowns of
    many small items.
  - 192 and 194 are small diffs over many tests.

  Their size explains them.
- **The three largest skills** (retro 9,230 tokens, ship 7,714, intent 5,499): retro grew with the
  insights and the rating, which are judgment, not mechanism. No deterministic step was found.
- **The Tradeoffs insight:** only one row has a last value, so no trade can be read yet.
- **Unmeasured signals** (findings caught later, repeated tests, tests passing for the wrong
  reason, an approver's call the person overturned): not worth a seed until M22 shows whether the
  person overturns the approver's calls at all.
