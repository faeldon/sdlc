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

- G2 revised → G5: the median Tier 2 change still stops 9 times against O3's 6, and with every
  change in the window at Tier 2, the tier rule now costs more than the extra stops; G5 holds both.
- G3 carried: more changes went through every stage first time (5 of 11 Tier 2 changes, against
  1 of 12), but rework still counts shared files, not fixes (M5).
- G4 carried: hosts have had the issue forms since v1.3.0 was published, and the evidence still
  counts no issue in any release; the local channel is unbuilt.
- M4 carried: neither seed is started, and a Tier 2 change still meets 3 permission prompts.
- M5 carried: 2026-10-27-1 shipped as 029 (it reads as vanished only because 029's intent sits at
  the old `work/` path); 2026-10-25-12 and 2026-10-26-6 are open.
- M6 carried: 026 shipped and every release since is published; 2026-10-25-9 is open and no report
  has arrived through an issue.

## Where we are

Fourteen changes closed since 2026-10-26 (027–040), released and published as v1.4.0, v1.5.0 and
v1.6.0. They finished the move to `.sdlc/`, put the process guide in the plugin with only a host's
answers in its repo, made ship's review honest and risk-scaled, and gave the factory a review loop,
evidence and an eval. Every change was measured, and every one whose intent could be read was
Tier 2: the median stops its person 9 times against a target of 6, though 5 of 11 now go through
every stage first time. No bug was filed and no issue arrived in any release, which says more about
the channel than about the code.

## Goals

- G3. The loop's own numbers can be trusted: rework, size and ship's findings say what happened
- G4. What a host reports reaches the register without the person carrying it, and the
  retrospective counts it (O1, O2)
- G5. A change costs its person what its tier says it should: the stops O3 sets, under a tier rule
  that fits the changes this repo makes (O3)
- ~~G2. A change stops its person as often as O3 says it should, with the target and the gates agreeing on what that is (O3)~~ Revised → G5: every change is Tier 2, so the tier rule is part of the cost

## Milestones

### M4. Permission stops are named, and the avoidable ones gone

Close records what each permission stop asked for, every prompt a skill's rules should have covered
is covered, and the median change stops within its target.

Groups: 2026-10-26-4, 2026-10-26-5

### M7. The tier rule fits this repo

This repo's always-Tier-2 carve-outs are re-drawn from what its changes actually risk, the product
doc's Tier 1 bet says what the next window should show, and that window shows it.

Groups: 2026-11-04-9

### M9. A run reads what it needs

Ship and setup read their rare branches only when the script says they apply, retro and release
print no per-change metrics by default, and the retro section of `scripts/sdlc.py` is its own file.

Groups: 2026-11-04-6, 2026-11-04-7, 2026-10-26-8, 2026-11-04-10

### M5. Rework and first time say what happened

Retro's rework counts the earlier changes a later one says it fixes, not shared files, and ship's
first-time rate tells a review that caught something apart from a loop that circled.

Groups: 2026-10-25-12, 2026-10-26-6, 2026-10-27-1

### M8. The factory has built a change here

One change, the robustness paydown, is built through `/sdlc-factory:build`, and its `Close`
commit's numbers sit beside the manual medians, so the factory's bet has evidence for or against it.
The tests paydown follows by hand.

Groups: 2026-10-26-7, 2026-11-04-8

### M6. Hosts report through issues

Hosts have the issue forms and `/sdlc:triage`. A session in a host on this machine can hand a
report to the plugin's session. The next retrospective's evidence counts reports that arrived that
way.

Groups: 026, 2026-10-25-9

## Next major release

None planned. 1.5.0 removed the last shim, and nothing in the inbox asks a host to change what it
does. Moving retro out of `scripts/sdlc.py` (2026-11-04-10) changes nothing a host sees.

## Dropped findings

- Rework: the pairs left after `rework_common` are again shared test and guide files. A duplicate
  of 2026-10-25-12, under M5.
- Ship went through first time in 6 of 11 Tier 2 changes. A duplicate of 2026-10-26-6, under M5.
- `retro` printed 112 KB and `release --check` 43 KB, most of it each change's metrics. A duplicate
  of 2026-10-26-8, under M9.
- The `robustness` nits stand at 10, past the threshold. A duplicate of 2026-10-26-7, whose list
  names five of them; its intent takes every open one. Under M8.
- A Tier 2 change meets 3 permission prompts. A duplicate of 2026-10-26-4 and 2026-10-26-5, under
  M4.
- 027, 028 and 029 read with no tier, impact or `serves:`: their commits hold their intents at the
  old `work/` path, which retro reads nowhere by design, and the next window won't include them.
- `tests/test_skills.py` (11 of 14 changes) and `.sdlc/setup.json` (6): every skill edit has to pass
  the first and every defaults edit re-records the second. Sharing them is the design.
- The fresh reviewer is counted on 5 deep diffs and raised nothing: whether it ran can't be told
  from a clean run. The nit 2026-11-03-15 covers it.
- No bug was reported, fixed or escaped, so the escape rate is flat at 0 of 14 against 0 of 20.
  With `[review] sensitive` set, that is no case for loosening either: no issue has arrived through
  any release (G4).
- Two Important findings (035 F1, 038 F1) share no class.
- The person's response (median 23 minutes for a Tier 2 change, 10 of them in ship) now exceeds
  the agent's 17: reading the review is the work the gate exists for.
- Tokens pile up in build (median 11.5M cache reads of a Tier 2 change's 27.7M): that is where the
  code is written.
- 3 of 11 readable changes serve no outcome, against 7 of 20: not growing.
