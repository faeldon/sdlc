---
id: 209
slug: upstream-bugs
kind: spec
created: 2026-11-21
updated: 2026-11-21
---

# 209 — A host's /sdlc:bug files a bug in the plugin upstream · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

This change takes in no nits: the intent names none.

1. **R1. The upstream repo comes from the manifest.** `sdlc.py upstream` reports `repo` as the
   `owner/name` parsed from the running manifest's `repository` (`release_source()`). It never takes
   the repo from an argument, the host's config or the host's remote. If `repository` is missing or
   isn't a `https://github.com/<owner>/<name>` URL, `available` is false and `why` says so.
   `test_upstream_repo_comes_from_the_manifest` fails if a non-GitHub `repository`, or one changed in
   a fixture manifest, isn't what the report says.
2. **R2. The plugin's own repo files locally.** In this plugin's repo (`_own_repo()` true for the
   main checkout), `upstream` reports `own_repo: true` and `available: false`, and `/sdlc:bug` never
   asks whether the bug is the plugin's. `test_upstream_is_unavailable_in_the_plugins_own_repo`
   fails otherwise.
3. **R3. The person says which kind of bug it is.** In a host, `/sdlc:bug` asks whether the bug is
   in the host's own work or in the plugin. It may propose "the plugin" when the bug as told is a
   failing `sdlc.py` or `factory.py` call, an `/sdlc:` or `/sdlc-factory:` skill, or the plugin's
   docs, but it never decides alone. A host bug follows today's Steps 1–6 unchanged. The skill's
   text is pinned by `test_bug_asks_which_kind_before_filing_upstream` (`tests/test_skills.py`).
4. **R4. Only allowlisted fields reach the body.** `upstream --render` builds the body from a fixed
   shape held in `sdlc.py`. The input file's `## Title`, `## What happens`,
   `## What should happen`, `## How to see it`, `## Command`, `## Exit` and `## Output` sections
   become the person's words and the failing command. Everything else in the body is the diagnostic
   block, and that is all the body holds. Any other section in the input file is dropped and listed
   in `left_out`. `test_upstream_body_holds_only_the_allowlist` feeds a fixture host whose folder
   name, remote, git user and email, change slugs and titles, entry titles, branch names, config
   values, `Sdlc-*` trailers and file contents are each a distinct sentinel, puts every sentinel
   into the input file and into the command's output, and fails if any sentinel appears in the
   rendered title or body.
5. **R5. The diagnostic block is versions and key names.** It holds the sdlc version and the scope
   it's installed at (or `read in place`), the sdlc-factory version and scope (or `not installed`),
   the Claude Code version, the OS name and release, the `uv` version, and the dotted names of the
   keys set in the host's `.sdlc/config.toml`, sorted, with no values. A tool that can't be read
   shows `unknown`, and rendering goes on. `test_upstream_diagnostics_name_keys_never_values` fails
   if a config value shows up, or if a missing `claude` or `uv` raises.
6. **R6. Host specifics are cut, and text that stays unsafe is left out.** Every free-text field
   (the person's words, the command, the output) goes through one cutter (`_cut_host()`):
   - Absolute paths become `${CLAUDE_PLUGIN_ROOT}/…` under the plugin, `<repo>/…` under the host's
     main checkout or a worktree, and `<path>` anywhere else.
   - A repo-relative path is kept only under the plugin's own layout (`.sdlc/` and
     `.claude/worktrees/`, with each change folder shown as `<change>`). Any other path becomes
     `<path>`.
   - Change names and slugs, entry ids and titles, branch names, commit SHAs, `#N` issue refs, the
     remote's URL and owner, git's `user.name` and `user.email`, and every string config value are
     replaced by their placeholder.

   If a known specific is still present after the cut, the field is left out and the body says so
   (`*Left out: it named the host.*`). Output longer than 40 lines keeps its last 40 and says how
   many it dropped. `test_upstream_cut_leaves_out_what_it_cannot_make_safe` fails if a field holding
   a specific the cutter can't place is sent, or if the note is missing.
7. **R7. The body sent is the body shown.** `upstream --render` prints `{title, body, key,
   left_out, already}`, and `key` is a hash of the cut, allowlisted fields. `upstream --send --key
   <key>` renders again and refuses, filing nothing, if the key differs.
   `test_upstream_send_refuses_a_body_not_previewed` fails if a changed input file is filed under an
   old key.
8. **R8. One WAIT, public, with the exact body.** `skills/bug/SKILL.md` keeps exactly one `WAIT`
   heading. For a plugin bug its question is literally
   `File this bug publicly on <owner/name> as <login>? Anyone can read it. (yes / edit it / no)`.
   The rendered body is shown in the message and in the dialog's preview first. Nothing is sent on
   any answer but a chosen yes. `test_skills.py`'s existing WAIT and dialog tests cover the heading.
   `test_bug_shows_the_upstream_body_before_its_wait` pins the order (render, show, ask, send).
