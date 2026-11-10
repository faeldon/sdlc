# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## What the new reading changes on 041–047

Rerun through the new `read_events` and `summarize` against this repo's transcripts: 041's stops
fall 15 → 9 (5 task notices, 1 `/reload-plugins`), 045's 8 → 5 (3 harness), 046's 12 → 11 (2
harness; one compaction summary quoted `<command-name>/sdlc:…` and so was already read as a
skill, which also opened a stage it shouldn't have). 042, 043 and 044 are unchanged. 047's own
"plan and build" after spec's yes is an `after_gate`, the stop this change's skill edits remove.

"Tool loaded." reaches a saved transcript only inside a `tool_result` entry (or the
`api-request-blob` copy of the request), which `_only_tool_results()` already skips: it was never
counted, so the old docstring caveat is gone.

## Left undone

- [x] The seed's first aim: cover the tool prompts a skill's rules should have, for hosts that
  run in `default` mode. No prompt has been recorded here (`prompt_modes=auto` everywhere), so it
  waits on a host's `Sdlc-Prompt` lines. → seed: 2026-11-10-2
