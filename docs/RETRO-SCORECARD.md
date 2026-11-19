# Retrospective scorecard

> The framework `/sdlc:retro` reports against: five pillars, each with a headline metric, a few
> supporting ones and a guardrail, framed by a Value band above and a Trust band below. Every
> metric the plugin captures has a home here, either on the scorecard or as a diagnostic read
> when its pillar moves. The last section lists the seeds that build it. Figures marked
> *baseline* are from the retrospective of 2026-11-18 and the analysis done the same day.

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
- **Status:** captured (S2, 168): each change's `work` class and `work_mix`'s counts and shares,
  with the unclassed apart.

### Outcomes moved
- **What:** each product outcome (O1–O6) scored done, carried, revised or dropped, with the
  changes that served it and whether what their `Moves` lines said should change, did.
- **Why:** it ties the work to what users need, rather than to what was easy to build.
- **Where:** the product doc, each change's `serves:` and `Moves` lines, `retro.evidence`.
- **Status:** captured (the product pass); moves onto the scorecard with S14.

### Time to users
- **What:** median time from a change landing to the first release that holds it, and releases
  per window (DORA's deployment frequency).
- **Why:** a landed change helps nobody until it is released. Work that lands fast and waits weeks
  for a release isn't fast.
- **Where:** each change's `release` (the first tag holding it) and its `Close` commit's time.
- **Status:** captured (S13, 168): `time_to_users`'s median days and `releases`, the unreleased
  counted apart.

### Last retro's follow-through
- **What:** of the seeds, milestones and intents the last retrospective proposed, the share now
  done or dropped, against carried or vanished.
- **Why:** a retrospective whose recommendations don't happen is cost without value.
- **Where:** `direction.milestones`, the register, the last report.
- **Status:** captured (S12, 168) for seeds and milestones: `follow_through`'s verdicts and
  share. Intents aren't: nothing records the titles a retrospective proposes.

## Pillar 1: Speed. Are we shipping new capability quickly?

### Headline: lead time per change
- **What:** the time from a change being opened (its `new`) to its `Close` commit landing on the
  base branch. Median and 85th percentile, by tier and by way of building.
- **Why:** it is what a person waiting for a change experiences. Today's cycle figure (`elapsed`)
  counts only the measured segments of each stage, so it hides time spent queued and time spent
  ready but not landed. *Baseline:* changes 139–148 showed 43.5 minutes of `elapsed` against a
  real median lead time of 250.
- **Where:** the `opened:` time `new` writes into the intent, and the `Close` commit.
- **Status:** captured (S1): `Sdlc-Lead`'s `lead` on each `Close` commit, and `process.lead`'s
  median and 85th percentile by tier and way of building.

### Supporting: throughput
- **What:** changes landed per week, by way of building, and by impact.
- **Why:** lead time says how fast one change goes; throughput says how much lands. The factory
  trades the first for the second. *Baseline:* by hand 1–5 a day, 41 minutes median lead time;
  factory 32–36 a day, 93 minutes.
- **Where:** `Close` commits, `Sdlc-Mode`, `impact:`.
- **Status:** partly: per week by tier is captured (`process.throughput`); by mode needs S9, and
  by impact S2.

### Supporting: flow efficiency and ready-wait share
- **What:** flow efficiency is the time agents (or the person) were working on a change, divided by
  its lead time. Ready-wait share is the part of lead time a change spent finished and waiting to
  be decided or landed.
- **Why:** they say where a change's time goes, and so which lever is biggest. *Baseline:* 47% of
  factory lead time was ready-waiting; agents working was 23%.
- **Where:** agent sessions' start and end times, the approver's decision time, `land-times.jsonl`,
  the `Close` commit.
- **Status:** captured (S1): `Sdlc-Lead`'s parts, and `process.lead`'s `shares`
  (`ready_wait`, `agents`).

### Supporting: predictability
- **What:** the 85th percentile lead time against the median, and how far the board's "typical"
  step estimates were from the actual times.
- **Why:** a process that is fast on average but sometimes very slow is hard to plan around.
- **Where:** lead times, the board's step medians.
- **Status:** partly: the 85th percentile against the median is captured (S1); the board's
  estimates against the actual times aren't.

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
  knowing whether it works (DevEx). Gate seconds and slot waits are captured (S10, 175):
  `pipeline.gates`, by window, with `pipeline.red_gate`; review-round time isn't.
- **Landing time:** the train's steps, from `land-times.jsonl`. Captured (S10, 175) as the
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
- **Status:** needs S7 and S8.

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
- **Status:** partly (S10, 175): the share at full depth (`pipeline.depth`, from each run's
  `DEPTH:` line) and the landings with paths no review read (`pipeline.unreviewed`) are captured;
  security findings and irreversible paths aren't.

### Supporting: design health
- **What:** hotspot concentration (the share of changes touching the top three files), co-change
  pairs, the largest functions and files, files touched per change, and test-to-code growth.
- **Why:** they show the code concentrating where every change has to go, which is how a codebase
  slows down.
- **Where:** `architecture` (file level), indicators (function level).
- **Status:** captured at file level; function level needs S7 and S8.

### Supporting: test health
- **What:** suite time, the slowest tests, tests whose code moved without them, and the skills'
  cases' scores.
- **Why:** a slow or stale suite is a quality tax on every change, and the cases are the only test
  of the skills themselves.
- **Where:** `tests.times` (`retro.test_times`), `tests.drifted`, the cases' history.
- **Status:** partly: suite times and drifted tests are in `retro`'s output; the cases' scores
  are kept per run and read by ship and release, not by `retro`.

### Supporting: comment health
- **What:** each script's comment density (comment and docstring lines over non-blank lines) and
  the files outside 0.10–0.40; docstring coverage of long (30+ lines) and hot functions; the share
  of comments that narrate the line they sit on; and comments' share of the scripts' bytes, with
  its estimate in tokens.
- **Why:** agent-written code narrates when unsure, and code with too few comments can't be
  audited; no one ratio is right, so the four together, and their trend, show which way it drifts.
  Comments are also a share of every file an agent reads.
- **Where:** this repo's `.sdlc/comment-health.py`, under `retro.indicators`, beside function heat.
- **Status:** captured (S17, 178), as indicator rows; their trend is the report's `Change`.
  **Guardrail:** Cost, its `comment est. tokens` row: trimming comments to cut what agents read
  must not cost the coverage rows.

### Guardrail: lead time
Quality bought with slowness shows up as lead time rising. See Speed.

### Diagnostics
- **Review noise:** the share of findings the person answered `wrong`. A noisy pass costs attention.
- **First-time rate per stage:** how often each stage passes without rework.
- **Red-gate rate:** builds the gate sent back.
- **Verifier kept vs dropped:** how many of the reviewers' requested changes were real.
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
- **Status:** needs S3.

### Supporting: auto-landed share
- **What:** the share of landings that passed their own gate (`Sdlc-Landed: by=auto`).
- **Why:** it shows how much of the work needs no landing decision at all.
- **Where:** landing trailers.
- **Status:** captured; needs counting in S3.

### Supporting: spurious stops and looks
- **What:** stops that turned out to need nothing (a misread record, a false stop like
  2026-11-18-95), and looks per change.
- **Why:** every false stop teaches the person to stop reading stops.
- **Where:** `runs/stopped.md`, looks in `decisions.md`, `runs/mended`.
- **Status:** partly. Needs S3.

### Supporting: the person's experience
- **What:** one question at each retrospective's approval, "how did this window feel: focused,
  interrupted, overloaded?", as a 1–5 rating and a line.
- **Why:** numbers can't see frustration or cognitive load (SPACE, DevEx). A window can score well
  and still be exhausting.
- **Where:** the retrospective itself, recorded in its report.
- **Status:** needs S16.

### Guardrail: escape rate, factory against by hand
- **What:** escapes per change for factory-built changes against hand-built ones (O6).
- **Why:** autonomy must not cost trust. If the factory escapes more, less should be delegated.
- **Where:** `bugs.escapes` with each introducing change's `Sdlc-Mode`.
- **Status:** needs S9.

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
- **Status:** captured (S4, 174): `retro`'s `cost.per_change`, dollars and agent-minutes per
  landed factory change by tier, each with its `n`; hand-built changes record tokens, not dollars,
  so they are counted missing, never $0.

### Supporting: waste share
- **What:** the share of spend on work that didn't land or was redone: ejected changes, red gates,
  rework rounds, failed or rerun cases, mends, dropped changes.
- **Why:** the cheapest change is the one not built twice. Waste is where cost can fall without
  slowing anything.
- **Where:** `costs.jsonl`, tagged by what each run was for.
- **Status:** captured (S4, 174): `retro`'s `cost.waste`, its share and parts, with the runs
  recorded before purposes counted apart, never as waste.

### Supporting: spend by role and model
- **What:** dollars per change split by agent role (builder, each reviewer, approver) and model.
- **Why:** it shows where the money goes, and what a model choice costs. *Baseline:* the builder
  is most of every change's cost.
- **Where:** `costs.jsonl`.
- **Status:** captured (S4, 174): `retro`'s `cost.by_role` and `cost.by_model`.

### Supporting: cost per unit of output
- **What:** dollars, and agent output tokens, per 100 added code lines.
- **Why:** a secondary normaliser for comparing changes of different size. It is never a target:
  lines of code reward bloat.
- **Where:** `spend.out_per_line`, `costs.jsonl`.
- **Status:** partly: out tokens per added code line is captured (`spend.out_per_line`); dollars
  per line need S4.

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
- **Status:** fed by S5: `surface.share`, the unmeasured left out, and `surface.retire` for the
  never-used.

### Headline: context per run
- **What:** the median tokens a skill run reads (its `SKILL.md` and side files), per skill and in
  total.
- **Why:** every token a skill reads is paid by every host on every run (O5).
- **Where:** `prose` (estimated, bytes / 4), Close trailers (each change's tokens, not each
  skill's).
- **Status:** captured as an estimate per skill (`prose`); no measured figure per skill run.

### Supporting: footprint in a host
- **What:** the files setup writes into a host, the config keys it asks about, and the lines under
  `.sdlc/`.
- **Why:** what a host has to carry and understand before it gets any value.
- **Where:** `setup.json`, `defaults/`.
- **Status:** fed by S5: `surface.footprint`.

### Supporting: the plugin's surface and its growth
- **What:** the count of skills, commands, config keys and doc lines, and their growth per release
  against the capability added.
- **Why:** surface that grows faster than capability is complexity accumulating.
- **Where:** the repo itself.
- **Status:** fed by S5: `surface.growth`, in the plugin's own repo.

### Supporting: process overhead and workarounds
- **What:** time and stops spent on the process itself rather than the change, and workarounds:
  changes landed outside the loop, records fixed by hand, overrides.
- **Why:** an opinionated process earns its opinions only while it isn't in the way. A workaround
  is the process saying no to something the person needed.
- **Where:** stops, `extra`, and `simplicity.workarounds`: the commits on the base branch no
  change or command made (`outside`, and `hand_record` for a record), the register entries filed
  again after they left (`restored`), and the factory's ejections, stopped trains and fixes asked
  at landing (`overrides`, from each change's `runs/ejections.jsonl` and `build/land-<n>.ask.md`).
- **Status:** captured by S6, read from history; an edit to a change's own records on its branch
  is still unmeasured.

### Supporting: time to a host's first closed change
- **What:** whether a repo that has never seen the plugin gets from setup to its first closed
  change without editing anything the plugin wrote (O1).
- **Why:** it is the first experience of every host.
- **Where:** `tests/test_adoption.py`, hosts' reports.
- **Status:** captured (the test).

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
- **Status:** captured (170).

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
- **Status:** captured (170).

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

The scorecard reaches hosts when S14 and S15 build it into the plugin, and each part goes where
a host already finds its kind:

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
either numbering (S1).

**What a host's scorecard leaves out.** The skills' cases are this repo's only, so nothing about
them is in a host's scorecard. A host with no factory gets the by-hand view: the mode comparison
and pipeline health say "no factory changes" rather than show zeros.

## Seeds to build it

The order matters: each phase reads data an earlier one adds. File each with `/sdlc:idea`, with
its `After:` line, or open it with `/sdlc:intent` where marked.

### Data (the numbers)

| Seed | What it adds | Pillar | After |
|---|---|---|---|
| **S1** | Close records lead time and the stage breakdown (queue, agents working, idle, ready-waiting, landing) as trailers; retro reports their medians and 85th percentiles beside `elapsed`. **Exists as 2026-11-18-94**: edit it to add the breakdown and percentiles. | Speed | – |
| **S2** | Work mix: each landed change classed capability, fix, debt or process from its `impact:`, seed tag, `fixes:`, `reworks:` and theme; retro reports the shares. | Value | – |
| **S3** | Decisions and stops counted: escalations per change, the kept-default rate, overturned approver calls, auto-landed share, spurious stops and looks. | Autonomy | – |
| **S4** | Waste tagged in `costs.jsonl` (each run marked by what it was for: build, rework, red-gate fix, ejected, rerun, mend); retro reports waste share and cost per landed change. | Cost | – |
| **S5** | Feature inventory: retro lists every skill, command and config key with its use in the window, the footprint setup leaves, and the surface's growth per release; unused for N windows becomes a retire candidate. Its list is the feature map, 2026-10-25-3. | Simplicity | – |
| **S6** | Workarounds tagged: a change landed outside the loop, a record fixed by hand, an override, each recorded so retro counts it. **Done: 180.** | Simplicity | – |
| **S7** | This repo's function-heat indicator, `.sdlc/function-heat.py`, set in `retro.indicators`. **Open as a Tier 1 intent by hand.** | Quality | – |
| **S8** | Indicators in a structured format (JSON rows), rendered as a table in the report; "no indicators set" said when empty; setup offers the key. | Quality | S7 |
| **S9** | Figures by way of building: lead time, throughput, cost and escape rate, factory against by hand. | Speed, Autonomy | S1 |
| **S10** | Pipeline and risk figures: gate seconds and slot-wait trend, red-gate rate, train figures (gates, ejections, bisections, base moves, accept stops, conflicts), mends, full-depth share, unreviewed landings. | Speed, Quality | S1 |
| **S11** | Trust band: each headline's coverage and why the rest is missing, greyed under half; the Claude Code version, models and plugin version against the last window. | Trust | – |
| **S12** | Follow-through: the share of the last retrospective's seeds, milestones and intents done or dropped against carried or vanished. | Value | – |
| **S13** | Time to users: median time from landing to release, and releases per window. | Value | – |
| **S17** | Comment health, an indicator beside function heat: comment density per file as a band and its trend, docstring coverage of long and hot functions, the share of comments that restate their line, and comments' share of what agents read. **Done: 178.** | Quality, Cost | S8 |

### Presentation (the report)

| Seed | What it adds | After |
|---|---|---|
| **S14** | The scorecard: the report opens with the Value band, the five pillars' headlines and guardrails against the last retrospective (trend and `n`), and the Trust band; each pillar's diagnostics follow in its own section. | S1–S13 |
| **S15** | The Insights section: the synthesis questions in a guide file a host can extend, each answered by a read-only sub-agent on its pillar's data, in the fixed answer shape. | S14 |
| **S16** | The person's experience: one rating and line asked at the retrospective's approval, recorded in its report. A change to a WAIT, so Tier 2. | S14 |

### Already filed that feed it

| Seed | What it is | Pillar |
|---|---|---|
| 2026-11-18-92 | Name the skill an after-gate stop follows | Autonomy |
| 2026-11-18-90 | A pruning pass over the tests that drifted | Quality |
| 2026-11-18-88, -89 | Pay down the tests and style nits | Quality |
| 2026-11-18-91 | Agents stop calling `sleep` | Cost |
| 2026-11-18-93 | The review doc names a doc's claim the change made false | Quality |
| 2026-11-18-95 | A builder's "UNTESTABLE: none." stops the run (bug) | Autonomy |

### The Quality pillar's first reading: refactors

The structural debt index, computed by hand on 2026-11-18, recommends these. Each is a mechanical
move in the style of the one that gave close and the landing their own modules.

| Seed | Refactor | Why | After |
|---|---|---|---|
| **R1** | A command registry for `sdlc.py` and `factory.py` | `main` is rewritten by 13 and 22 changes a window, and is where train conflicts land | – |
| **R2** | Agents' prompts out of `factory.py`, one file per task | `_task_prompt` (232 lines, 17 changes) and `_land_task` (138) | – |
| **R3** | A run-state module for the factory's loop | `cmd_agent`, `loop_state`, `cmd_verdicts` (16, 10, 10 changes) | R2 |
| **R4** | One shared reader in core for the factory's records | `factory_reading`, `needs_of`, `_factory_files`, `_hand_placeholders` | – |
| **R5** | Split `tests/test_factory.py` along the factory's modules | 5,712 lines, +4,773 in a window | – |
| **R6** | Split `cmd_close` into named steps inside `closing.py` | 365 lines in one function | – |

### Waves

The order the work follows, in waves: a wave starts once the one before it has landed, and its
changes can run side by side. Under each change are the register entries it takes in, by id. Its
intent names them, so landing it retires them; an entry's text and state stay in
`.sdlc/work/inbox.md`. Every entry open when this plan was written is named once, wave 6 holding
those the scorecard doesn't need. An entry filed later goes into the wave of the change that
touches its files.

#### Wave 0, done

- **R1**, the command registry: 160.
- **S7**, function heat: 161.

#### Wave 1, done

- **S1**, lead time and its stage breakdown: 162.
- **R4**, one reader in core for the factory's records: 163.
- **R2**, the agents' prompts in files: 164.

#### Wave 1½: two bug fixes

- Bug 2026-11-18-95, with idea 2026-11-18-91.
- Bug 2026-11-18-103, with idea 2026-11-18-66.

#### Wave 2

- **S2, S12 and S13**, as one change: 2026-11-18-64, 2026-11-18-65, 2026-11-18-97.
- **S3**: 2026-11-18-92, 2026-11-18-86, 2026-11-18-87.
- **S11**: 2026-11-18-107.
- **R3**: 2026-11-18-68, 2026-11-18-69, 2026-11-18-80, 2026-11-18-84, 2026-11-18-70,
  2026-11-18-71, 2026-11-18-85, 2026-11-18-98, and idea 2026-11-18-67.
- **R6**: 2026-11-19-1, 2026-11-19-2, 2026-11-19-3, 2026-11-19-4, 2026-11-18-100. The first two
  restate decisions D3 and D1 of 162, so R6 retires them as answered.
- **The style pay-down**, 2026-11-18-89, last in the wave: 2026-11-18-81, 2026-11-18-82,
  2026-11-18-75, 2026-11-18-77, 2026-11-18-78, 2026-11-18-83, 2026-11-18-96, 2026-11-19-5,
  2026-11-18-76, 2026-11-18-108.

#### Wave 3

- **S4**, done: 174.
- **S5**, with the feature map 2026-10-25-3 and the process map 2026-10-25-1.
- **S6**, done, with 2026-11-18-93: 180.
- **S8**.
- **S17**, done: 178.
- **S9**.
- **S10**, done: 175.

#### Wave 4

- **S14**, with 2026-11-18-105.

#### Wave 5

- **S15**.
- **S16**.
- **R5**, with the tests pay-down 2026-11-18-88 and the pruning pass 2026-11-18-90:
  2026-11-18-79, 2026-11-18-101, 2026-11-18-104, 2026-11-18-109, 2026-11-19-6, 2026-11-19-7,
  2026-11-19-8.

#### Wave 6: outside the scorecard

The backlog the scorecard doesn't need, in no order: 2026-10-25-23, 2026-10-27-10, 2026-10-26-11,
2026-10-26-13, 2026-10-26-10, 2026-11-10-2, 2026-11-18-74, 2026-11-13-1, 2026-11-18-99,
2026-10-24-6.
