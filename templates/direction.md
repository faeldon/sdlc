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
> Groups: 006, "Reopen drafts from the list"
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

<One line per goal and milestone the previous doc left open, by id: done (with the change or
release that did it), dropped or revised (with the reason, and for revised the new id), or carried
(with what's left). `sdlc.py retro`'s `direction.milestones` says what each grouped seed and change
became. "First retrospective" is an answer.>

## Where we are

<Two or three sentences on the state of the repo as of this retrospective: what the changes since
the last one added up to, what the releases shipped, and what the counts say about how the loops
are running.>

## Goals

<Each goal as `- G<n>. <what it's for>`, stated so a later retrospective can say whether it was
met; a closed one struck, `- ~~G<n>. …~~ Done: …`. Three open at most: a list of ten goals sets
no direction.>

## Milestones

<Each milestone as its own `### M<n>. Name` heading: what is true when it's done, then one
`Groups:` line naming the changes (NNN) and seeds ("their heading") it groups. In the order they
should land.>

## Next major release

<What the next release that changes what its users do would contain, and why it is major (see the
`impact:` table in the process doc). "None planned" is an answer.>

## Dropped findings

<Each finding this retrospective decided not to act on, with its reason: a finding dismissed
without one is one nobody can check later.>
