# The insights

The report's `## Insights` answers the synthesis questions: one per pillar of the scorecard, from
the plugin's `guide/insights.md`, and any the repo adds in its own `[docs] insights` doc. Each is
answered by its own agent from that pillar's figures alone, so each context stays small and each
answer is independent of the others and of this session's passes.

## Cut the figures

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py retro --insights
```

It prints `questions`, each with its `title`, `pillar`, `question` and `data` (only that pillar's
figures, its scorecard rows, the window and what changed underneath), and `problems`, what is wrong
with the repo's question doc: say each one in Step 4. It writes nothing and runs no host command,
so no evidence, indicator or test-time output is in any `data`.

## Ask every question at once

Spawn `subagent_type: "sdlc:insight"` once per question, all of them in one message, so they run
in parallel. Give each only:

- its `title`, `pillar` and `question`;
- its `data`, as `retro --insights` printed it;
- the answer shape: the four lines `Headline:`, `Evidence:`, `Recommendation:` and
  `Disposition:` (`seed`, `intent: <title>`, `dropped: <reason>` or `none: <why>`).

Nothing of this session's reasoning goes in a prompt: not the passes' findings, not the other
questions or their answers, not what you expect it to say.

## Keep every answer

**Never drop one.** An agent that fails, returns nothing, or returns something not in the shape is
recorded as `Disposition: none: not answered, <why>`, with its Headline saying it wasn't answered,
so the question still appears in the report. Keep each answer's words as the agent gave them;
correct only a figure it misread from `data`, and say so in Step 4.

Then fold each Disposition into Step 3 as a finding of its own:

- **`seed`** becomes a seed in Step 4's `next-entry` count. When a pass's finding and an insight
  point at the same thing, they are one seed, and both name its id.
- **`intent: <title>`** joins the intent titles.
- **`dropped: <reason>`** goes under the direction doc's *Dropped findings*, as any dropped
  finding does.
- **`none: <why>`** stays in the answer alone.

In Step 6, once the seed ids are known, each `seed` is written as `seed <id>`.
