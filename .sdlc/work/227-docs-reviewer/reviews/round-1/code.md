VERDICT: CHANGES

- CHANGE: [context] skills/ship/docs.md:28: It says `sdlc.py ship` "refuses a diff this applies to whose note says neither" `Docs review:` line. `cmd_ship` now asks for that line only when `findings.md` exists (`line != "docs" or found["exists"]`, sdlc.py:4187). That is the builder's departure D1, and it is still open in `decisions.md`. Reword to "refuses, when the change has a `findings.md`, a diff this applies to whose note says neither". Check `skills/ship/SKILL.md`, the ship paragraph of `docs/REFERENCE.md` and `plugins/factory/README.md` for the same unconditional claim. D1 stays open for the person, and the doc must match whichever way it is answered.

## Notes
- NIT: plugins/factory/scripts/factory.py:1010: `docs_review` re-reads every listed doc's full text on each `_rounds_at_depth()` call, which `status` and `verdicts` may make many times. It is cheap now, but a docs-site `reviewed` list could make it slow. Cache per call, or short-circuit before the read loop when `changed` has a path outside `tests/` (clause e), since the read only decides which clause holds. {robustness S low}
- NIT: scripts/sdlc.py:~8010: `_docs_applies` and `docs_review` duplicate clauses (a)–(e), by the spec's no-import design. A test that runs both over the same fixtures would pin them in step, as the other copies are. {tests S med}
- Done well: the base-branch read of the docs list is the same on both sides. `docs` is kept out of `reviewers` and out of `beyond`, so a host's `["code"]` list keeps its docs check. The three `REVIEWERS` copies are updated together, and there is a test per join clause.
- I ran no tests; the gate record `build/round-1.gate.md` is PASS. I read the diff and the new agent and side files.
