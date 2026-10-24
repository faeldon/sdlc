# Product

> What the sdlc plugin is for, and the outcomes it is after. Every change names the outcomes it
> serves on its intent's `serves:` line (or `none`), and `/sdlc:retro` scores each one. The plugin
> reads only the `- O<n>.` lines; the rest is for people.

## Users

People who run the plugin in their own repos with Claude Code: usually one person or a small team,
approving every stage themselves, often with several changes open at once. They didn't write the
plugin and won't read its code; they read the skills' questions and what lands in their repo.

## Problem

Claude Code will happily change a repo with no record of why, no design anyone approved, and no
review before it lands. A process that fixes that by adding paperwork gets abandoned. The plugin's
job is to make each change's why, design and review checkable, in the host's own repo, at a cost
the person running it keeps paying.

## Outcomes

- O1. **First closed change.** A repo that has never seen the plugin gets from `/sdlc:setup` to its
  first closed change without editing anything the plugin wrote. Measured by:
  `tests/test_adoption.py` passing, and issues filed against setup, `new` or close per release
- O2. **Nothing lost.** No host loses a change's work or gets one number twice. Measured by: issues
  reporting either, which stays at zero
- O3. **Few stops.** Each change stops its person at the gates its tier passes and at most one
  more (Tier 1 by hand: intent, ship and close, plus plan when plan mode ran; Tier 2: intent, spec,
  plan, ship and close). Measured by: the stops above that target close records per change, by
  tier and way of running
- O4. **Evidence-led direction.** A retrospective sets direction from evidence about the product,
  not only process counts. Measured by: the share of direction goals that cite an outcome and the
  evidence behind it

## Bets

- Prose skills behind narrow `allowed-tools` and one WAIT each hold up in repos the tests have
  never seen. The adoption test and issues from hosts are what would break this.
- People will keep the tiers honest: most changes are Tier 1. A tier mix drifting to Tier 2 says
  the overhead is too high, or the tier rule is wrong.
- The factory saves stops without costing trust: people approve its runs as readily as their own
  builds.
