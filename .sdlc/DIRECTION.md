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
> A struck item stays for one more retrospective, then may go.


## Since the last retrospective

- G3 done: rework now counts what a later change says it fixed (060: 3 links this window, each
  through a bug's `Introduced by:`), ship's first-time rate tells a recommended fix from a loop
  (049), and the process figures are committed as a report each retrospective (066).
- G4 revised → G7: one person runs the plugin, and they file what they find as seeds and bugs
  themselves (5 bugs this window, each fixed within two days), so no issue was going to arrive. The
  first host besides this repo will be the factory's pilot project, which G7 covers.
- G5 revised → G8: the median Tier 2 change still stops 8 times against O3's 6 (9 last time), and
  cost now covers the context a host pays and how long a review takes as well (O5).
- M4 done: 042 names each permission stop on the `Close` commit and 047 sorts the other stops by
  kind. 26 changes recorded prompts and none asked, though 21 of them ran in `auto` mode
  (2026-11-10-2 covers default-mode hosts). Its stops-within-target clause moves to M10.
- M5 done: 060 and 049 shipped. 2026-10-27-1 shipped as 029 and reads as vanished only because of
  the old `work/` path.
- M6 done: hosts have had the issue forms and `/sdlc:triage` since 026, and the evidence counts
  their reports per release. The local hand-off, 2026-10-25-9, was retired as superseded.
- M7 done: 043 redrew this repo's always-Tier-2 carve-outs, and the window shows it: 9 of 27
  changes came in at Tier 1, against 0 of 11.
- M8 revised → M13: both its seeds shipped by hand (057, 061), so no change has been built through
  the factory here. The factory's first run moves to a pilot project, under a supervisor agent.
- M9 revised → M14: its reads shipped (056, 058, 059). Moving retro out of `scripts/sdlc.py`
  (2026-11-04-10) carries into M14, where review time is the measure.

## Where we are

Twenty-seven changes closed since 2026-11-04 (041–067), released as v1.7.0 and v1.8.0. Every one of
them was measured.
- **Delivery:** median cycle is 46 minutes for a Tier 1 change (n=9) and 58.5 for a Tier 2 change
  (n=18). The agent's share of the clock is 0.18; most of the rest is time away.
- **Tiers and stops:** a third of the changes now come in at Tier 1. Stops are down a little but
  still over target, and the cause is now visible. Every change asked at least one question at
  intent beyond its gate (33 in all), mostly what the change serves and what it moves.
- **Bugs:** five bugs were reported and fixed, each within two days. Three of them escaped from
  changes in the window, all in how `scripts/metrics.py` reads transcripts, and the escape rate
  went from 0 of 14 to 3 of 27.
- **Code:** `scripts/sdlc.py` grew to 9,481 lines (+1,752), and 22 of the 27 changes touched it.
- **Users:** one person runs the plugin, here. The factory's pilot will be the first other repo.

## Goals

- G6. Ship's review catches the ways this repo's code has already failed, before a host meets them
  (O2)
- G7. The factory takes a change from intent to `main` with a supervisor agent deciding what it can
  and calling the person only for what needs them, with trust kept. Its first evidence comes from
  a pilot project, the plugin's first host besides this repo (O1, O3, O6)
- G8. A change costs little: its person's stops within O3's target, its host's context small, and
  its review quick (O3, O5)
- ~~G3. The loop's own numbers can be trusted: rework, size and ship's findings say what happened~~ Done: 049, 060, 066
- ~~G4. What a host reports reaches the register without the person carrying it, and the retrospective counts it (O1, O2)~~ Revised → G7: one person uses the plugin and files their own seeds; the pilot is the first other host
- ~~G5. A change costs its person what its tier says it should: the stops O3 sets, under a tier rule that fits the changes this repo makes (O3)~~ Revised → G8: cost covers context and review time too

## Milestones

### M10. A Tier 2 change stops within its target

Intent proposes what a change serves, and what it should move, in the draft its WAIT approves,
rather than asking first. The next window's median Tier 2 change stops 6 times or fewer.

Groups: 2026-11-17-1

### M11. The review knows the window's escapes

The review doc names the two classes behind the window's escapes and Important findings, and the
next window's escape rate is back below 3 of 27.

Groups: 2026-11-17-2

### M12. Each rule is said once

`AGENTS.md` keeps the boundaries and the rules that aren't obvious from the code. Each feature's
detail lives in one place, so a change that loosens a rule edits one sentence, not six.

Groups: 2026-11-17-3

### M13. The factory builds a change in the pilot project

A supervisor agent runs one change in the pilot project from an approved intent to ship's
question. It hands build, review and verification to the factory's agents and calls the person
only for a gate, a blocking decision or an ESCALATE. The change's `Close` numbers (stops, time and
any escape) sit beside this repo's manual medians.

