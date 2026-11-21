---
id: 213
slug: setup-nudge
tier: 2
impact: patch
stage: shipped
created: 2026-11-21
opened: 2026-11-21T04:01Z
updated: 2026-11-21
shipped: 2026-11-21
idea:
depends_on:
fixes: [2026-11-21-12]
serves: [O1]
origin: self
---

# 213 — The setup nudge reaches the person and clears when setup has nothing to do

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

From the bug: "The setup nudge never reaches the person and never clears. It is only a line in
sdlc.py status's output (■ Setup), so a person who doesn't run /sdlc:status never sees it, and a
skill that runs status doesn't pass it on. And after a release that changes no defaults,
/sdlc:setup stops at complete without recording the new version, so status keeps saying "set up
with 1.10.0, the plugin is 1.11.0 → /sdlc:setup" forever."

It happened in this repo on 2026-11-21: `status` showed `■ Setup: set up with 1.10.0, the plugin
is 1.11.0 /sdlc:setup` at a session's start; the model read it (intent's Step 0) and never passed
it on; the person found it in a table hours later and asked why the repo was "still on 1.10".
`/sdlc:setup` then reported `complete: true`, `drift` finding nothing to refresh, break or report,
and wrote nothing, so the line stays. `setup_nudge()` (`scripts/sdlc.py`) compares
`.sdlc/setup.json`'s recorded `version` with the running plugin's and nothing else, so a nudge for
a release that changed no defaults can never be cleared by doing what it says.

## Outcome

- After a release that changes no defaults, `/sdlc:setup` on a `complete` repo leaves `status`
  with no `■ Setup` nudge. A test runs the bug's steps on a fixture set up at an older version and
  fails if the line is still there.
- When a repo's setup is behind, a new session says so in one line, beside 206's release line from
  the startup hook, and skills that run `status` pass `■ Setup` on rather than swallow it. A test
  checks the hook's output for a fixture repo whose setup is behind.
- The nudge never reads as a problem: `vet --strict` still refuses nothing for it.

## Affected

- **Area:** setup's version record, `status`'s nudge, and the startup hook.
- **Files & components:** `scripts/sdlc.py` (`setup_nudge()`, `cmd_record()` or `readiness`,
  `cmd_update`'s `--hook` line); `skills/setup/SKILL.md` (the `complete` stop); possibly the
  skills that run `status`; REFERENCE.md *After an update*; tests.
- **Downstream:** every host: the hook would say one more thing at session start, and setup's
  `complete` stop would change; `.sdlc/setup.json`, which `drift` reads as its baseline.
- **Contracts:** *Setup: `drift()` and `readiness`* (`complete` errs towards false; `record` writes
  `setup.json` each time setup writes, so recording on `complete` is a write where setup now writes
  nothing); *Writes before a WAIT*, if setup records without asking; *Updates: the one hook* (it
  only advises: one line or nothing, never an update); *a nudge in `status` is never a problem*.

## Constraints

- Setup still writes nothing before its question, unless the spec shows a version-only record
  needs none.
- The hook stays one line or nothing, cheap (a file read), and never blocks or fails a session.
- A repo whose defaults did change still gets setup's full refresh, and the nudge stays until then.

## Open questions

- ~~Does the nudge ask `drift` instead of the recorded version (a drift read in every `status`), or
  does setup's `complete` stop re-record the version (a write, so does it need a question)?~~
  Resolved: the nudge asks `drift`, and only when the record is behind; no write (spec R1, R3, R4)
- ~~If setup re-records on `complete`, is that one small "Record 1.11.0?" question, or a named
  exception to confirm-before-writing like the update cache?~~ Resolved: moot; setup doesn't
  re-record
- ~~Does the hook carry the setup line in every repo, or only when no release line is shown, so one
  line stays one line?~~ Resolved: only when no release line is shown (spec R6, R7)
- ~~Which skills pass `■ Setup` on: every skill that runs `status`, or only `/sdlc:status` and
  intent's Step 0?~~ Resolved: `/sdlc:status` and intent's Step 0, approved with the spec (R10)
