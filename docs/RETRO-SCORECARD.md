# Retrospective scorecard

> The framework `/sdlc:retro` reports against: five pillars, each with a headline metric, a few
> supporting ones and a guardrail, framed by a Value band above and a Trust band below. Every
> metric the plugin captures has a home here, either on the scorecard or as a diagnostic read
> when its pillar moves. Figures marked *baseline* are from the retrospective of 2026-11-18 and
> the analysis done the same day.

## Why a framework

A retrospective captures far more numbers than anyone can read each time. Without a frame, either
most of them go unread, or the report becomes a wall of tables. The framework keeps the first page
to one screen and still uses every number:

- **Five pillars,** one per thing that matters: shipping quickly, quality you can trust, autonomy
  that doesn't overburden the person, cost per change, and simplicity.
- **Each pillar has one headline and one guardrail.** The headline is the number that pillar is
  judged by. The guardrail is the number that shows the pillar being bought at another's expense.
- **Read in pairs.** A headline that improves while its guardrail worsens is a finding, not a win.
- **Diagnostics open only when a headline or guardrail moves.** They explain the move. They are
  not read every time.
- **Two bands frame the pillars.** *Value* (above) asks whether the work is aimed at the right
  things. *Trust* (below) asks whether the numbers can be believed.

The framework borrows from established ones: DORA (lead time, change failure rate, time to
restore, deployment frequency), the Flow Framework (work mix, flow efficiency), SPACE and DevEx
(the person's experience, feedback loops), Kanban (predictability) and unit economics (cost per
change). What's specific here is the autonomy pillar, which measures how much an agent-run
process asks of its person, and the simplicity pillar, which measures the plugin as a product a
host carries.

## How the scorecard reads

```
┌─ VALUE ── work mix · outcomes moved · time to users · last retro's follow-through ─┐
│                                                                                   │
│  PILLAR       HEADLINE                              GUARDRAIL                     │
│  Speed        lead time per change                  change failure rate           │
│  Quality      escape rate · structural debt index   lead time                     │
│  Autonomy     the person's minutes per change       escapes, factory vs by hand   │
│  Cost         $ and agent-minutes per landed change quality (escape rate)         │
│  Simplicity   surface used · context per run        lead time                     │
│                                                                                   │
└─ TRUST ── coverage per pillar · unmeasured signals · what changed underneath ─────┘
```

Each figure is shown against the last retrospective, with its trend (up, down, flat) and the `n`
it rests on. A figure resting on less than half the window's changes is shown greyed, as a hint,
never as a number to act on. After the scorecard come the **Insights** (one synthesis question per
pillar, and one on the tradeoffs), then one section per pillar with its diagnostics, then the
existing passes and dispositions.

Each metric below is described as: **what it is**, **why it matters**, **where it comes from**, and
**status** (*captured*, *partly*, or *needs* a seed, named in the last section).

## Value band: is the work aimed at the right things?

The pillars measure how work is done. This band measures what it is spent on.

### Work mix
- **What:** the share of landed changes that are new capability, defect fixes, debt and
  refactoring, or process work, per window.
- **Why:** a healthy mix is a choice; an unseen one just happens. A window spent mostly on the
  machinery itself, or mostly on fixes, is worth knowing about, whichever is intended.
- **Where:** each change's `impact:` (`minor` and above is capability), its seed's tag (`[bug]`,
  `[nit]`, `[idea]`), its `fixes:` and `reworks:` lines, and its theme.
- **Status:** captured: each change's `work` class and `work_mix`'s counts and shares, with the
  unclassed apart.

### Outcomes moved
- **What:** each product outcome (O1–O6) scored done, carried, revised or dropped, with the
  changes that served it and whether what their `Moves` lines said should change, did.
- **Why:** it ties the work to what users need, rather than to what was easy to build.
- **Where:** the product doc, each change's `serves:` and `Moves` lines, `retro.evidence`.
- **Status:** captured, by the product pass. The scorecard's Value band says so in one line: the
  product pass scores them in the direction doc, and the report holds nothing the skill wrote.