9. **R9. Filed under the person's own login, with nothing GitHub would drop.** The GitHub tracker
   gets `file_issue(repo, title, body)`, which runs `gh issue create --repo <owner/name> --title …
   --body-file -`. It passes no `--label`, no `--assignee` and no `--milestone`, because GitHub drops
   those for anyone without push access to the repo. `test_github_file_issue_names_the_repo_and_sets_nothing_else`
   (a fake `gh`) fails if another flag is passed or if `--repo` is missing.
10. **R10. A rerun never files twice.** Before it calls `gh`, `--send` records `{key: {repo,
    state: "sending"}}` in `sdlc-upstream.json` in the git common dir. After it files, it records
    `state: "filed"` with the number and URL. A key already `filed` makes `--send` print that URL and
    send nothing, and makes `--render` report it as `already`. A key left at `sending` first looks
    for the marker among the login's own issues on that repo (`find_issue(repo, marker)`, `gh issue
    list --repo … --author @me --state all --json number,url,body`, matched locally), and files only
    if none holds it. `test_upstream_send_never_files_twice` and
    `test_upstream_send_after_a_stopped_send_finds_the_issue_first` fail on a second `issue create`.
11. **R11. With no `gh` or no login, nothing is filed and the bug still ends cleanly.** `upstream`
    reports `available: false` and a `why` (`gh isn't installed`, or `run gh auth login`). `--send`
    then exits 0 with `filed: null`, the `why`, and the repo's new-issue URL. The skill shows the body
    to paste there and ends its run without an error. `test_upstream_without_gh_files_nothing`
    fails if `gh` is called or the exit isn't 0.
12. **R12. The upstream issue says it came from a host, in a form triage reads.** The body's first
    line is `<!-- sdlc:host-bug:<key> -->`. `sdlc.py intake` adds `from_host: true` to each issue
    whose body holds `<!-- sdlc:host-bug:`. `/sdlc:triage` writes `Origin: host` on the entry it
    files from such an issue, so an intent taking it proposes `origin: host` (207).
    `test_intake_flags_an_issue_from_a_host` fails otherwise.
13. **R13. The upstream number never enters the host's issue records.** No `Issue:` line, `closes:`
    line or `Sdlc-Triaged:` trailer is written for an upstream issue, so `recorded_issues()` and
    `mark-triaged` never confuse it with the host's own issue of the same number.
    `test_an_upstream_send_changes_nothing_recorded_issues_reads` fails if `recorded_issues()`
    differs after a send.
14. **R14. It runs on Windows.** The renderer, the cutter and the record use `encoding="utf-8"`,
    `newline="\n"`, `shutil.which` for `claude`, `uv` and `gh`, and `as_posix()` for every path they
    compare. The renderer's tests are marked `portable`.
15. **R15. The docs say what it does.** The new `upstream` command appears in `docs/FEATURES.md`
    (`tests/test_feature_map.py`). These are updated: REFERENCE.md *Trackers* and *Issues people
    file*, README's line on `/sdlc:bug`, and AGENTS.md's *Trackers* and *Writes before a WAIT*
    paragraphs (see Contracts touched).

## Design

### What I took as given, and checked

- The manifest's `repository` is `https://github.com/faeldon/sdlc` (`.claude-plugin/plugin.json`).
  `release_source()` already reads it for update checks, and a fork's manifest names the fork.
- `_own_repo(main)` tells the plugin's own repo from a host by its files (`sdlc.py:5257`).
- `plugin_installs()` / `most_specific()` give each plugin's version and scope, and `in_place()`
  says when the copy is read in place (`sdlc.py:9372–9476`).
- The GitHub tracker's `_create()` creates labels on the repo it runs in, and assigns `@me`
  (`github.py:186`). Both are wrong for someone else's repo, so the upstream send can't reuse it.
- `intake()` skips any issue labelled `sdlc`, `landed` or `triaged`, and returns the body
  (`github.py:273`). So a host bug must carry neither label, and a body marker is something triage
  can already see.
- `recorded_issues()` reads `#N` on `Issue:` lines as the host's own issue N (`sdlc.py:7745`). An
  upstream number written there would make `mark-triaged` comment on the wrong issue.
- The `Origin:` body key already exists (`BODY_KEYS`, `sdlc.py:197`).
- One fact comes from GitHub, not from the code: labels, assignees and milestones on a new issue are
  silently dropped for anyone without push access. That is why the "from a host" sign is a body
  marker and not a label.

### The pieces

