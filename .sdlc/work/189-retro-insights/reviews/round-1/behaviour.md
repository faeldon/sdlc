VERDICT: PASS

The end-to-end path matches the spec. `retro --insights` gives seven questions with only their own pillars' figures and no problems, and `retro --report` without a draft shows the Not-answered sentence. `config` reports `docs.insights` as specified. I did not run the host-extension, commit or draft-removal paths directly; they are covered only by the gate's record.

Decisions D1 and D2 in `decisions.md` are the builder's own defaults and are still unanswered. D1 is the response reasons kept in `process.response` rather than `time.tiers[t]`. D2 is the lead-time-by-way rows left at `none in the window`. Neither fails a spec requirement I ran, so I raise no change on them.

## Notes
- `checks.md` does not exist for this change, so there are no acceptance checks to read.
- The gate record `build/round-1.gate.md` says `GATE: PASS`, exit 0.
- I did not run the tests, per the rules.
- Speed's `data` holds the `process` figures (`cycle`, `lead`, `throughput`, `time`, `wip`, `capacity`) plus `by_way`, `pipeline` and `scorecard`, and no `cost`. This matches R3.
- The seven questions come out in the spec's pillar order.

## Evidence
$ uv run --quiet --script scripts/sdlc.py retro --insights > /tmp/ins189.json
exit: 0

$ python3 -c "...print problems and each question's pillar and data keys..."
problems `[]`; the seven titles (Value, Speed, Quality, Autonomy, Cost, Simplicity, Tradeoffs) each carry only their pillar's keys, for example Speed: `['by_way', 'pipeline', 'process', 'scorecard']`
exit: 0

$ uv run --quiet --script scripts/sdlc.py retro --report | grep -n -A3 '## Insights'
55:## Insights
57:Not answered: this report was written without the retrospective's insights.
exit: 0

$ uv run --quiet --script scripts/sdlc.py config | grep -n -A6 '"insights"'
93: "insights": { "path": ".sdlc/INSIGHTS.md", "exists": false, "source": "host", "layout": "answers", "guide": ".../guide/insights.md" }
exit: 0

$ python3 -c "...print Speed's process keys..."
['window', 'underneath', 'cycle', 'lead', 'throughput', 'time', 'wip', 'capacity']
exit: 0

$ git status --short | head -3
 M .sdlc/setup.json / M AGENTS.md / M docs/FEATURES.md (the same list as before my runs, so nothing was written)
exit: 0

$ cat .sdlc/work/189-retro-insights/build/round-1.gate.md
GATE: PASS … Exit: 0 … Tree: unchanged
exit: 0