### Time to users
- **What:** median time from a change landing to the first release that holds it, and releases
  per window (DORA's deployment frequency).
- **Why:** a landed change helps nobody until it is released. Work that lands fast and waits weeks
  for a release isn't fast.
- **Where:** each change's `release` (the first tag holding it) and its `Close` commit's time.
- **Status:** captured: `time_to_users`'s median days and `releases`, the unreleased counted
  apart.

### Last retro's follow-through
- **What:** of the seeds, milestones and intents the last retrospective proposed, the share now
  done or dropped, against carried or vanished.
- **Why:** a retrospective whose recommendations don't happen is cost without value.
- **Where:** `direction.milestones`, the register, the last report.
- **Status:** not captured: intents, since nothing records the titles a retrospective proposes.
  Seeds and milestones are: `follow_through`'s verdicts and share.

## Pillar 1: Speed. Are we shipping new capability quickly?

### Headline: lead time per change
- **What:** the time from a change being opened (its `new`) to its `Close` commit landing on the
  base branch. Median and 85th percentile, by tier and by way of building.
- **Why:** it is what a person waiting for a change experiences. Today's cycle figure (`elapsed`)
  counts only the measured segments of each stage, so it hides time spent queued and time spent
  ready but not landed. *Baseline:* changes 139–148 showed 43.5 minutes of `elapsed` against a
  real median lead time of 250.
- **Where:** the `opened:` time `new` writes into the intent, and the `Close` commit.
- **Status:** captured: `Sdlc-Lead`'s `lead` on each `Close` commit, and `process.lead`'s median
  and 85th percentile by tier and way of building.

### Supporting: throughput
- **What:** changes landed per week, by way of building, and by impact.
- **Why:** lead time says how fast one change goes; throughput says how much lands. The factory
  trades the first for the second. *Baseline:* by hand 1–5 a day, 41 minutes median lead time;
  factory 32–36 a day, 93 minutes.
- **Where:** `Close` commits, `Sdlc-Mode`, `impact:`.
- **Status:** captured: each week of `process.throughput` by tier, by way of building (`ways`)
  and by work class (`classes`, the work-mix classes standing in for impact), and
  `by_way.throughput`'s changes per week for each way.

### Supporting: flow efficiency and ready-wait share
- **What:** flow efficiency is the time agents (or the person) were working on a change, divided by
  its lead time. Ready-wait share is the part of lead time a change spent finished and waiting to
  be decided or landed.
- **Why:** they say where a change's time goes, and so which lever is biggest. *Baseline:* 47% of
  factory lead time was ready-waiting; agents working was 23%.
- **Where:** agent sessions' start and end times, the approver's decision time, `land-times.jsonl`,
  the `Close` commit.
- **Status:** captured: `Sdlc-Lead`'s parts, and `process.lead`'s `shares` (`ready_wait`,
  `agents`).

### Supporting: predictability
- **What:** the 85th percentile lead time against the median, and how far the board's "typical"
  step estimates were from the actual times.
- **Why:** a process that is fast on average but sometimes very slow is hard to plan around.
- **Where:** lead times, the board's step medians.
- **Status:** not captured: the board's estimates against the actual times. The 85th percentile
  against the median is (`process.lead`).

### Guardrail: change failure rate
- **What:** the share of landed changes that needed a follow-up fix: a later change's `reworks:`
  line naming it, or a bug's `Introduced by:` line.
- **Why:** speed bought by shipping things that then need fixing isn't speed. This is DORA's
  stability measure.
- **Where:** `rework`, `bugs.escapes`.
- **Status:** captured.

### Diagnostics
- **Queue time:** from opening to the first agent or edit. Long queues are often deliberate
  batching; the number says how much.
- **Idle between agents:** gaps inside a build when no agent ran. Large gaps mean a run waited on
  the person or on the supervisor.
- **Stage times:** median time per stage (intent, design, build, test, ship, close).
- **WIP and capacity:** how many changes ran at once, and whether those running beside others took
  longer.
- **Feedback-loop time:** gate seconds and review-round time, the time between making a change and
  knowing whether it works (DevEx). Gate seconds and slot waits are captured:
  `pipeline.gates`, by window, with `pipeline.red_gate`; review-round time isn't.
- **Landing time:** the train's steps, from `land-times.jsonl`. Captured as the
  landing's events: `pipeline.landing`'s gates, ejections, bisections, base moves, accept stops
  and conflicts.

## Pillar 2: Quality. Can I trust what's built, including its structure?

Two halves: defects (does it work) and design health (will it keep being easy to change).

### Headline (defects): escape rate
- **What:** bugs found after landing, per closed change, with their severity.
- **Why:** it is the plainest answer to "can I trust what landed". *Baseline:* 2 of 86 (0.02), down
  from 3 of 27 (0.11).
- **Where:** `[bug]` entries with `Introduced by:`, `bugs.rate`.
- **Status:** captured.

### Headline (design): structural debt index
- **What:** the functions ranked by how many changes rewrote them in the window, times their size,
  and the trend of the top ones window over window.
- **Why:** a function that most changes have to touch, and that keeps growing, is where the next
  defect and the next merge conflict will come from. It turns "the code feels messy" into a list.
  *Baseline:* `factory.py`'s `main` (22 changes, 184 lines) and `_task_prompt` (17, 232), `sdlc.py`'s
  `main` (13, 476).
- **Where:** a host's `retro.indicators` command (function-level parsing is language-specific, so
  the core never does it), rendered in the report.
