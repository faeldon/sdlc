---
id: 209
slug: upstream-bugs
tier: 2
impact: minor
stage: shipped
created: 2026-11-21
opened: 2026-11-21T03:44Z
updated: 2026-11-21
shipped: 2026-11-21
idea: 2026-11-21-1
depends_on:
serves: [O1]
origin: host
---

# 209 — A host's /sdlc:bug files a bug in the plugin upstream

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

When the plugin itself breaks in a host, nothing gets the bug to the plugin's repo. `/sdlc:bug` in
a host files into the host's own `.sdlc/work/inbox.md`, which is right for the host's code and a
dead end for the plugin's. The only route upstream is someone opening `faeldon/sdlc`'s issue form
in a browser by hand and rebuilding the context the failing session already had: the command, its
exit, the refusal text, the plugin version and the install scope.

Today's update to 1.11.0 is the example: its six steps, the second install at another scope and
the restart nothing announced were found only because the plugin's owner also owns that host and
read its transcripts from this repo. A host anyone else owns would have hit the same silently.

That gap is also a measurement gap. `PRODUCT.md`'s first bet says "issues from hosts are what would
break this", and O1 is measured by issues filed against setup, `new` or close per release. Both
depend on host bugs reaching GitHub, and nothing helps them get there.

## Outcome

- In a host, `/sdlc:bug` tells a bug in the host's own work from one in the plugin, and for a
  plugin bug offers to file it upstream, on the plugin's repo read from its manifest's
  `repository`, never typed.
- The issue holds only an allowlist: the person's own words (what happened, what they expected,
  how to see it); the failing plugin command, its exit, and the refusal or error it printed, paths
  cut to repo-relative; and a diagnostic block of the sdlc and sdlc-factory versions and install
  scope, the Claude Code, OS and `uv` versions, and the names of the config keys set, never their
  values. No `Sdlc-*` numbers, titles, branch names or file contents. A test feeds a fixture full of
  host specifics and fails if any reaches the rendered body.
- The exact body is shown before anything leaves, in the message and in the dialog's preview,
  behind one WAIT that says the issue is public. Nothing is filed on a no.
- It is filed through the GitHub tracker under the person's own `gh` login, and its number is
  recorded on the host's side, so a rerun never files it twice.
- The upstream issue arrives in a shape `/sdlc:triage` here already reads, with a label or marker
  that says it came from a host, so 207's `origin: host` follows from it when a change takes it.
- **Moves O1:** bugs a host meets in setup, `new` or close reach the plugin's repo as issues, so
  O1's issues-per-release measures hosts, not only this repo.
- The send path, the allowlist renderer, the preview-then-WAIT and an opaque host id are built to
  be reused by the opt-in usage report (an idea not yet filed).

## Affected

- **Area:** the bug skill, the GitHub tracker, issue rendering, triage intake.
- **Files & components:** `skills/bug/SKILL.md`; `scripts/trackers/github.py` (sensitive);
  `scripts/sdlc.py` (the renderer, the diagnostic block, the record of what was filed); a new
  `templates/upstream-bug.md` (irreversible); possibly `.github/ISSUE_TEMPLATE/` or a label here;
  `/sdlc:triage`'s intake; REFERENCE.md *Trackers* and *Issues people file*, README,
  `docs/FEATURES.md`; tests.
- **Downstream:** every host, which this sends a little of its data from, to a public repo; this
  repo's issue tracker and triage; the retrospective's issue counts for O1.
- **Contracts:** *Trackers* (core renders, the tracker sends; core never calls `gh`; a tracker
  never reads `.sdlc/`); *Writes before a WAIT* (an outward-facing write, behind its own WAIT);
  *Intake: `recorded_issues()`* (the record committed before the issue is told); `templates/`
  irreversible; *Nothing about a project or a workspace*, read from the host's side (nothing that
  identifies the host leaves it); *The scripts run on Windows*; *Narrow `allowed-tools`*.

## Constraints

- Nothing is sent without the person seeing the exact body and saying yes: no background filing,
  no hook, no default-on.
- An allowlist, not a scrubber: a field not named is never sent.
- The host's confidentiality first: a refusal's text that can't be cut to something safe is left
  out, and the body says it was.
- Without `gh` or a login, the skill shows the body to paste by hand and files nothing; it never
  fails the host's own `/sdlc:bug`.
- The host's own bug filing is unchanged for a bug in the host's code.

## Open questions

- ~~How does `/sdlc:bug` tell a plugin bug from a host bug: the person says so, or it is inferred
  from a failing `sdlc.py` command or refusal in the session?~~ Resolved: the person says so; the
  skill may only propose (spec R3)
- Does the host also keep a local entry for the upstream bug, to follow it, and how is the upstream
  number recorded (a body line, or a new record `recorded_issues()` knows)? The number: resolved,
  in `sdlc-upstream.json` in the git common dir, never on an `Issue:` line (spec R10, R13); a
  local entry: not in this change, approved with the spec
- ~~Which label or marker says "from a host", and does `/sdlc:triage` here need a change to read
  it?~~ Resolved: a body marker, `<!-- sdlc:host-bug:<key> -->`, since GitHub drops labels from
  people without push access; `intake` flags `from_host` and triage writes `Origin: host` (spec R12)
- ~~What is the opaque host id, and is it sent now or only once the usage report exists?~~
  Resolved: not sent; the usage report designs it when it has a use, approved with the spec
- ~~Which refusal and error text is safe to send? Do repo-relative paths count as host
  specifics?~~ Resolved: they do, outside the plugin's own layout; text that still names the host
  is left out with a note (spec R6)
- ~~Can a host point upstream at a private repo instead of the public one, by config?~~ Resolved:
  no; a fork points its own manifest at itself, approved with the spec (spec R1)
