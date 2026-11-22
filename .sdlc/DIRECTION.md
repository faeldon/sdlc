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

- G7 carried: the factory built all 34 of this window's changes, and the person approved every
  landing. It has still not run in a pilot project, so there is no evidence from a second repo.
- G8 carried: a landed change costs a median $2.36 at Tier 1 and $7.38 at Tier 2 (n=17 each), up
  from $2.03 and $7.30. The gate got slower again: 261.5 seconds a round against 158.5 (n=45), and
  the slowest 15% waited 648 seconds for a slot. Running two gates at once (`gate_jobs = 2`, set
  by hand in d039b1b) also filled the machine's swap during this window.
- G9 carried: escapes fell from 0.14 to 0.12 per change (4 in 34). 13 of the 34 changes
  escalated, and no landing approved itself: the person approved all 34.
- M13 carried: no change has run in the pilot project yet.
- M20 done: 198 and 199. 198 fixed bug 2026-11-20-27, which its `Close` commit records in
  `Sdlc-Fixes:`. `retro` reads that seed as vanished anyway, because it doesn't count a bug fixed
  by a change; 2026-11-22-41 covers that.
- M21 revised → M24: its four seeds shipped (200 and 201), but the gate round median rose from
  158.5 to 261.5 seconds instead of falling back near 90. The shared setup was not enough, and
  two gates now compete for the machine.
- M22 done: 202 and 203. The person kept 24 of 26 assumed defaults, and the approver ran on Sonnet
  for 28 of 34 changes with no rise in escapes. Whether the person overturned any of its calls is
  still unmeasured.
- M23 done: 204 shipped three of its seeds, and 2026-11-20-31 was retired.

## Where we are

Thirty-four changes closed in two days (198–233), all built by the factory and all measured. Two
releases went out: v1.11.0 and v1.12.0, a median of 0.2 days after each change landed. The plugin
moved from 1.10.0 to 1.11.0 underneath this window, and Claude Code moved on two changes, so read
every trend below as a hint.

- **Delivery:** the median factory lead time is 194 minutes (n=34), up from 166. Most of it is
  waiting: queued 34%, waiting at ready 26%, idle 21%, agents 12%. A median of 5 changes ran at
  once, and at most 8.
- **Stops and decisions:** questions rose from 0.6 to 1.09 per change: 26 defaults and 11 looks,
  no blocking ones. 6 builds stopped for nothing. The landing ran 34 acceptance steps across 16
  changes.
- **Review and escapes:** 4 escapes in 34 changes. One is tied to a change: 227's docs branch
  broke the ship case's grader (2026-11-22-40, low), and its review had no finding on those
  paths. 9 bugs in the register are tied to no change. 5 of the window's 12 important findings
  were doc text that disagreed with the code, and 227 added the docs reviewer to catch that.
- **Cost:** $190 in all. The builder took $122 of it. Waste (rework, mends, ejected runs) was
  7% of the dollars and 13% of the minutes.
- **Code:** both splits from the last window are growing back. `sdlc.py` went from 9,884 to
  11,322 lines and `factory.py` from 6,039 to 7,381, each touched by 16 of the last 30 changes.
  216 (autopilot) was reopened by five later changes, and two of its important findings were the
  same fault: a child process started without an explicit `env=`. Tests went from 48,537 to 57,128
  lines, and run in 48 minutes serially. The `test_train` tests take 28 to 35 seconds each, and
  10 test files have drifted from the code they load.
- **Nits:** 59 are open, and all five themes are past the process doc's threshold of 5: tests 24,
  docs 14, style 8, robustness 7, refactor 6.
- **Users:** one person runs the plugin, here. No host filed an issue against any release.

## Goals

- G7. The factory takes a change from intent to `main` with a supervisor agent deciding what it can
  and calling the person only for what needs them, with trust kept. Its first evidence comes from
  a pilot project, the plugin's first host besides this repo (O1, O3, O6)
- G8. A change costs little: its person's stops within O3's target, its host's context small, and
  its review quick (O3, O5)
- G9. Trust in the factory rests on evidence: a landing stops only for what needs its person, and
  its escapes and stops are read beside the hand-built changes' (O6)
