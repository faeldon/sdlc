---
id: NNN
slug: SLUG
kind: spec
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# NNN — TITLE · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

<Numbered, each one checkable. "R3. Saving a draft twice keeps one draft, and the test asserting it
fails if a second row appears" — not "should work correctly". These become the review's checklist
and the test names.>

1.
2.

## Design

<How it works. The pieces and how they connect, the data each one owns, what happens on the edge
cases the requirements name. Name the existing code you're reusing rather than re-deriving it.>

## Contracts touched

<For each invariant in the repo's policy doc this comes near: what it says, and how this design
stays inside it. If it needs to *change* one, say so here loudly — that's a policy edit and its own
decision, not a side effect.>

## Alternatives rejected

<Say what you didn't do and why. This is the section that pays for itself six months later, when
someone proposes the thing you already thought through.>

## Verification

<The commands to run and what healthy output looks like. This is what Stage 4 executes and what
plan.md's Tests section implements.>
