# Decisions

- [x] D1 (builder round 1, default): Read the factory's skill folder names and `factory.py`'s `@command` names as text for the inventory (R3), and record this read in AGENTS.md's factory paragraph. Going ahead with it unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: read them — `surface` covers the factory too; one more crossing of the factory boundary, its regex pinned by a test
  - OPTION: core only — no policy edit; the inventory misses about a third of the skills and every factory command
  - WHY: the approved spec includes R3, but names the boundary edit as the person's call
- [x] D2 (builder round 1, default): Class `/sdlc-factory:build` and `land` as `supervised`: their runs are counted, and commands only they run are `unmeasured`. Going ahead with it unless told otherwise. → settled by the approver: R5 settles it: an item with no record is `unmeasured`, never `unused`. The supervisor session keeps the typed command but none of its calls (`metrics._supervised()`, plan.md Departures). Counting those commands as `inside` would turn them into false retire candidates, and a recorded use still makes an item `used`. The code review confirmed `_states` gives each item a `why`.
  - OPTION: supervised — honest; most `factory.py` commands stay unmeasured until the supervisor's calls are attributed to a change
  - OPTION: inside, as `SKILL_STAGE` implies — simpler; every supervisor-only command reads `unused` and becomes a false retire candidate
  - WHY: R5's rule that an item with no record is never `unused`
- [x] D3 (builder round 1, default): Leave the skills' cases commands (`cases`, `run-cases`) out of a host's surface. Going ahead with it unless told otherwise. → settled by the approver: The existing rule and its test, `test_a_hosts_retrospective_never_mentions_the_cases`, already require a host's retro to say nothing about the skills' cases. In this repo, `cases` and `run-cases` are still listed. Nothing a host can do changes, and no test was loosened.
  - OPTION: leave them out in a host — keeps the existing rule that a host's retro never mentions the cases
  - OPTION: list them everywhere — a complete inventory; breaks that rule and its test
  - WHY: `test_a_hosts_retrospective_never_mentions_the_cases`
