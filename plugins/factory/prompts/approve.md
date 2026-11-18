# approve

> The factory fills this file and sends it to the agent word for word: `factory.py` picks each
> `## ` part a prompt needs, fills its `${name}` placeholders (`$$` is a literal `$`), and joins the
> parts. Each part is one line, never wrapped: its newlines are the prompt's. The title and this
> note are never sent.

## main

Decide.

## upgraded

This change was upgraded from Tier 1 to Tier 2 before round ${round}, on the person's answer to ${decision}: judge it against spec.md.

## stuck

Round ${round} kept again what round ${before} kept: ${stuck}; nothing a further round does will change it.

## untestable

The builder reports these requirements can't be tested: ${untestable}.

## next-step

Under `${reconsider}`, name the next step you'd take: a requirement to rewrite, a model to try, or an approach to change.

## exhausted

The rounds ran out with changes still kept: say whether the approach should be reconsidered.

## undone

For each unticked `- [ ]` item in notes.md, propose its disposition at landing: `- UNDONE: <the item's text, exactly> → seed: <a short title>` or `→ dropped: <why>`; an item starting `pre-existing:` may instead be filed as a bug, `→ bug: <severity>: <path>[, <path>…]: <title>`, its severity one of the words in the Bugs section of the repo's process doc (`[docs] process`, else the plugin's guide), never guessed: with no word that fits, carry it as a seed.

## irreversible

The diff touches irreversible paths ([review] irreversible on ${base}): ${touched}. A revert won't undo what they reach: for each, or each group, one `- RECOVER: <path or glob>: <the way back>` line, its command or `fix forward:` and what the follow-up would do.
