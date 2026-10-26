---
id: 026
slug: github-intake
tier: 2
impact: minor
stage: shipped
created: 2026-10-26
updated: 2026-10-26
shipped: 2026-10-26
idea: 2026-10-25-11
depends_on:
serves: [O2]
---

# 026 — GitHub issues as the intake for bugs and requests

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The inbox (`work/inbox.md`, 024 and 025) is the one register of change requests, but only a
session in the repo's own checkout can write to it. Where `archive.target` is GitHub, anyone who
isn't running a session (a host's own users, or someone reporting a problem with the plugin
itself) has no channel into it: they open a GitHub issue, and nothing reads it. The plugin looks
only at issues labelled `sdlc`, the ones it opened for its own changes, so every other issue sits
outside the pipeline: `status` never surfaces it, retro never counts it, and a bug filed there can
be fixed with no `Sdlc-Fixes:` trailer recording it. A host has it worse: setup gives its users no
issue template, so a report arrives without the facts a `[bug]` entry needs (`Severity:`,
`Paths:`, a repro).

## Outcome

- `/sdlc:triage` lists the open issues no change claims (no `sdlc` archive label, not yet
  triaged) and, after its one WAIT, files each as an `[idea]` or `[bug]` inbox entry, or adds it
  to the `closes:` line of the open change that takes it on.
- A triaged issue is labelled `triaged` and left open, with a comment naming the inbox entry's id
  or the change; a later triage run skips it.
- When a change takes on a triaged entry, the issue closes through that change's `Close` commit,
  the way `Closes #N` closes the change's own issue.
- `/sdlc:setup`, in a host whose target is GitHub, offers issue templates (bug and request) whose
  fields map onto the entry's `BODY_KEYS`.
- This repo runs `/sdlc:triage` on its own issues as the first user.
- **Moves O2:** a request or bug filed on GitHub, in a host or in this repo, reaches the register
  and is accounted for at close, where today it is lost unless someone reads the issue list.

## Affected

- **Area:** the GitHub tracker, the inbox, setup, and a new skill.
- **Files & components:** `scripts/trackers/github.py` (listing unclaimed issues, labelling and
  commenting), `scripts/sdlc.py` (a triage subcommand rendering entries, the tracker interface,
  ids from `next_entry_ids()`, `Closes` lines on the `Close` commit), a new
  `skills/triage/SKILL.md`, `skills/setup/SKILL.md` and a template under `defaults/` or
  `templates/`, `docs/REFERENCE.md`, `README.md`, tests.
- **Downstream:** every host with `archive.target = "github"`: its issue list gets a new label, its
  repo may get `.github/ISSUE_TEMPLATE/` files, and the `status` Next up list and retro's bug
  counts read the entries triage writes.
- **Contracts:** core never calls `gh` and a tracker never reads `work/` (the split runs along that
  line); `bug-commit` is the only code that commits the inbox, from the main checkout alone; inbox
  ids come from `next_entry_ids()`, never a change number; only publish pushes; setup's record and
  drift cover any new default it copies (`sdlc.py record`); the tests' `WAIT`, `allowed-tools` and
  `READS_CONFIG` invariants for the new skill.

## Constraints

- An issue the plugin opened for a change (labelled `sdlc`) is never triaged.
- Triage closes an issue only on a verdict the person approved that says nothing more will be done
  (already resolved, wontfix, not a bug, duplicate); anything filed or taken on closes at close, so
  the issue stays open until the fix lands.
- No inbox entry is written twice for one issue, across reruns and across worktrees.
- An entry never matches an issue by title alone: the link is the issue's number or URL.
- With no tracker, or a target other than GitHub, triage says there is nothing to read and writes
  nothing.

## Open questions

- ~~Which committing path does triage use: `bug-commit` widened to triage's entries, or a commit
  of its own from the main checkout?~~ Resolved: `bug-commit` as it stands; it already commits
  entries of any kind (`File`/`Update`/`Retire`).
- ~~How does an entry carry its issue: a new `BODY_KEYS` line (`Issue: #N`)? And how does close
  turn it into `Closes #N` when a change's `idea:` or `fixes:` names that entry?~~ Resolved: an
  `Issue: #N` body line; `/sdlc:intent` copies it onto the new change's `closes:` line, and close
  reads only `closes:` (spec R6–R8).
- ~~Is the `triaged` label enough to skip an issue, or is the comment the record and the label
  only a filter?~~ Resolved: the record is the entry's `Issue:` line or a change's `closes:`; the
  label is the filter, needed because the entry is deleted at ship while the issue stays open until
  the push; the comment is for the reporter.
- ~~Who decides idea vs. bug, and the severity: triage proposes and the person approves at the
  WAIT, or the issue template's fields decide?~~ Resolved: triage proposes, the person decides at
  the WAIT.
- ~~Does setup write the issue templates into `.github/ISSUE_TEMPLATE/` as host-owned files (a
  default), and how does drift treat them?~~ Resolved: yes, as YAML issue forms from
  `defaults/issue-forms/`, host-owned once written; `record` lists them as created, `drift` doesn't
  compare them.
- ~~Should linking to an open change also comment on that change's issue, or only on the triaged
  issue?~~ Resolved: the covered issue goes on the change's `closes:` line, whatever its kind;
  triage comments on the covered issue, and `sync` lists it in the change's issue body, which
  GitHub cross-links.