- **Status:** captured in this repo, by `retro.indicators`' function heat: each function's
  commits and lines as indicator rows, their trend the report's `Change`. A host gets it from its
  own command.

### Supporting: Important findings and recurring classes
- **What:** Important review findings per change, and the failure classes two or more changes
  share.
- **Why:** a class that recurs is one the review doc should name, so the review catches it before
  landing.
- **Where:** `findings.md`, `bugs.important`.
- **Status:** captured.

### Supporting: time to restore
- **What:** median days from a bug being filed to its fix landing.
- **Why:** DORA's recovery measure. Fast fixes limit what an escape costs.
- **Where:** `bugs.days_to_fix`.
- **Status:** captured.

### Supporting: risk exposure
- **What:** the share of changes reviewed at full depth, security findings, changes landed with
  paths no review read (`Sdlc-Landed … unreviewed=n`), and changes to irreversible paths.
- **Why:** autonomy raises the stakes of a missed review. This shows whether the riskiest code
  gets the deepest look.
- **Where:** the factory's `depth`, findings by pass, landing trailers, `[review]`.
- **Status:** not captured: changes to irreversible paths. The share at full depth
  (`pipeline.depth`, from each run's `DEPTH:` line), the landings with paths no review read
  (`pipeline.unreviewed`) and security findings (`bugs.review_sources.security`) are.

### Supporting: design health
- **What:** hotspot concentration (the share of changes touching the top three files), co-change
  pairs, the largest functions and files, files touched per change, and test-to-code growth.
- **Why:** they show the code concentrating where every change has to go, which is how a codebase
  slows down.
- **Where:** `architecture` (file level), indicators (function level).
- **Status:** captured: file level in `architecture`, function level in this repo by
  `retro.indicators`' function heat.

### Supporting: test health
- **What:** suite time, the slowest tests, tests whose code moved without them, and the skills'
  cases' scores.
- **Why:** a slow or stale suite is a quality tax on every change, and the cases are the only test
  of the skills themselves.
- **Where:** `tests.times` (`retro.test_times`), `tests.drifted`, the cases' history.
- **Status:** not captured: the cases' scores, which are kept per run and read by ship and
  release, not by `retro`. Suite times and drifted tests are in `retro`'s output.

### Supporting: comment health
- **What:** each script's comment density (comment and docstring lines over non-blank lines) and
  the files outside 0.10–0.40; docstring coverage of long (30+ lines) and hot functions; the share
  of comments that narrate the line they sit on; and comments' share of the scripts' bytes, with
  its estimate in tokens.
- **Why:** agent-written code narrates when unsure, and code with too few comments can't be
  audited; no one ratio is right, so the four together, and their trend, show which way it drifts.
  Comments are also a share of every file an agent reads.
- **Where:** this repo's `.sdlc/comment-health.py`, under `retro.indicators`, beside function heat.
- **Status:** captured, as indicator rows; their trend is the report's `Change`.
  **Guardrail:** Cost, its `comment est. tokens` row: trimming comments to cut what agents read
  must not cost the coverage rows.

### Guardrail: lead time
Quality bought with slowness shows up as lead time rising. See Speed.

### Diagnostics
- **Review noise:** the share of findings the person answered `wrong`. A noisy pass costs attention.
- **First-time rate per stage:** how often each stage passes without rework.
- **Red-gate rate:** builds the gate sent back.
- **Arbiter kept vs dropped:** how many of the reviewers' requested changes were real.
- **Nits by theme and age:** debt the reviews recorded but didn't fix.

## Pillar 3: Autonomy. Am I deciding only what needs me?

### Headline: the person's minutes per change
- **What:** the person's response time plus the number of stops per change, against the tier's
  target.
- **Why:** autonomy that still needs the person at every step isn't autonomy. This is the cost the
  person pays.
- **Where:** `metrics` (the `response` clock, `stops`, `target`).
- **Status:** captured.

### Supporting: decisions escalated, and the kept-default rate
- **What:** decisions escalated to the person per change, and the share where the person kept the
  agent's default.
- **Why:** a high kept-default rate means the agents could have decided those themselves, and the
  process is asking too much. A low one means the escalations were earned.
- **Where:** each change's `decisions.md` (`→ decided: the assumed default, confirmed` against an
  alternative), the approver's settled calls.