1. **`sdlc.py upstream`** (a new `@command`, not in `READ_ONLY` because `--send` writes and reaches
   the network).
   - With no flag, it prints `{available, why, own_repo, repo, login, input, new_issue_url}`.
   - `input` is `<git-common-dir>/sdlc-upstream-input.md`, the scratch file the skill writes the
     person's words and the failing command into. It sits in the git common dir, so it dirties no
     checkout, worktree or main.
   - `login` comes from the tracker's `login()` (`gh api user --jq .login`).
2. **The renderer, `upstream_body(home, fields)`**, a pure function apart from reading diagnostics.
   It takes the parsed input sections (R4), cuts each field (R6) and lays them out in a constant
   `UPSTREAM_BODY` shape: marker, a one-line note that `/sdlc:bug` filed it from a host, then
   `### What happens`, `### What should happen`, `### How to see it`, `### The command` (the command
   and its exit, the output in a `text` fence) and `### Diagnostics` (R5). The title is
   `sdlc: <the person's title, cut>`. A field the person left empty is omitted along with its
   heading. A body over `ISSUE_LIMIT` loses the oldest output lines first.
3. **The cutter, `_cut_host(text, specifics)`**. `specifics` is built once per render from what
   the plugin can already see:
   - the main root and each worktree path (`main_root()`, `worktrees()`), and the home directory
   - `change_dirs()` names and slugs, `inbox_entries()` ids and titles
   - `git branch --format`, the remote URLs, `user.name` and `user.email`
   - every string value in the resolved config

   Replacements run longest first. Then a final check fails a field that still holds any specific
   (R6).
4. **Diagnostics, `upstream_diagnostics(home)`**. It reads `plugin_version()`, `plugin_installs()`
   and `most_specific()` for sdlc and sdlc-factory, `claude --version` and `uv --version` (first
   version-looking token, else `unknown`), and `platform.system()` / `platform.release()`. The key
   names come from the parse `load_config()` already makes, so config still has one reader.
5. **The send, `upstream --send --key <key>`**. It renders again and checks the key (R7), checks
   the record (R10), writes `sending`, and calls the GitHub tracker's `find_issue()`, then
   `file_issue()`. It writes `filed` with the number and URL, removes the input file, and prints
   `{filed, url, number}`.
   - The tracker is loaded by `upstream_tracker()`: the same by-path loader as `tracker()`, pinned
     to `trackers/github.py`, whatever `archive.target` says. The host's own tracker setting has no
     bearing on the plugin's repo.
   - Its readiness is `shutil.which("gh")` and `gh auth token`'s exit, not the host remote check
     `unavailable()` makes.
6. **The tracker gets three new methods**: `login()`, `find_issue(repo, marker)` and
   `file_issue(repo, title, body)`. Each takes everything it needs as arguments and reads no
   `.sdlc/`.
7. **The skill**, `skills/bug/SKILL.md`:
   - Step 0 also runs `upstream`.
   - Step 1 asks which kind of bug it is, in a host only (R3). For a plugin bug, Step 1 gathers the
     title, what happens and what should, how to see it, and, from the session, the failing plugin
     command, its exit and what it printed.
   - Step 3 `Write`s those under the fixed headings to `input`, runs `upstream --render`, and shows
     the title, the body and `left_out`.
   - Step 4's one WAIT asks R8's question.
   - Step 5 runs `upstream --send --key <key>`. With `available: false`, it shows the body and
     `new_issue_url` to paste by hand.
   - Step 6 reports the URL and says to follow it there.
   - It adds one `Bash(... sdlc.py upstream *)` rule.
8. **Triage**: `cmd_intake()` sets `from_host` (R12), and `skills/triage/SKILL.md` Steps 2–3 say an
   entry filed from such an issue carries `Origin: host`.

### Edge cases

- A no, or an edit, leaves the record untouched. An edit rewrites the input file and renders again,
  under a new key.
- A send that dies after GitHub made the issue leaves `sending`, and the rerun finds it (R10).
- Two worktrees filing the same bug share one record file. The record is written under the existing
  `_main_lock()`, so two sends of one key can't both create an issue.
- The input file is overwritten by the next plugin bug if a run stops after a no. It never leaves
  the machine and is never committed.

### Boundaries

- **Always:** render from the allowlist alone, show the exact body before the WAIT, and record
  before and after the send.
- **Asks first:** every send, behind the one WAIT, which names the repo, the login and that the
  issue is public.
- **Never:**
  - send anything in the background, from a hook, or on by default
  - set a label, assignee or milestone upstream
  - write an upstream number into the host's register or change folders
  - read the repo from anywhere but the manifest
  - fail a host's `/sdlc:bug` because filing upstream can't be done
  - send the opaque host id (see the questions below)
- No usage report is built here. The renderer, the cutter, the diagnostics and the send are
  general functions so that report can use them later.

