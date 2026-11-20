VERDICT: PASS

I checked R1–R14 against the diff and the gate record (`build/round-1.gate.md`: green). I found nothing Critical or Required. I ran no tests of my own.

## Notes

- DECISION: [default] (D1, already in `decisions.md`) The per-tier response reasons sit in a new `process.response` block, not in `time.tiers[t]` as R11 says.
  - OPTION: keep `process.response` — `time.tiers` keeps its shape, and the scorecard and Autonomy bundle read it fine.
  - OPTION: move it into `time.tiers[t]` — matches the spec's words, but changes an existing block's shape.
  - WHY: the builder's default works and no reader is hurt. The spec wording is the only thing that differs.
- NIT: skills/retro/SKILL.md:~441: the refusal sentence in Step 6 now runs far past 100 columns. Wrap it, since the diff made it longer. {style S low}
- NIT: .sdlc/work/189-retro-insights/notes.md: the lead-time-by-way rows still say `none in the window` when the window closed changes but none of that way. R11 named four blocks and not `process.lead`'s ways, so this is outside the spec. Ship will give it a disposition. {robustness S low}

Done well:

- Every refusal is collected before anything is written, and the draft is removed only after the commit.
- The draft is filtered out of `changed` and never committed.
- `retro --insights` empties the three host command lists, so no host command runs.
- `INSIGHT_FIELDS` and the disposition kinds are fixed in the script, not in a guide a host could reword.
- A `seed` with no id is refused, because the regex requires one.
- The Context pass: AGENTS.md's *Retrospectives* paragraph now says the draft is read, rendered and removed, and the commit still holds four kinds of file.
