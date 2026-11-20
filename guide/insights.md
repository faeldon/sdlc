# Insights

> The synthesis questions `/sdlc:retro` answers in its report's `## Insights`: one for each pillar
> of the scorecard, and one on the tradeoffs between them. Each is answered by the `sdlc:insight`
> agent from that pillar's figures alone, which `sdlc.py retro --insights` cuts. This guide is read
> in place. A repo's own questions (`[docs] insights`, `.sdlc/INSIGHTS.md`) are read after it, block
> by block: a pillar's `##` holding text replaces its question here, a `###` under a pillar's `##`
> adds a question on that pillar's figures, and any other `##` adds one on the tradeoffs' figures.
> Every answer takes the one shape the script reads, which no question doc can change.

## Value

Is the work mix the one we'd choose, and did the last retrospective's recommendations happen?

## Speed

Where does a change's time go, and what is the single biggest lever?

## Quality

What should be refactored, into what shape, and in what order? What keeps failing the same way?

## Autonomy

Which decisions could agents make reliably, and which stops added nothing?

## Cost

Where is spend wasted, and what would cost less without slowing anything?

## Simplicity

What could we remove or make quieter without anyone missing it?

## Tradeoffs

Which pillar is being bought with another?