- **Status:** captured: `autonomy.escalations` per change, and `autonomy.kept_default`'s kept
  and changed defaults and their rate.

### Supporting: auto-landed share
- **What:** the share of landings whose WAIT approved itself (`Sdlc-Landed: by=auto`).
- **Why:** it shows how much of the work needs no landing decision at all.
- **Where:** landing trailers.
- **Status:** captured: `autonomy.auto_landed`'s landings by `auto`, `person` and `autopilot`,
  and its share.

### Supporting: spurious stops and looks
- **What:** stops that turned out to need nothing (a misread record, a false stop like
  2026-11-18-95), and looks per change.
- **Why:** every false stop teaches the person to stop reading stops.
- **Where:** `runs/stopped.md`, looks in `decisions.md`, `runs/mended`.
- **Status:** captured: `autonomy.spurious_stops`, at build and at landing, per change, and
  `autonomy.looks`.

### Supporting: the person's experience
- **What:** one question at each retrospective's approval, "how did this window feel: focused,
  interrupted, overloaded?", as a 1–5 rating and a line.
- **Why:** numbers can't see frustration or cognitive load (SPACE, DevEx). A window can score well
  and still be exhausting.
- **Where:** the retrospective itself, recorded in its report.
- **Status:** captured: the rating and line in the report's `## Experience`, against the last
  retrospective's.

### Guardrail: escape rate, factory against by hand
- **What:** escapes per change for factory-built changes against hand-built ones (O6).
- **Why:** autonomy must not cost trust. If the factory escapes more, less should be delegated.
- **Where:** `bugs.escapes` with each introducing change's `Sdlc-Mode`.
- **Status:** captured: each escape's `way`, and `bugs.rate.window.by_way` (copied to
  `by_way.escapes`), the window's rate for each way over its own changes.

### Diagnostics
- **Extra stops by kind:** `after_gate`, `asked`, `revise`, `unprompted`. A kind that recurs is a
  question a skill could ask in its WAIT.
- **Prompts:** tool permissions the person answered, and the mode they ran in.
- **Mends:** replies the script couldn't read and sent back.
- **Overturned calls:** approver settlements the person later changed.

## Pillar 4: Cost. What does a change cost, in money and in time?

### Headline: cost per landed change
- **What:** the API-equivalent dollars and the agent-minutes per change that landed, by tier.
- **Why:** it is the unit economics of the process. Dollars are what the agents cost; agent-minutes
  are what the machine's time costs. *Baseline:* a one-line config change cost $1.04; a large
  Tier 2 move, $8.94.