- G10. Autopilot runs a bounded goal unattended, and what it lands is read beside the supervised
  factory's: its stops, escapes and cost (O3, O6)

## Milestones

### M13. The factory builds a change in the pilot project

A supervisor agent runs one change in the pilot project from an approved intent to ship's
question. It hands build, review and verification to the factory's agents and calls the person
only for a gate, a blocking decision or an ESCALATE. The change's `Close` numbers (stops, time and
any escape) sit beside this repo's manual medians.

Groups: 2026-11-17-5

Serves: G7

### M24. The gate stays quick with two at once

Gates split the machine's cores between them and wait out memory pressure, and the pruning pass
has looked at the slow and drifted tests. The gate's round median is back under 160 seconds, and
two gates at once no longer fill swap.

Groups: 2026-11-22-38, 2026-11-22-48

Serves: G8

### M25. Autopilot's first goal lands

One bounded autopilot run, with `gate_jobs = 1` and a low budget, takes a theme of nit paydowns
from seed to landing. Its `Close` numbers sit beside this window's supervised factory medians.

Groups: 2026-11-22-49, 2026-11-22-50, 2026-11-22-51

Serves: G10, O6

### M26. The factory's new code has its own module

The autopilot, park and readiness code that five changes kept reopening moves out of
`factory.py` into a module loaded by path, behind one helper that starts every child process with
an explicit env. Then `sdlc.py` is split the same way.

Groups: 2026-11-22-45, 2026-11-22-46

Serves: G9

### M27. The factory's questions and waits are explained

Each question and stop is read by the stage and reason it was asked, the spurious build stops
are traced to their causes, and the reason a READY change waits on its acceptance checks is known.

Groups: 2026-11-22-42, 2026-11-22-43

Serves: G9, O3

### ~~M20. A landing stages only what its change owns~~ Done: 198 and 199; 198 fixed 2026-11-20-27

### ~~M21. The gate stays quick as the suite grows~~ Revised → M24: its seeds shipped, but the round median rose to 261.5 seconds

### ~~M22. A default the person keeps never stops them~~ Done: 202 and 203; 24 of 26 defaults kept, the approver on Sonnet with no rise in escapes

### ~~M23. The scorecard reads true~~ Done: 204; 2026-11-20-31 retired

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

None planned. M26 moves code between modules without changing a command, and M24 changes how
gates share a machine, not what a host runs.

## Dropped findings

- **Rework questions:** 216 was reopened by 218, 220, 222, 228 and 231. Those were planned
  autopilot follow-ups, and M26 takes up the shape they point at. 213 rewrote 11 of 206's lines to
  make its setup nudge reach the person: an undeclared rework, which history can't amend now.
- **The commit outside the loop** (d039b1b, `gate_jobs = 2` set by hand): a tuning of the
  config, whose cost M24 takes up.
- **Records edited by hand** (8ec1322 and ef75cb3, both 2026-11-21): entries added before every
  seed went through `/sdlc:idea`. None since.
- **The one attributed escape** (227 → 2026-11-22-40, low): a skill's branch list moved without
  its case's grader. The bug covers it, and one case is too few to name a class for the review.
- **Loosening the review:** escapes fell from 0.14 to 0.12, but on 34 changes, with the plugin
  moving underneath. Not enough to lighten `[review] sensitive`.
- **The docs reviewer on every REFERENCE.md or factory README diff** (the Quality insight): 227
  landed the docs reviewer on the window's last day. The next window shows whether it catches
  this class as it is.
- **Spend outliers:** 203 (comment share 8.5×), 215 (7.1×) and 201 (out per line 7.8×) are small
  diffs or paydowns of many items. Their size explains them.
- **The three largest skills** (retro 9,883 tokens, ship 7,858, intent 5,889): each grew by
  judgment, not mechanism. They were not read again this time. The last retrospective found no
  deterministic step in them, and none of them changed shape since.
- **Unmeasured signals** (an approver's call the person overturned, among others): 2026-11-21-49
  already proposes measuring autopilot's overturn rate.
