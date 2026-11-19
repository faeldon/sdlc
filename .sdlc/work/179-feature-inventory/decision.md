DECISION: ESCALATE

**Why.** All three round-1 reviewers passed, and the gate is green on the current build: `./check.sh`, 3178 passed, 29 skipped, plugin validation passed. Every requirement from R1 to R14 has a test, and the reviewers found nothing Critical or High; four nits are recorded. The one thing blocking a landing is D1. The spec itself says the extra read of the factory's files (and the AGENTS.md edit that lists it) is the person's call, and nobody has answered it yet. The build already includes that read.

**Open items**
- None open. Four nits are recorded in `findings.md`: F1 (code: an AGENTS.md line past 100 columns), F2 (code: a missing comment at `retro.py:1768`), F3 (code: REFERENCE.md doesn't say what `retire.windows` counts), F4 (test: a test docstring cites "179 R1").

**Decisions to confirm**
- ESCALATED: D1: This changes the factory boundary in AGENTS.md: one more file `sdlc` reads from the factory, which is a policy edit. The spec says "The person decides it; it is not a side effect". The code reviewer also noted that approval is "not in the files I read". If the answer is no, R3 is dropped and the inventory covers core only. That means a rebuild without the factory listing, the regex test that pins it, and the AGENTS.md line.
- SETTLED: D2: R5 settles it: an item with no record is `unmeasured`, never `unused`. The supervisor session keeps the typed command but none of its calls (`metrics._supervised()`, plan.md Departures). Counting those commands as `inside` would turn them into false retire candidates, and a recorded use still makes an item `used`. The code review confirmed `_states` gives each item a `why`.
- SETTLED: D3: The existing rule and its test, `test_a_hosts_retrospective_never_mentions_the_cases`, already require a host's retro to say nothing about the skills' cases. In this repo, `cases` and `run-cases` are still listed. Nothing a host can do changes, and no test was loosened.

**Every other reason to escalate**
- None beyond D1.

**For the person at ship**
- First, the AGENTS.md factory paragraph: does the added sentence about reading skill folder names and `@command` names as text match what you'll accept for D1? It's also the line F1 flags as too long.
- Then `scripts/retro.py`'s `surface()`, `_states()` and `_retire()`. These hold the rule that unmeasured is never unused, and the walk back over earlier windows (F3).
- Then the new `Sdlc-Skill` trailer in `scripts/metrics.py`: it adds to the trailer contract and changes no existing line.
- Finally, check by eye that the Mermaid in `docs/FEATURES.md` and `docs/PROCESS.md` renders on the pushed branch. No reviewer opened those files' content.

- IMPACT: minor — `retro`'s JSON gains a `surface` block (use per skill, command and key, share used, footprint, retire candidates), `Close` commits gain an `Sdlc-Skill` line, and two new maps are in `docs/`. These are new capabilities; nothing existing is redefined.

**Undone items**
- None: there is no `notes.md` and no unticked item.

**How to recover**
- The prompt names no irreversible paths. If one is needed, plan.md's Rollback applies: `git revert` undoes the whole change. `Close` commits made while it was in place keep their `Sdlc-Skill` lines in history, and nothing reads them.