- **Where:** `runs/costs.jsonl` (each agent run's reported cost, tokens and duration).
- **Status:** captured: `retro`'s `cost.per_change`, dollars and agent-minutes per landed
  factory change by tier, each with its `n`; hand-built changes record tokens, not dollars, so
  they are counted missing, never $0. `by_way.cost` compares the ways in tokens, measured the same
  on both sides, with dollars beside them where recorded.

### Supporting: waste share
- **What:** the share of spend on work that didn't land or was redone: ejected changes, red gates,
  rework rounds, failed or rerun cases, mends, dropped changes.
- **Why:** the cheapest change is the one not built twice. Waste is where cost can fall without
  slowing anything.
- **Where:** `costs.jsonl`, tagged by what each run was for.
- **Status:** captured: `retro`'s `cost.waste`, its share and parts, with the runs recorded
  before purposes counted apart, never as waste.

### Supporting: spend by role and model
- **What:** dollars per change split by agent role (builder, each reviewer, approver) and model.
- **Why:** it shows where the money goes, and what a model choice costs. *Baseline:* the builder
  is most of every change's cost.
- **Where:** `costs.jsonl`.
- **Status:** captured: `retro`'s `cost.by_role` and `cost.by_model`.

### Supporting: cost per unit of output
- **What:** dollars, and agent output tokens, per 100 added code lines.
- **Why:** a secondary normaliser for comparing changes of different size. It is never a target:
  lines of code reward bloat.
- **Where:** `spend.out_per_line`, `costs.jsonl`.
- **Status:** not captured: dollars per line. Out tokens per added code line are
  (`spend.out_per_line`).

### Guardrail: quality
Cheap work that escapes isn't cheap. A falling cost with a rising escape rate is the finding.

### Diagnostics
- **Tool calls and errors:** calls per change, and the ones that keep failing (*baseline:*
  `sleep`, 18 of 19).
- **Tokens per stage and cache reads.**
- **Cost outliers:** changes over twice their tier's median.
- **Model and version drift:** a change of model or Claude Code version between windows can move
  every number at once.

## Pillar 5: Simplicity. Is the plugin small, used and out of the way?

### Headline: share of the surface used
- **What:** of all the skills, commands and config keys the plugin offers, the share used in the
  window.
- **Why:** a feature nobody uses still costs every host its context, its docs and its upkeep.
  Features unused for several windows are candidates to retire.
- **Where:** the `Sdlc-Skill` and `Sdlc-Tool` trailers (each skill and command per change), the
  host's config, against an inventory built from the code.
- **Status:** captured: `surface.share`, the unmeasured left out, and `surface.retire` for the
  never-used.

### Headline: context per run
- **What:** the median tokens a skill run reads (its `SKILL.md` and side files), per skill and in
  total.
- **Why:** every token a skill reads is paid by every host on every run (O5).
- **Where:** `prose` (estimated, bytes / 4), Close trailers (each change's tokens, not each
  skill's).
- **Status:** not captured: a measured figure per skill run. An estimate per skill is (`prose`).

### Supporting: footprint in a host
- **What:** the files setup writes into a host, the config keys it asks about, and the lines under
  `.sdlc/`.
- **Why:** what a host has to carry and understand before it gets any value.
- **Where:** `setup.json`, `defaults/`.
- **Status:** captured: `surface.footprint`.

### Supporting: the plugin's surface and its growth
- **What:** the count of skills, commands, config keys and doc lines, and their growth per release
  against the capability added.
- **Why:** surface that grows faster than capability is complexity accumulating.
- **Where:** the repo itself.
- **Status:** captured: `surface.growth`, in the plugin's own repo.

### Supporting: process overhead and workarounds
- **What:** time and stops spent on the process itself rather than the change, and workarounds:
  changes landed outside the loop, records fixed by hand, overrides.
- **Why:** an opinionated process earns its opinions only while it isn't in the way. A workaround
  is the process saying no to something the person needed.
- **Where:** stops, `extra`, and `simplicity.workarounds`: the commits on the base branch no
  change or command made (`outside`, and `hand_record` for a record), the register entries filed
  again after they left (`restored`), and the factory's ejections, stopped trains and fixes asked
  at landing (`overrides`, from each change's `runs/ejections.jsonl` and `build/land-<n>.ask.md`).
- **Status:** not captured: an edit to a change's own records on its branch. The rest is, read
  from history.

### Supporting: time to a host's first closed change
- **What:** whether a repo that has never seen the plugin gets from setup to its first closed
  change without editing anything the plugin wrote (O1).
- **Why:** it is the first experience of every host.
- **Where:** `tests/test_adoption.py`, hosts' reports.
- **Status:** captured, by the test.

### Guardrail: lead time
Simplifying must not remove what's used or slow a change down.

### Diagnostics
- **Never used for N windows:** each skill, command and key no one touched, with its retire
  candidacy.
- **Deprecations pending:** shims and retired keys still carried.
- **Hosts' reports:** issues filed per release, by area (empty until a host exists).

## Trust band: can the numbers be believed?

### Coverage per pillar
- **What:** for each headline, the changes it rests on out of the window's changes, and why the
  rest are missing.
- **Why:** a tidy number built on half the data is worse than an obviously incomplete one.
  *Baseline:* spend covered 41 of 86 changes.
- **Where:** each headline's `coverage` and `missing_because` (`process.lead`, `process.escapes`,
  `metrics`, `spend`), greyed in the report under half.
- **Status:** captured.

### Unmeasured signals
- **What:** what the process can't yet measure: findings caught later, tests a newer one repeats,
  tests that pass for the wrong reason.
- **Why:** naming the blind spots keeps them from being read as zero.
- **Where:** `unmeasured`.
- **Status:** captured.

### What changed underneath
- **What:** the Claude Code version, the models in use, and the plugin version, against the last
  window.
- **Why:** a change of model can move every pillar at once, and should be ruled out before reading
  any trend.
- **Where:** the `Sdlc-Runtime` trailer close writes, read as `process.underneath`.
- **Status:** captured.

## Insights: the synthesis questions

After the scorecard, the report answers a fixed set of questions. Each answer is a headline, the
evidence (every number taken from `sdlc.py retro`'s output, with its `n`), a recommendation, and a
disposition (a seed, an intent, or dropped with why). "Nothing to act on this window" is a valid
answer. The questions ship in a file the guide holds, and a host can add its own.

| Pillar | Question |
|---|---|
| Value | Is the work mix the one we'd choose, and did the last retrospective's recommendations happen? |
| Speed | Where does a change's time go, and what is the single biggest lever? |
| Quality | What should be refactored, into what shape, and in what order? What keeps failing the same way? |
| Autonomy | Which decisions could agents make reliably, and which stops added nothing? |
| Cost | Where is spend wasted, and what would cost less without slowing anything? |
| Simplicity | What could we remove or make quieter without anyone missing it? |
| Tradeoffs | Which pillar is being bought with another? |

Each question runs as a read-only sub-agent given only its pillar's data, in parallel, so each
context stays small and each answer is independent of the others.

## Hosts

The scorecard reaches hosts by way of the plugin, and each part goes where a host already finds
its kind:

- **The numbers** in `sdlc.py retro`, in core and language-neutral.
- **The page** in `templates/retro.md`, which a host overrides in `.sdlc/templates/`.
- **The synthesis questions** in a `guide/` file, which a host extends with its own.
- **The metrics' meanings** in `docs/REFERENCE.md`'s *Retrospectives*.

This doc stays this repo's design reference. Two figures read differently in a host:

- **Simplicity** means the process's own overhead and workarounds there. The plugin's own surface
  (skills used, footprint, growth) is this repo's measure alone.
- **The structural debt index** comes from the host's own `retro.indicators`, in its language.

**Lead time needs a start time in every host.** A host on local numbering has no issue, and
`intent.md`'s `created:` holds only a date, so `new` records `opened:`, to the minute, under
either numbering.

**What a host's scorecard leaves out.** The skills' cases are this repo's only, so nothing about
them is in a host's scorecard. A host with no factory gets the by-hand view: the mode comparison
and pipeline health say "no factory changes" rather than show zeros.