Groups: 2026-11-17-5

### M14. A review reads only the code it touches

Retro's history readers live in their own file, the first boundary out of `scripts/sdlc.py`. The
next changes to retro are reviewed with fewer tokens read and less agent time in ship than this
window's medians: 9.6M cache reads and 9 agent minutes for a Tier 2 ship.

Groups: 2026-11-04-10

### M15. Every goal answers to an outcome

The retrospective checks its goals and milestones, and the changes that serve `none`, against the
product doc's outcomes, and proposes an outcome where recurring work has none.

Groups: 2026-11-17-4

### ~~M4. Permission stops are named, and the avoidable ones gone~~ Done: 042, 047; stops within target moves to M10

### ~~M5. Rework and first time say what happened~~ Done: 049, 060

### ~~M6. Hosts report through issues~~ Done: 026; the local hand-off was retired as superseded

### ~~M7. The tier rule fits this repo~~ Done: 043; 9 of 27 changes at Tier 1, against 0 of 11

### ~~M8. The factory has built a change here~~ Revised → M13: the first factory run is in a pilot project, under a supervisor

### ~~M9. A run reads what it needs~~ Revised → M14: the reads shipped (056, 058, 059); the module split carries on

## Next major release

None planned. Nothing open asks a host to change what it does: M10 changes intent's draft, not what
the person approves, and moving retro's code out of `scripts/sdlc.py` changes nothing a host sees.
The supervisor (M13) adds to `sdlc-factory` without changing the core loop.

## Dropped findings

- **Ship's and retro's skills:** they are the largest (about 7,550 and 6,700 tokens). 056 has only
  just moved ship's rare branches out, and no number yet shows more to cut. O5 will track it.
- **Changes run in parallel:** the 4 changes that ran beside two or more others took a median 173.5
  minutes, against 58.5 for the 16 that ran alone. Four changes are anecdote.
- **Time away:** it is 2,501 of the window's 3,670 clock minutes. That is the person's queue between
  sessions, not the loop's cost.
- **Rework questions** (38): the large ones are planned follow-ups, not missed fixes.
  - 049 extended 047's stop kinds;
  - 056 moved 053's ship text into branch files;
  - 061 paid down nits that 041's review raised;
  - 062 built on 044's ranking.

  The three declared links (050 fixing 015 and 047, 052 fixing 050) are all the window's rework.
- **The review's noise:** 1 finding was answered `wrong` out of the 27 answered changes' reviews.
  No pass is noisy.
- **Nits:** none are open.
- **Changes that serve no outcome:** 8 of 27 serve `none`, against 3 of 11. Most were cost and
  cleanup work, which O5 now gives an outcome, and M15 keeps checked.
- **Making `scripts/metrics.py` sensitive:** the escapes are all low severity, and a review class
  (2026-11-17-2) is narrower than a deep review on 11 of every 27 changes.
- **No issues from hosts:** one person uses the plugin and files their own seeds. This is not
  evidence about O1 or O2 until a second repo runs it (G7).
