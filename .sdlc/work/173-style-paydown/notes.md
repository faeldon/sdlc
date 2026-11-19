# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Left undone

- [x] The other factory agents (`approver.md`, `builder.md`, `resolver.md`, `reviewer-behaviour.md`, → seed: 2026-11-19-27
  `reviewer-security.md`, `reviewer-test.md`, `reviewer-ui.md`, `spec-writer.md`, `verifier.md`)
  keep prose lines past 100 columns; no entry named them, so they stayed out of this change.
- [x] `plugins/factory/README.md` keeps table rows past 100 (the agents table, the run-log table) → dropped: a markdown table row and a fenced block can't wrap, and rewording them only to fit a column limit isn't worth a change
  and fenced lines (the diagram, the folder listing): a markdown row can't wrap, so only rewording
  would shorten them.
- [x] `AGENTS.md` keeps a few short lines mid-paragraph outside the paragraphs the nits named → dropped: purely cosmetic, no line goes past 100, and the next edit to those paragraphs can refill them
  (*Retrospectives*' "so `retro` is", the skills invariant's "is literally").
