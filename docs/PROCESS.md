# Process

The plugin's three loops as maps, in `docs/FEATURES.md`'s terms: the **change loop** that takes one
change from a seed to the base branch, the **release loop** that takes landed changes to users,
and the **retro loop** that looks across both and sets what comes next. Each stage shows its
skill, the `sdlc.py` (or `factory.py`) commands the skill runs, what it checks, and what it writes.
A `WAIT:` node is the skill's one approval: nothing it writes is written before the person's
yes. `guide/process.md` says why each step is there; `tests/test_feature_map.py` fails when a
skill, a stage or a WAIT is missing from these maps.

## The change loop

A Tier 1 change skips design; a Tier 0 change has no folder and is committed directly. Either way
of building, by hand or by the factory, ends at the same ship and close. `/sdlc:status` and
`/sdlc:dashboard` read every open change at any point and write nothing.

```mermaid
flowchart TD
  update["/sdlc:update, when a session says a release is out<br/>calls: config, update<br/>runs: claude plugin update, per install"] --> wupdate["WAIT: /sdlc:update"]
  wupdate -->|restart Claude Code| setup
  setup["/sdlc:setup, once a repo<br/>calls: config, readiness, drift, update --installed, record, reset, vet<br/>writes: .sdlc/config.toml, the process and review docs"]
  setup --> wsetup["WAIT: /sdlc:setup"]
  uninstall["/sdlc:uninstall<br/>calls: config, uninstall<br/>removes what setup wrote"] --> wuninstall["WAIT: /sdlc:uninstall"]
  seeds["inbox.md: seeds"] --> intent
  intent["/sdlc:intent<br/>calls: config, status, next, lookup, groups, nits, new, sync"]
  intent --> wintent["WAIT: /sdlc:intent"]
  wintent --> plan["stage: plan<br/>writes: intent.md, the branch and its worktree"]
  plan -->|Tier 2| spec["/sdlc:spec<br/>calls: config, vet, lookup, nits, status, sync"]
  plan -->|Tier 2, factory| fspec["/sdlc-factory:spec<br/>calls: config, start, fresh, agent, write-spec, stage"]
  spec --> wspec["WAIT: /sdlc:spec"]
  fspec --> wfspec["WAIT: /sdlc-factory:spec"]
  wspec --> design["stage: design<br/>writes: spec.md"]
  wfspec --> design
  plan -->|Tier 1| build
  design --> build["stage: build<br/>plan mode writes plan.md, then the code, test first"]
  build -->|factory| fbuild["/sdlc-factory:build<br/>calls: config, start, fresh, agent, gate, verdicts, carry, decisions, stage<br/>builder, reviewers, arbiter and approver in rounds"]
  fbuild --> wfbuild["WAIT: /sdlc-factory:build"]
  build -.->|any stage| spike["stage: spike<br/>thrown away; back to the stage it left"]
  build --> test["stage: test<br/>the gate: the host's check; the hand gate: sdlc.py gate"]
  wfbuild --> test
  test -->|factory decisions| decide["/sdlc-factory:decide<br/>calls: config, ask<br/>writes: decisions.md"]
  decide --> wdecide["WAIT: /sdlc-factory:decide"]
  test --> ship["/sdlc:ship, stage: ship<br/>calls: config, preflight, vet, findings, base, resolve, ship, next-entry, sync<br/>checks: the gate, acceptance checks, review passes"]
  ship --> wship["WAIT: /sdlc:ship"]
  wship --> shipped["stage: shipped<br/>writes: findings.md, the change's commit"]
  test -->|factory batch| land["/sdlc-factory:land<br/>calls: config, train, land-check, accept, cases, sdlc-path<br/>ships and closes each change in a train, the gate at its tip"]
  land --> wland["WAIT: /sdlc-factory:land"]
  shipped --> close["/sdlc:close<br/>calls: config, close<br/>writes: the Close commit and its Sdlc trailers; mirrors to the tracker"]
  close --> wclose["WAIT: /sdlc:close"]
  wland --> landed["landed on the base branch"]
  intent -.->|away| autopilot["/sdlc-factory:autopilot<br/>calls: config, autopilot<br/>opens seeds, builds and lands them unattended, its calls its own"]
  autopilot --> wautopilot["WAIT: /sdlc-factory:autopilot"]
  wautopilot --> landed
  wclose --> landed
  plan -.->|won't ship| drop["/sdlc:drop<br/>calls: config, drop, close<br/>writes: stage: dropped, the Drop commit"]
  drop --> wdrop["WAIT: /sdlc:drop"]
  status["/sdlc:status and /sdlc:dashboard<br/>calls: status, vet, board<br/>read-only"]
```

## The release loop

`/sdlc:status` says a release is due from the changes closed since the last tag. The two WAITs
keep what can be undone (the tag) apart from what can't (the push).

```mermaid
flowchart TD
  landed["changes landed since the last tag, each with its impact"] --> release
  release["/sdlc:release<br/>calls: config, unreleased, release<br/>proposes the version from the highest impact"]
  release --> wrelease["WAIT: /sdlc:release"]
  wrelease --> tagged["writes: the version files, the changelog, a Release commit and its tag"]
  tagged --> publish["/sdlc:publish<br/>calls: config, publish"]
  publish --> wpublish["WAIT: /sdlc:publish"]
  wpublish --> users["pushes the base branch and the tag, never forced; runs the host's publish command"]
```

## The retro loop

What the change and release loops leave in history comes back as seeds. The retrospective is due
after two releases or one major; the skills that file seeds run whenever something is found.

```mermaid
flowchart TD
  history["history since the last Retrospective commit: Close and Drop commits, releases, trailers"] --> retro
  retro["/sdlc:retro<br/>calls: config, retro, next-entry, retro-commit<br/>five passes: cost, architecture, process, product, direction"]
  retro --> insights["retro --insights<br/>one sdlc:insight agent per synthesis question, all at once"]
  insights --> wretro["WAIT: /sdlc:retro"]
  wretro --> written["writes: the direction doc, the product doc's outcomes, seeds, the insights draft and the experience draft, the report with its Insights and Experience; one Retrospective commit, never the drafts"]
  health["/sdlc:health<br/>calls: config, vet<br/>tiers each finding"] --> idea
  idea["/sdlc:idea<br/>calls: config, status, next-entry, inbox-commit"] --> widea["WAIT: /sdlc:idea"]
  bug["/sdlc:bug<br/>calls: config, bugs, next-entry, inbox-commit"] --> wbug["WAIT: /sdlc:bug"]
  triage["/sdlc:triage<br/>calls: config, intake, bugs, next-entry, inbox-commit, mark-triaged, needs-info, sync"] --> wtriage["WAIT: /sdlc:triage"]
  feval["/sdlc-factory:eval<br/>calls: config, escapes, score, report-dir<br/>replays reviewers on escaped bugs"] --> wfeval["WAIT: /sdlc-factory:eval"]
  freview["/sdlc-factory:review<br/>calls: config, slice, report-dir<br/>reviews code no change touched"] --> wfreview["WAIT: /sdlc-factory:review"]
  written --> seeds["inbox.md: seeds"]
  widea --> seeds
  wbug --> seeds
  wtriage --> seeds
  wfreview --> seeds
  wfeval --> report["writes: a report under .sdlc/reports/"]
  seeds --> next["the next /sdlc:intent"]
```
