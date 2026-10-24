# Product

> What this repo's product is for, and the outcomes it is after. Every change names the
> outcomes it serves on its intent's `serves:` line (or `none`), and `/sdlc:retro` scores each
> outcome against the evidence `retro.evidence` prints. The plugin reads only the outcome ids
> and their short names, which the skills show beside each id; the rest is yours.
>
> Outcomes keep their ids from one retrospective to the next, and end done, dropped or revised,
> never silently gone: `sdlc.py retro-commit` refuses a doc that drops an open one. The forms:
>
> ```
> - O1. **Unaided setup.** A new user finishes setup without help. Measured by: setups finished / started
> - ~~O2. Exports open in a spreadsheet~~ Done: 0 failed-export reports since 1.4.0
> - ~~O3. Teams share drafts~~ Revised → O4: they share links, not drafts
> ```
>
> Evidence commands, set in `.sdlc/config.toml` under `[retro] evidence`, print counts and
> summaries: never a person's name, address or message. What they print stays in the session
> that ran the retrospective.

## Users

<Who uses this, and what they're trying to get done when they reach for it. Name the kinds of
user that matter, not every one.>

## Problem

<What's hard for them today, before or without this product, in their terms rather than the
code's.>

## Outcomes

<Each outcome as `- O<n>. **<short name>.** <what is true for users when it's met>.
Measured by: <the number or signal that says so>`. The short name is two or three words a person
remembers. Three or four open at most: they are what every change is asked to serve.>

## Bets

<What you believe and haven't proven yet: the assumptions the outcomes rest on, so a
retrospective can say which evidence supports or breaks them.>
