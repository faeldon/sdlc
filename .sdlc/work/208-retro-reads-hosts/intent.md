---
id: 208
slug: retro-reads-hosts
tier: 2
impact: minor
stage: shipped
created: 2026-11-21
opened: 2026-11-21T03:34Z
updated: 2026-11-21
shipped: 2026-11-21
idea:
depends_on:
serves: [O4]
origin: host
---

# 208 — The retrospective reads what the local host repos show

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The repos that use this plugin hold the best evidence of how it is used and where it falls short,
and no retrospective reads any of it. `/sdlc:retro` walks this repo's history alone, and
`.sdlc/evidence.py`, the one hook for this repo's own evidence, counts only its GitHub bug labels.

A read-only look on 2026-11-21 at the four hosts set up on this laptop found:

- **G7's pilot hasn't happened, and nothing measured it.** None of the 109 changes the hosts closed
  was built by the factory. `DIRECTION.md` says "no pilot project has run it yet" by assertion; M13
  counts done because its one seed shipped.
- **The busiest host's by-hand changes cost far more than this repo's:** 95 closed, a median of 15
  stops and 134 minutes each, against 8 stops and 45.5 minutes here, and 21 of 116 changes dropped
  (18%) against 1 of 211. That is evidence for O3 and `PRODUCT.md`'s first bet no retro has seen.
- **Hosts fall behind:** three of the four were set up at 1.4.0 or 1.5.0, against 1.11.0.

The hosts hold far more than those figures: per-stage and per-tier stops, time and tokens
(`Sdlc-Stage`, `Sdlc-Totals`); which skills and tools are used (`Sdlc-Calls`, `Sdlc-Tool`), which
would turn the retro's `surface` from `unmeasured` into used or unused in real hosts; why changes
are dropped; escapes (`Sdlc-Fixes`, `reworks:`); the config keys and templates a host changed; and
friction in sessions (refusals, permission prompts, errors) in the Claude Code transcripts. None of
it reaches the retro's figures, its `sdlc:insight` agents or its direction.

## Outcome

- A gitignored local list of host paths (e.g. `.sdlc/hosts.local`, as `.sdlc/terms.local` is). On
  a machine with no list, everything here reports `unmeasured`, never zero.
- Hosts are discovered, never read unlisted: the repos `claude plugin list --json` shows with sdlc
  installed at project scope (this repo and its worktrees left out) that the list doesn't name are
  reported by count, `1 installed repo not in your host list`, with how to add each, so a new
  project is noticed without being read until the person lists it.
- `/sdlc:retro`'s evidence includes host figures as counts only: hosts read; changes closed,
  dropped, by hand and by the factory; stops and time per tier and stage; escapes; version lag; and
  the further signals the spec chooses. Hosts are never named, and the figures stay apart from this
  repo's history-based trends.
- The spec catalogs which host signals to read, maps each to the outcome or retro pillar it informs,
  and sets a privacy rule per source: transcripts counts only, config key names only, a host's
  prose or content never.
- Each pillar's `sdlc:insight` agent gets the host figures beside this repo's, e.g. the stops
  pillar sees "by hand: 8 here, 15 in the busiest host".
- **Moves O4:** the retrospective's direction cites evidence from repos other than this one, so a
  goal like G7 is judged by measured host figures: "no pilot has run" or "a pilot ran" is shown,
  not asserted.
- A test reads two fixture host repos with known trailers and checks the counts, and that no host
  name or path appears in the output; one checks a machine with no list reports `unmeasured`.

## Affected

- **Area:** this repo's retrospective evidence, and the retro's insight inputs.
- **Files & components:** `.sdlc/evidence.py` (or a second script under `retro.evidence`);
  `.gitignore` for the host list; `scripts/retro.py` if insight agents get host figures by pillar;
  `skills/retro/SKILL.md`; `.sdlc/config.toml`'s `retro.evidence`; REFERENCE.md *Retrospectives*,
  `docs/CONTRIBUTING.md`, `docs/FEATURES.md`; tests.
- **Downstream:** this repo's committed retrospective reports and direction doc, which carry the
  figures; contributors, whose retro reads only their own machine's list; hosts, none, unless the
  spec makes the plugin's `retro.py` host-aware, when a host with a list could read its own hosts.
- **Contracts:** *Nothing about a project or a workspace* (no host name or path in any committed
  file or report); *Retrospectives* (read-only but for its report; `_evidence()` the only place a
  host's commands run); `unmeasured`, never `unused`; *Mechanism vs. policy*; the hosts' own
  confidentiality, some holding confidential data.

## Constraints

- Read-only against every host: it never writes, commits, fetches or runs a host's commands.
- Nothing that identifies a host leaves this machine: names, paths, titles, branch names, commit
  messages, prose. Transcripts are read for counts only.
- A missing list, or a host that can't be read, is `unmeasured`, never a failure of the retro.
- The report says how many hosts it read, since the figures depend on whose machine ran it.
- History-based figures stay reproducible from git; host figures are a section of their own.

## Open questions

- ~~Which signals are worth reading first, and which outcome or pillar does each inform?~~
  Resolved: the spec's signal table (Design), each from trailers and files the plugin writes
- ~~Can a host's transcripts be read safely at all, and which counts come from them (refusals,
  prompts, errors, skill invocations)?~~ Resolved: a change's sessions are already counted into its
  trailers at close; transcripts outside a change are not read, and stay `unmeasured` (spec R6)
- ~~Do host figures reach the `sdlc:insight` agents (a `retro.py` change), or stay in the evidence
  script alone?~~ Resolved: they reach the agents, so the reading is `retro.py`'s own; evidence
  output never reaches an agent or the report (spec R13)
- ~~Should host-aware reading be a plugin feature (`retro.hosts` or similar) any host could use for
  its own hosts, or stay this repo's?~~ Resolved: this repo's alone, gated on `_own_repo()`, no
  config key; approved with the spec (R1)
- ~~Are older hosts' thinner trailers read where they exist, or only from a version on?~~ Resolved:
  read where they exist, the rest `unmeasured` (spec R8)
- ~~How does a retro weigh one person's hosts, a biased sample, against this repo's own figures?~~
  Resolved: not weighed by the script; kept apart, with the host count and a sample note in the
  report and every bundle (spec R6, R11, R12, R15)
- ~~Does this make M13 measurable, so the retro judges it done by a host factory landing rather than
  its seed shipping?~~ Resolved: measurable from the factory-built count; the milestone rule itself
  is unchanged (spec R14)
- ~~Where is discovery said: only in the retro, or in `status` too? How does the person add a
  discovered repo (a printed line to append, or a command), and exclude one for good (a `!path`
  line in the list)? A discovered repo's path is shown only in the terminal, never in a report.~~
  Resolved: `retro` gives the count only; `sdlc.py hosts` prints paths and the lines to append;
  `!path` excludes; not in `status` (spec R9, R10)
