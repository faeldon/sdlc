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

- G6 done: 078 named the window's escape classes in the review doc, and escapes fell from 3 of 27
  changes (0.11) to 2 of 86 (0.02), each fixed within a day.
- G7 carried: the factory now takes changes from intent to `main`. It built 68 of this window's 86,
  and since 139 and 147 it lands them as a train after one yes. No pilot project has run it yet, so
  there is still no evidence from a second repo.
- G8 carried: factory changes stop a median 4 times against a target of 4 (n=68). A Tier 2 built
  by hand still stops 8 times against 6 (n=9). Review cost moves to M16, and the machine's load to
  M17.
- M10 done: 069 shipped, and most Tier 2 work now runs through the factory, at 4 stops. The 9 built
  by hand still sit at 8, which G8 keeps in view.
- M11 done: 078; escapes are back below 3 of 27.
- M12 done: 090.
- M13 carried: 070 shipped the supervisor. The factory has built 68 changes here, but none in the
  pilot project.
- M14 revised → M16: 068 moved retro's readers out of `scripts/sdlc.py`. Ship's review of a Tier 2
  built by hand still takes 10 agent minutes, against 9. The boundary that matters now is close,
  push, the lock and the landing, which 153 moves.
- M15 done: 092. This retrospective checks goals and `none` changes against the outcomes.

## Where we are

Eighty-six changes closed in two days (068–152 and 154), released as v1.9.0 and v1.10.0. All were
measured.

- **Delivery:** the median cycle is 46 minutes at Tier 1 and 76 at Tier 2 (n=43 each). The agent's
  share of the clock went from 0.18 to 0.84: factory runs leave little time away. 76 of the 86 ran
  beside three or more others, at a median of 67.5 minutes. Too few ran alone to compare.
- **Tiers and stops:** the tiers split evenly (43/43), up from a third at Tier 1. Factory changes
  stop at their target of 4. A Tier 2 built by hand stops 8 times against 6. Stops after a gate
  was answered recur: 15 in 11 changes.
- **Review:** 2 findings were answered `wrong` across 34 answered reviews. Both were a skills'-cases
  grader failing a skill that had done the right thing (100 and 150), which 156 takes on. Five
  changes' Important findings share one class: a doc's claim left false by the change.
- **Bugs:** 2 reported and 2 fixed, within 0 and 1 days. The escape rate is down from 0.11 to 0.02.
- **Code:** `plugins/factory/scripts/factory.py` grew from 1,149 to 7,910 lines, and 23 of the last
  30 changes touched it. `scripts/sdlc.py` is at 10,729 lines (+1,248). Tests went from 18,861 to
  38,166 lines.
- **Users:** one person runs the plugin, here. Hosts filed no issues in any release.

## Goals

- G7. The factory takes a change from intent to `main` with a supervisor agent deciding what it can
  and calling the person only for what needs them, with trust kept. Its first evidence comes from
  a pilot project, the plugin's first host besides this repo (O1, O3, O6)
- G8. A change costs little: its person's stops within O3's target, its host's context small, and
  its review quick (O3, O5)
- G9. Trust in the factory rests on evidence: a landing stops only for what needs its person, and
  its escapes and stops are read beside the hand-built changes' (O6)
- ~~G6. Ship's review catches the ways this repo's code has already failed, before a host meets them (O2)~~ Done: 078; escapes 3 of 27 → 2 of 86

## Milestones

### M13. The factory builds a change in the pilot project

A supervisor agent runs one change in the pilot project from an approved intent to ship's
question. It hands build, review and verification to the factory's agents and calls the person
only for a gate, a blocking decision or an ESCALATE. The change's `Close` numbers (stops, time and
any escape) sit beside this repo's manual medians.

Groups: 2026-11-17-5

Serves: G7

### M16. The deep review can name the risky code

Close, push, the main lock and the landing live in modules of their own, listed in `[review]
sensitive`. A change to them gets the deep review, and the rest of `scripts/sdlc.py` and
`factory.py` may still run light.

Groups: 153

Serves: G8, O2

### M17. Agents' test runs share the machine with the gate

A builder's or reviewer's `./check.sh` takes a `gate_jobs` slot as the gate does, so a batch built
at once never has two full suites competing for the cores.

Groups: 155

Serves: G8

### M18. The skills' cases tell what a skill did

A failed case says which step the skill took and which it skipped. It stops a landing only when
the person says so, and the `wrong` answers this window gave the grader don't recur.

Groups: 156

Serves: G9

### M19. The suite and the nits stay small

The two nit themes at the threshold are paid down, and the drifted tests are looked at again.
Agents stop calling commands the harness refuses.

Groups: 2026-11-18-88, 2026-11-18-89, 2026-11-18-90, 2026-11-18-91

Serves: G8

### ~~M10. A Tier 2 change stops within its target~~ Done: 069; factory Tier 2 at 4 stops (n=34), hand-built still 8 (n=9)

### ~~M11. The review knows the window's escapes~~ Done: 078; escapes 2 of 86

### ~~M12. Each rule is said once~~ Done: 090

### ~~M14. A review reads only the code it touches~~ Revised → M16: 068 shipped; the risky code is what the review must name next

### ~~M15. Every goal answers to an outcome~~ Done: 092

## Next major release

None planned. 153 moves code between modules without changing a command. 155 and 156 change how
the factory runs its agents and cases, not what a host does.

## Dropped findings

- **`factory.py`'s growth** (1,149 → 7,910 lines, 23 of the last 30 changes): its landing and train
  are the part 153 moves out. The rest waits until 153 shows what the split costs.
- **Rework questions** (375): the large ones are planned follow-ups, not missed fixes.
  - 139's train replaced 103's and 114's one-at-a-time landing.
  - 147's unattended loop built on 139's train.
  - 145 and 151 regrouped the board's columns.

  The 10 declared links are the window's rework: 080, 083, 085, 086, 089 and 091 follow 075 or
  080; 084, 087, 119 and 123 follow earlier changes.
- **Changes run in parallel:** 76 of the 86 ran beside three or more others, and only 2 ran alone.
  Two changes are anecdote.
- **The review's noise:** both `wrong` answers were the cases' grader, not a review pass. 156
  covers it.
- **`docs` as a recurring `none` theme** (090, 102, 116, 142): this is the repo's own upkeep of its
  rules and docs, for whoever maintains the plugin, and not an aim of a host's. The share of `none`
  changes fell from 8 of 27 to 15 of 86.
- **Tightening or loosening the review:** the rate is down, and 153 already reworks `[review]
  sensitive` on purpose.
- **Spend outliers** (083's out per line 8.6×, 082's comment share 11×): both are small code
  changes with large docs (14 and 50 code lines). Their size explains them.
- **The three largest skills** (ship 7,721 tokens, retro 7,636, intent 5,468): this rests on sizes
  alone. No mechanical step was found without reading them, so it is left to a pass that does.
- **Unmeasured signals** (findings caught later, repeated tests, tests passing for the wrong
  reason): not worth a seed until the pruning pass (2026-11-18-90) shows what per-test data
  would add.
