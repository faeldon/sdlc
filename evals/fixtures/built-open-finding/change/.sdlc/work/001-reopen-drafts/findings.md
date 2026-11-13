# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change.

## F1. [important] [correctness] Reopening returns another draft's text after a rename

`reopen()` reads `DRAFTS` by title, and nothing removes the old title when a draft is saved under a
new one, so reopening the old title returns stale text.

Evidence: drafts.py:12
Class: a lookup keyed by a value that can change; save() has the same shape.
Disposition: open
