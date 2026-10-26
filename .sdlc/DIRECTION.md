# Direction

> Rewritten by `/sdlc:retro` each time it runs; history keeps every earlier version. It says where
> the repo is headed, not what is being built: the changes are in `work/`, the seeds in
> `work/inbox.md`.
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

- G1 done: 020 gave the retrospective its evidence, and this one scores every outcome against it.
- G2 carried: the target and the gates now agree (007), but the median change still stops above
  it, Tier 1 at 7 against 5 and Tier 2 at 9.5 against 6.
- G3 carried: size, nits and the drift gate are honest now; rework still counts shared files, not
  fixes, and a ship that fixes its own finding reads as a miss.
- M1 done: 020 (v1.2.0) added `retro.evidence`, and its rows decide O2 and O3 below.
- M2 revised → M4: 007 and 014 shipped and the two numbers agree, but Tier 1 still runs 2 stops
  over, and permission prompts (median 2.5 a change) are most of the excess.
- M3 done: 021, 023, 012 and 008 all shipped in v1.2.0.

## Where we are

Twenty changes closed since 2026-10-24: eighteen in v1.2.0 and two in v1.3.0 (025, 026), tagged
today and not yet published. They built the inbox (seeds, bugs, nits) and the GitHub intake, and
made the loop's own numbers honest. Every change was measured. Twelve of the twenty were Tier 2,
only one of those went through every stage first time, and the median change stops its person
2 to 3.5 times above the target. The evidence shows no issue filed against the plugin in any
release. That is no channel, not no problems: hosts' reports have reached this repo by hand,
and 026's issue forms reach users only once v1.3.0 is published.

## Goals

- ~~G1. Each retrospective scores the product's outcomes from evidence, not from process counts alone (O4)~~ Done: 020, and this retrospective scores O1–O4 against its rows
- G2. A change stops its person as often as O3 says it should, with the target and the gates
  agreeing on what that is (O3)
- G3. The loop's own numbers can be trusted: rework, size and ship's findings say what happened
- G4. What a host reports reaches the register without the person carrying it, and the
  retrospective counts it (O1, O2)

## Milestones

### ~~M1. The retrospective has evidence~~ Done: 020, in v1.2.0

### ~~M2. The stop target and the gates agree~~ Revised → M4: they agree since 007; what's left is the prompts

### ~~M3. The loop's numbers are honest~~ Done: 008, 012, 021 and 023, in v1.2.0

### M4. Permission stops are named, and the avoidable ones gone

Close records what each permission stop asked for, every prompt a skill's rules should have covered
is covered, and the median Tier 1 change stops within its target.

Groups: 2026-10-26-4, 2026-10-26-5

### M5. Rework and first time say what happened

Retro's rework counts the earlier changes a later one says it fixes, not shared files, and ship's
first-time rate tells a review that caught something apart from a loop that circled.

Groups: 2026-10-25-12, 2026-10-26-6, 2026-10-27-1

### M6. Hosts report through issues

v1.3.0 is published, so hosts have the issue forms and `/sdlc:triage`. A session in a host on this
machine can hand a report to the plugin's session. The next retrospective's evidence counts reports
that arrived that way.

Groups: 026, 2026-10-25-9

## Next major release

None planned. The next release, 1.4.0, removes the shims in `.sdlc/deprecations.toml` (the
`work/ideas.md` fallback and bare-date headings) and ships as a minor on purpose, after the few
hosts have migrated. 027 would be major only if it moved an existing host's `work/` without a
key to keep it.

## Dropped findings

- Rework: 55 pairs, nearly all appends to a shared skill or test file. A duplicate of the seed
  2026-10-25-12, grouped under M5.
- `scripts/sdlc.py` grew from 4,928 to 7,047 lines and 16 of 20 changes touched it: proposed as an
  intent to split it, not a seed. The seed 2026-10-24-5 still measures it for any host.
- Findings caught at ship against those found later stay unmeasured: the bug register's
  `Introduced by:` line now carries them, and no bug has been filed yet.
- The person's response time (median 14 minutes for a Tier 2 change) almost matches the agent's
  (15.5): reading a spec or a review is the work the gates exist for, not a queue.
- Tokens pile up in build (median 8.9M cache reads for Tier 2): that is where the code is written,
  and there is nothing yet to compare it with.
- Seven of twenty changes serve no outcome, down from five of six: no longer growing.
- No bugs reported, fixed or escaped in the window: nothing to weigh against a tier.