## Contracts touched

- **Trackers: core renders, the tracker sends; core never calls `gh`; a tracker never reads
  `.sdlc/`.** Kept: `sdlc.py` renders and records, and `github.py` makes every `gh` call, given only
  strings. **Needs an edit to the policy:** AGENTS.md says each tracker is "loaded only when
  `archive.target` names it". This design also loads `trackers/github.py` for `upstream`, whatever
  the target, because the plugin's repo is on GitHub whatever the host uses. The sentence should
  become "loaded only when `archive.target` names it, or, the GitHub one alone, by `upstream`, to
  file on the plugin's repo". That is the person's decision.
- **Writes before a WAIT, and the one write with no WAIT.** **Needs an edit to the policy:**
  rendering the preview needs the person's words in a file before the WAIT. The scratch file
  `sdlc-upstream-input.md` in the git common dir would be a write before a WAIT, joining the five
  named there. It decides nothing, dirties no checkout and is never committed: the same footing as
  `findings.md` and the update cache. The record `sdlc-upstream.json` is written only after the yes.
  It's state like the main lock, not an artifact.
- **Intake: `recorded_issues()` is the one reader, and the record is committed before the issue is
  told.** Kept by keeping the upstream issue out of it (R13). The upstream record isn't one of the
  three records; it is about an issue on another repo. "Recorded before the send" holds through the
  `sending` state (R10). It is a state file, not a commit, so a fresh clone forgets it; see the
  questions below.
- **Templates are irreversible, `templates/` overridable by a host.** Kept by not adding a template.
  The body's shape is a constant in `sdlc.py`, so a host override can't add fields the allowlist
  doesn't name.
- **Nothing about a project or a workspace, read from the host's side.** Kept by R4 and R6 and their
  sentinel fixture. The test data in this repo stays neutral (`reopen-drafts`).
- **The scripts run on Windows.** Kept by R14.
- **Narrow `allowed-tools`; one WAIT per writing skill; the dialog.** Kept: one new `Bash(...)`
  rule, written as the skill runs it, and the existing WAIT heading with a fourth question form,
  as retire and retag already have.
- **Only the named steps push.** Untouched. `gh issue create` is not a git push.
- **`scripts/trackers/` is `[review] sensitive`.** This change gets the deep review there.

## Alternatives rejected

- **A label such as `from-host`.** GitHub drops labels set by anyone without push access, so the
  label would be missing on exactly the issues it exists for. A body marker survives, and `intake`
  already returns the body.
- **Reusing `_create()` or the host's own `tracker()`.** `_create()` makes labels in the repo it
  runs in and assigns `@me`. `tracker()` returns nothing when `archive.target = "none"`, which would
  make filing upstream depend on how the host archives its own changes.
- **A scrubber over a free body the skill writes.** The intent asks for an allowlist. A model-written
  body can't be checked by a test, and a scrubber lets through whatever it doesn't know about.
- **Passing the person's words as command-line arguments** instead of a scratch file. Multi-line
  text with quotes in a Bash call is fragile under `allowed-tools` matching, and on Windows. `--send`
  would have to be given the same text twice, with no guarantee it matches the preview.
- **A `templates/upstream-bug.md`.** A host could override it and add fields to what leaves the
  host. And the shape is this repo's intake contract, not a host's choice.
- **Inferring a plugin bug from the session without asking.** It's a guess that sends data off the
  host. The person says which kind; the skill may only propose.
- **A config key pointing upstream at another repo.** A fork's manifest already does that, with no
  new key, no `READS_CONFIG` entry and no setup question. See the questions below for a private
  mirror.
- **A change to `.github/ISSUE_TEMPLATE/`.** `gh issue create --body-file` bypasses the forms, and
  triage reads the marker, not a form.

## Verification

```bash
uv run --group dev pytest -q -n auto -k "upstream or from_host or intake or file_issue"
uv run --group dev pytest -q tests/test_skills.py tests/test_feature_map.py tests/test_nothing_local.py
uv run --group dev pytest -q -m portable
./check.sh
```

A healthy run shows:

- Every test named in the Requirements passes.
- `test_skills.py` passes with the new rule used and `bug`'s single WAIT.
- `test_feature_map.py` passes with `upstream` mapped.
- `./check.sh` ends green: ruff, the format check, pytest and `claude plugin validate --strict`.

By hand, in a scratch host with the plugin loaded (`claude --plugin-dir <path-to-clone>`):

1. Without `gh` on `PATH`, `/sdlc:bug` on a plugin bug shows the body and the new-issue URL, files
   nothing, and ends without an error.
2. With `gh` logged in, `upstream --render`'s body holds none of the scratch host's names.

The second check doesn't send: answering no proves nothing leaves.

