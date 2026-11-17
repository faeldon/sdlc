# Product

> What this repo's product is for, and the outcomes it is after. Every change names the
> outcomes it serves on its intent's `serves:` line (or `none`), and `/sdlc:retro` scores each
> outcome against the evidence `retro.evidence` prints. The plugin reads only the outcome ids
> and their short names, which the skills show beside each id; the rest is yours.

## Users

People writing long notes in pieces: they save a draft, stop, and come back to it later.

## Problem

A draft saved today can be listed but not read back, so the writing done before a break is lost
to the writer even though it is on disk.

## Outcomes

- O1. **Drafts come back.** A writer returns to a saved draft and keeps writing where they stopped. Measured by: drafts reopened / drafts saved
- O2. **Tidy titles.** The list of drafts shows each title once, in the order they were saved. Measured by: duplicate titles reported

## Bets

Writers come back to a draft within a day, so reopening matters more than searching.
