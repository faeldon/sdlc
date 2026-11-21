
- **Resolved: how a plugin bug is told from a host bug.** The person says so. The skill may propose
  "the plugin" from a failing `sdlc.py`/`factory.py` call or a plugin skill, but never decides
  (R3). In the plugin's own repo the question isn't asked (`_own_repo()`, R2).
- **Resolved: which marker says "from a host", and whether triage changes.** The marker is a body
  line, `<!-- sdlc:host-bug:<key> -->`, because GitHub drops labels from people without push
  access. Triage changes a little: `intake` flags `from_host`, and the entry gets `Origin: host`
  (R12).
- **Resolved: which refusal text is safe to send, and whether repo-relative paths count as host
  specifics.** They do, outside the plugin's own `.sdlc/` and `.claude/worktrees/` layout. Every
  other path becomes `<path>`, and text that still names the host is left out with a note (R6).
- **Resolved: how the upstream number is recorded.** It goes in `sdlc-upstream.json` in the git
  common dir, never on an `Issue:` line. `recorded_issues()` would read an `Issue:` line as the
  host's own issue of that number (R10, R13).
- **Left open: does the host also keep a local entry to follow the upstream bug?**
  - No (the design): nothing is added to the host's register, and the record lives in the git
    common dir only, so a fresh clone forgets what it filed and could file it again.
  - Yes: a `[bug]` entry with a new `Upstream: owner/name#N` body key (not `Issue:`), committed by
    `inbox-commit` behind the same WAIT. That's a second write under one yes. `status` would also
    rank a bug the host can't fix among its own, unless status learns to put it aside.
- **Left open: the opaque host id.** The design leaves it out: the intent's allowlist doesn't name
  it, and the usage report doesn't exist yet.
  - Sending it now lets this repo see that two issues came from one host, but it's a field anyone
    can read in the issue, with no use yet.
  - Waiting means the report designs it when it has a use.
- **Left open: can a host point upstream at a private repo by config?** The design says no: a fork
  points its own manifest at itself.
  - A config key such as `upstream.repo` would let a company mirror the plugin's issues privately.
    It would also make the repo something a host types, which the intent rules out, and it needs a
    `READS_CONFIG` entry and a setup question.
- **Left for the person: two policy edits.** AGENTS.md's *Trackers* sentence ("loaded only when
  `archive.target` names it") and *Writes before a WAIT* (a sixth, the scratch input file) both have
  to change for this design. Both are named under Contracts touched.
