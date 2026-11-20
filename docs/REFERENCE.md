# sdlc reference

What a repo using the plugin can set, and how the plugin behaves in it. The
[README](../README.md) is the place to start; this is the place to look things up.
`sdlc.py config` shows every setting as your repo resolves it, and `sdlc.py readiness` whether
the repo is set up: `complete` when `/sdlc:setup` has nothing to draft, with the commands left
unset by choice in `unset`.

- [Configuration: `.sdlc/config.toml`](#configuration-sdlcconfigtoml)
- [The docs](#the-docs)
- [Templates: `.sdlc/templates/`](#templates-sdlctemplates)
- [After an update: refresh, reset, uninstall](#after-an-update-refresh-reset-uninstall)
- [`.sdlc/work/` and worktrees](#sdlcwork-and-worktrees)
- [Numbering](#numbering)
- [Trackers](#trackers)
- [The project doc](#the-project-doc)
- [The product doc](#the-product-doc)
- [Releases](#releases)
- [Retrospectives](#retrospectives)
- [Metrics](#metrics)

## Configuration: `.sdlc/config.toml`

Every key is optional, and `/sdlc:setup` writes only the ones that differ from their defaults. A
command left out is null, and the skill that would run it says there is nothing configured rather
than guessing. An unknown key is a warning, so a typo never passes for a setting.

```toml
[commands]
check = "make check"                        # the gate /sdlc:ship runs on this diff; pass or fail
build = "make integration"                  # the slow gate, run when a changed path matches:
build_when = "^src/"                        #   a regex over `git diff --name-only`
scan = "make scan"                          # drift across the whole repo; /sdlc:health runs it
worktree_setup = "make setup {worktree}"    # after /sdlc:intent makes a worktree, run from the main checkout
close_list = "ls /tmp/cache-{suffix}"       # read-only: what a closed change left outside git
close_cleanup = "! make drop {id}"          # handed to the human by /sdlc:close; never run by a skill
close_cleanup_runs = false                  # true: close runs close_cleanup itself, last, behind its question

[docs]
process = ".sdlc/SDLC.md"                   # the default: your answers to the plugin's process guide
review = ".sdlc/REVIEW.md"                  # the default: what you add to its review guide; without one, the guide alone
policy = "CLAUDE.md"                        # the default (AGENTS.md when that's the only one): the invariants /sdlc:spec designs inside
read_before_design = ["docs/conventions.md"]
explore = "/db:explore"                     # a skill or command for looking at the system itself
health = ".sdlc/HEALTH.md"                  # the default: each scan finding's meaning and response tier; off while absent
context = ["CLAUDE.md", ".claude/CLAUDE.md", "AGENTS.md"]  # the default: what gives a session its context
direction = ".sdlc/DIRECTION.md"            # the default: goals and milestones, rewritten by /sdlc:retro
project = ".sdlc/PROJECT.md"                # the default: which issue fields to fill; off while absent
product = ".sdlc/PRODUCT.md"                # the default: users and outcomes every intent serves; off while absent
insights = ".sdlc/INSIGHTS.md"              # the default: your own synthesis questions for /sdlc:retro; off while absent

[archive]
target = "github"                           # a module in scripts/trackers/; "none", the default, numbers locally
command = "my-tracker save {dir} {id}"      # target = "command": archive {dir}, print where it went

[release]
version_files = ["package.json"]            # each with one `version` line, edited in place; unset = no releases
tag = "v{version}"                          # the default: the release tag, and the next release's boundary
changelog = "CHANGELOG.md"                  # optional: the notes are added after its <!-- sdlc:releases --> line, else to the top
after_bump = "uv lock"                      # optional: run by /sdlc:release after the bump; the tracked files it changes are committed too; {version}, {tag}
prepare = "npm pack"                        # optional: run by /sdlc:release after after_bump; builds into untracked or ignored paths only; what it prints is shown at /sdlc:publish; {version}, {tag}
remote = "origin"                           # the default: where publish, and close and release by `[git] push`, push main and the tag
publish = "npm publish"                     # optional: run by /sdlc:publish after the push, with no terminal and stdin closed; {version}, {tag}
deprecations = ".sdlc/deprecations.toml"    # the default: each shim and the version that removes it; off while absent
due_after_changes = 5                       # the default: minor-or-higher changes before status says Release due; 0 = off
due_after_days = 14                         # the default: days since the oldest unreleased close before it's due; 0 = off

[retro]
after_releases = 2                          # the default: releases before status says Retro due; 0 = only a major one
evidence = ["./scripts/usage-summary.sh"]   # optional: what users did, printed for the product pass; only with a product doc
indicators = ["./scripts/complexity.sh"]    # optional: measures only a language can tell, as JSON rows; a table in the report
test_times = ["cat build/junit.xml"]        # optional: each prints a JUnit XML report on stdout, read for the pruning pass
test_paths = ["checks/"]                    # optional: the paths that are tests, replacing the conventions; `dir/` prefixes or globs
doc_paths = ["handbook/"]                   # optional: the paths that are docs, replacing the conventions

[metrics]
transcripts = true                          # the default: close reads this repo's transcripts, numbers only
idle_minutes = 30                           # the default: a longer wait is the person away, not answering
stop_allowance = 1                          # the default: stops beyond a change's approvals its person should expect

[review]
sensitive = [".github/workflows/", "scripts/release*"]  # optional: paths whose changes get ship's deep review
irreversible = ["migrations/"]              # optional: paths a revert doesn't undo; ship's commit says how to recover

[git]
base = "master"                             # optional: the branch changes start from and land on; unset = detected
attribution = false                         # unset until setup asks: false hides the agent's lines, true keeps them
push = ["close", "release"]                 # optional: the steps that push main, inside their own approval; unset = both with archive.target github, else []
nudge_after_changes = 1                     # the default: status says Unpushed once this many closed changes aren't on the remote; 0 = off
```

The placeholders:

- `archive.command`: `{dir}` is the shipped folder's path, `{id}` and `{slug}` the change's, and
  `{sha}` the commit it landed as. It must exit 0 and print where the change went, or close stops
  before removing the folder.
- `commands.worktree_setup`: `{worktree}` is the new worktree's path, and `{main}` the main
  checkout's, where it runs: a setup that links untracked data into the worktree names both.
- `commands.close_list`: `{suffix}` is the change's branch name with `-` as `_`.
- `commands.close_cleanup`: `{id}` is the change's number. A leading `!`, the prompt's prefix for
  a command the human types, is dropped when close runs it, since `sh` would read it as "not".

The commands `sdlc.py` runs itself (`release.after_bump`, `release.prepare`, `release.publish`,
`retro.evidence`, `retro.indicators`, `retro.test_times`, a project field's `command` lookup, `archive.command`,
`commands.close_cleanup` under `close_cleanup_runs`, and each acceptance check) run as `sh -c "<command>"` from the repo root on every platform: `/bin/sh` on macOS and
Linux, and on Windows the `sh` on `PATH`, Git for Windows', never `cmd.exe`. So one config means
the same thing in every session, and the same as the skills' own commands, which Claude Code runs
in Git Bash there. With no `sh` on Windows the command is refused, saying so. Their output is read
as UTF-8, with any byte that isn't UTF-8 replaced.

With `commands.close_cleanup_runs = true`, `/sdlc:close` names the cleanup in its question, and a
yes has `sdlc.py close` run it as its last step: after the merge, the `Close` (or `Drop`) commit,
the worktree's and branch's removal and the push, for a shipped or a dropped change alike, whatever
`close_list` found, with ten minutes to finish. Both keys are read from the base branch's config as
it was before the merge, so a change that turns the switch on, or edits the command, takes effect
from the next close. A cleanup that fails or times out is reported as `cleanup_failed` and handed to
the human; the close has landed all the same, and won't run it again.

A version line is `"version": "1.2.0"` (JSON) or `version = "1.2.0"` (TOML). A file with none,
or more than one, is refused rather than guessed at.

A `[docs]` path under `.sdlc/work/` is read like any other, from the checkout `config` runs in.

### Risky paths: `[review]`

`sensitive` and `irreversible` each list repo-relative paths: an entry ending in `/` names every path
under it, any other is an fnmatch glob (`*` crosses `/`), and a renamed file counts by both its
names. `sdlc.py preflight NNN` reports what the change's diff touches of each as its `risk` part,
read from the base branch's checkout, so a change can't lighten its own review by editing them. A
diff touching a `sensitive` path is `deep`: `/sdlc:ship` runs `commands.build` whatever
`build_when` says, has the plugin's `sdlc:reviewer` agent review the diff in a fresh context (its
findings marked `By: fresh` in `findings.md`) and its `sdlc:security` agent review it for
security beside it (`By: ship-security`), and its question names the paths. One touching an
`irreversible` path carries a `How to recover:` paragraph in its commit: for each, the command that
reverses it, or the fix forward. Risk never changes a change's tier. With neither set, every change
ships alike.

`preflight`'s `passes` part says which of ship's further passes apply, each with `applies` and
`why`, and none applies to a factory run (a change with a `decision.md`), whose own reviewers ran:

- **`security`**: a deep diff, as above.
- **`behaviour`**: a Tier 2 change with a filled `spec.md`. Ship runs the spec's path end to end
  itself, leaving out the gate and the change's acceptance checks, each command behind the
  person's prompt. Each failure is a finding marked `By: ship-behaviour`, and the commands run are
  its evidence.
- **`ui`**: the base branch's `.sdlc/factory.toml` holds a complete `[ui]` (`serve`, `shoot` and
  `paths`), and the diff touches its `paths`. It is read from the base branch, never the change's
  checkout, so a change can't turn its own UI review off. The `sdlc:ui` and `sdlc:ux` agents
  review the screenshots `factory.py shots` left under `.sdlc/reports/shots/<change>/`, marked
  `By: ship-ui` and `By: ship-ux`. `shots` lists the newest set that finished (`problem: null`),
  has every page at every width, and is newer than every changed path under `[ui] paths`. With
  none, `why` says which failed, and both reviews are skipped with it. Ship never takes a
  screenshot.

Each pass that applies says in `findings.md`'s note that it ran, or was skipped and why; `sdlc.py
ship` refuses a note that says neither, and the question names each.

### The base branch: `[git] base`

Every change branches from the base branch and lands back on it. Ship brings a branch up to date
with it, close fast-forwards it, release tags it, close, release or publish pushes it, and
status, release and the retrospective read history along its first-parent line. Wherever these docs say `main`, they
mean this branch.

`git.base` set is the base branch. Unset, it is worked out, in this order:

1. `main`, when the repo has a local `main`.
2. The branch `origin/HEAD` names, when that branch exists locally: what a clone of a repo whose
   default branch is `master` has.
3. Nothing.

It is never the branch the checkout happens to be on, `init.defaultBranch`, or what GitHub
reports, since the first two describe one machine rather than the repo and the third is a network
call. `config` prints the answer as `git.base`, with `git.base_source` saying which way it came:
`config`, `detected` or `unset`. `/sdlc:setup` writes `base` when the branch it detects isn't
`main`, so a later change to `origin/HEAD` can't move it, and asks for it when nothing is
detected.

**`git.attribution`** is the host's answer to whether a session's commits and pull requests name
the agent (the harness's `Co-Authored-By:` line and "Generated with" footer; the commits
`sdlc.py` makes carry only `Sdlc-*` trailers either way). It has no default:

- **Unset:** nothing is written, and `/sdlc:setup` asks, on a first setup or a later one, proposing
  no answer. `readiness` reports `attribution: missing`, not chosen.
- **`false`:** setup merges `"attribution": {"commit": "", "pr": "", "sessionUrl": false}` into
  `.claude/settings.json`, beside the allow rules: the object form, since Claude Code before
  v2.1.281 rejects `"attribution": false` and skips the whole file. `readiness` gives that object
  as `attribution.merge` until the file holds it, and warns when `.claude/settings.local.json` sets
  another, which wins over the shared file. `/sdlc:ship` leaves the lines out of its commit too.
  Setup's record notes the object, and `/sdlc:uninstall` removes it only when it is still exactly
  that.
- **`true`:** the harness's own lines, and nothing written.

With no base branch, or one that doesn't exist here, every command that writes refuses before it
does anything: `new` before it claims a number, so no GitHub issue is opened for a change that
can't be made, and `base`, `close`, `release`, `publish` and `retro-commit` too. `status`,
`unreleased` and `retro` report it and list no landed changes.

Changing `base` in a repo that has already closed changes points every history reader at the new
branch's line. The changes closed on the old one aren't found there unless the old branch was
merged into it by fast-forward.

### Whether the factory is enabled: `config`'s `factory`

`sdlc.py config` prints `factory: {"enabled": …, "scope": …}`, which `/sdlc:intent` reads to
decide whether its question offers `yes, for the factory` beside `yes, by hand`. It is not a
setting: it comes from Claude Code's own `enabledPlugins`, in three files read from the most
specific down, the first naming any `sdlc-factory@<marketplace>` deciding:

1. `.claude/settings.local.json` in the main checkout (`scope: local`);
2. `.claude/settings.json` in the main checkout (`project`);
3. `~/.claude/settings.json` (`user`).

So a factory turned off in `settings.local.json` is off for that repo, whatever the user's file
says. A missing file, one that won't parse, or no file naming the factory reads as
`{"enabled": false, "scope": null}`, with no warning: the core never needs the factory, and runs
nothing to find it. A factory loaded with `claude --plugin-dir` writes no settings, so it isn't
found, and intent asks its question as it does without one.

## The docs

The process's own docs live in `.sdlc/`, beside its config, so `docs/` is left to your project.

- **`docs.process`** (`.sdlc/SDLC.md`) holds your answers to the plugin's process guide
  (`guide/process.md`, which `config` names as `docs.process.guide`): the failure your process
  stops, what is always Tier 2 here, your gate, how a commit reaches your users. The guide holds
  the rest, the tiers and what each stage means, and is read in place from the installed plugin,
  so an update reaches you without a setup diff. Setup starts your file from `defaults/SDLC.md`.
- **`docs.review`** (`.sdlc/REVIEW.md`) holds what you add to the plugin's review guide
  (`guide/review.md`, `docs.review.guide`): the ways your code has failed. Without one,
  `/sdlc:ship` works through the guide alone and says so.
- **How the two are read.** Each file is cut into blocks at each heading and each `- **lead**`
  bullet. A block of yours with the same heading path, or lead, as one of the guide's stands in
  for it when it holds text of its own; any other is read after its parent's block in the guide;
  a heading with nothing under it only places what follows. To change something the guide says,
  copy its block into your file and edit it there.
- **A whole copy, from before 1.5.0.** A repo set up earlier has the whole guide copied into
  `.sdlc/SDLC.md` and `.sdlc/REVIEW.md`. From 1.5.0 every process and review doc is read as
  answers (`layout: answers`), after the guide, so a whole copy has the skills read each rule
  twice. Run `/sdlc:setup reset process` (and `review`): it shows the doc against the answers
  template, behind its one approval, and you carry over only what you changed. `drift` then notes
  only when the plugin's guide changed (`guide-changed`).
- **`docs.policy`** holds the invariants a design has to stay inside: `CLAUDE.md`, or `AGENTS.md`
  when the repo has no `CLAUDE.md`. Set it to name another file.
- **`docs.health`** (`.sdlc/HEALTH.md`) holds what each finding your scan can report
  means, and the response tier it usually gets. Off while absent; `/sdlc:setup` drafts it from
  `defaults/HEALTH.md` once `commands.scan` is set.
- **`docs.insights`** (`.sdlc/INSIGHTS.md`) holds your own synthesis questions for the
  retrospective's *Insights*, read after the plugin's `guide/insights.md` (`docs.insights.guide`),
  block by block: a pillar's `##` (Value, Speed, Quality, Autonomy, Cost, Simplicity, Tradeoffs)
  holding text replaces its question, one with nothing under it only places what follows, a `###`
  under a pillar's `##` adds a question on that pillar's figures, and any other `##` adds one on
  the Tradeoffs figures. A title asked twice is a problem, and the second is dropped. Off while
  absent; setup never copies or drifts it.
- A missing doc is reported, never silently replaced (except the review).

**Three commands, three questions.** `commands.check` is the gate `/sdlc:ship` runs on this diff:
is it correct, pass or fail. `commands.build` is the slow gate, run when a changed path matches
`build_when`. `commands.scan` looks for drift across the whole repo: `/sdlc:health` runs it,
and it produces findings rather than a pass or fail. A task of your own named `doctor` or `health`
is usually your scan; setup proposes it for `commands.scan`. It is unrelated to the plugin's
`sdlc.py readiness`, which only says whether the repo is set up for the plugin.

**`guide/`, `defaults/` and `templates/`.** A file in the plugin's `guide/` is read in place and
never copied: the process, review and insights guides. A file in `defaults/` is a doc `/sdlc:setup` copies
into your repo once; from then on it's yours, and the plugin only reads it. A file in `templates/`
is the shape of a file the plugin writes itself, each time it creates or rewrites one, and a
same-named file in `.sdlc/templates/` replaces it.

**AGENTS.md.** `AGENTS.md` is the instructions file other coding agents read, and Claude Code
reads it too when there's no `CLAUDE.md`. To give every agent and every Claude Code version the
same guide, keep it in `AGENTS.md` and make `CLAUDE.md` one line, `@AGENTS.md`; that's what
`/sdlc:setup` writes in a repo with neither. Then set `docs.policy = "AGENTS.md"`, since the
`CLAUDE.md` holds no invariants of its own.

**`docs.context`** lists the docs that give a session its context; the default is `CLAUDE.md`,
`.claude/CLAUDE.md` and `AGENTS.md`. `/sdlc:ship` runs a review pass of its own over them, and
over any `CLAUDE.md` or `AGENTS.md` above a changed path, whatever review the repo has: does the
diff make one say something false, or add something a future session needs and couldn't find
quickly? And is that already said in another context doc or a docstring? Then it proposes a
pointer there, not the line again. A proposed edit is shown with the findings, approved with the
commit, and lands in it. `sdlc.py context` does the listing, and flags their lines naming a path
the diff deletes or renames.

## Templates: `.sdlc/templates/`

`intent.md`, `spec.md` and `plan.md` here replace the plugin's own (`templates/`), file by file,
and so does `direction.md`, the sections `/sdlc:retro` fills. The plugin's are generic. A repo's
own can add the sections its domain needs and prompts in its own words; keep the placeholders
(`NNN`, `SLUG`, `TITLE`, `YYYY-MM-DD`) and the frontmatter, which `sdlc.py` reads. Prompt lines
start with `<`: two or more left in a file is how `sdlc.py status` tells a scaffold nobody has
written from a real artifact.

`inbox.md` here replaces what `.sdlc/work/inbox.md` starts as, when `/sdlc:retro` or `/sdlc:ship` first
adds a seed to a repo with none, and `notes.md` what a change's `notes.md` starts as, when a skill
or the factory first writes one. None has prompts: its note carries the rules. `checks.md`
is what a change's acceptance checks start as; its one example section's prompts make an untouched
copy a scaffold, which `sdlc.py vet` reports rather than runs. `findings.md` is the shape of the
file `/sdlc:ship` writes its review's findings into; an override keeps its `## F<n>. [rank]
[pass] title` headings and `Evidence:`, `Class:`, `Disposition:` and `Reason:` lines, which
`sdlc.py` counts.

`changelog.md` here replaces the section `/sdlc:release` adds to `release.changelog`. Its
placeholders are `{{version}}`, `{{date}}` and `{{notes}}`, filled as plain text, so a brace in a
note is kept as written. An override must keep `{{version}}` and `{{notes}}`. Like `issue.md`, its
text is rendered as it stands, so it has no title or note.

`issue.md` here replaces the layout of the change's issue. Its placeholders are `{{title}}`,
`{{name}}`, `{{tier}}`, `{{stage}}`, `{{impact}}`, `{{branch}}`, `{{commit}}`, `{{depends_on}}`,
`{{updated}}`, `{{problem}}`, `{{outcome}}` and `{{artifacts}}`. The marker line that ties the
issue to its change is written above it by `sdlc.py`, so no template can lose it.

## After an update: refresh, reset, uninstall

The docs setup copies from the plugin's defaults are yours once copied, so updating the plugin
never touches them. Rerun `/sdlc:setup` after `claude plugin update`: it shows what the new version
changed under them, and drafts the changes you haven't made yourself, behind its one approval.

**`.sdlc/setup.json`** is setup's record, written by `sdlc.py record` each time setup writes, and
committed with the rest. It holds the plugin version, the config keys that version knew, a hash
of each block of each default behind one of your docs (`process`, `review`, `health`, `product`,
`project`), a hash of each plugin template, the files setup created, and whether it added the
`.claude/worktrees/` line to `.gitignore`. A block is a `##`, `###` or `####` section, or a
`- **lead**` bullet. Nothing else reads it, and `sdlc.py status` names it when it is older than
the plugin, or missing.

**`sdlc.py drift`** (read-only, JSON) compares each block of your doc with the default now and the
recorded hash, and sorts what it finds:

| Found | Means | Setup |
|---|---|---|
| `added`, `refreshed`, `removed` | the plugin changed a block you never touched | drafts it, in `refresh` |
| `conflict` | you both changed it | shows both, in `report`; you merge it |
| `differs` | no record to say who changed it (set up before the record existed) | shows both, in `report` |
| `own`, `edited`, `host-removed` | yours: written, reworded or taken out | leaves it |
| `current` | the same | nothing |

Whitespace alone is never drift. `breaking` is kept apart from all of that: what the plugin would
now misread. That is a config key a release retired (`RETIRED_KEYS` in `sdlc.py` names its
replacement, until the release that drops the note; after it, the key is reported as one the
plugin doesn't read), a template override lacking a heading, frontmatter key or placeholder the script
reads (`TEMPLATE_READS`), or a project or product doc it can't parse: an override of
`retro.md` needs its `## Scorecard` and `## Indicators` sections and `{{scorecard}}` and
`{{indicators}}`, or the next retrospective has no table to compare its scorecard and indicators
with. `report` also lists config
keys the plugin doesn't read, keys new since the record (with their default; this page says what
each does), and plugin templates that changed under one of your overrides.

**`sdlc.py check` is now `sdlc.py vet`.** The command that checks each change folder against its
tier and stage was renamed with no alias: `sdlc.py check` is gone, and argparse refuses it. A
host's CI that runs `sdlc.py check --strict` must run `sdlc.py vet --strict` instead. The skills
call `vet`, so the read-only allow rule `Bash(uv run --quiet --script */scripts/sdlc.py vet *)` is
missing from a settings file written before: readiness reports it under `permissions.missing`, and
setup proposes it on its next run. The old `check` rule allows nothing that exists, and setup
leaves it. The factory's agent that weighs each round's findings is now the arbiter, and
`[models] verifier` is now `[models] arbiter`, with no shim: the old line is an unknown role,
warned about, and the arbiter runs on `[models] arbiter` or its default, `sonnet`.

**`/sdlc:setup reset <doc | template | all>`** puts the default back: a doc with its prompts
filled as a first setup fills them, after a diff of every block of yours it loses; a template
override by deleting it (`sdlc.py reset <name>`, which refuses any other path, and an override with
uncommitted edits).

**`/sdlc:uninstall`** removes what setup wrote: the committed files in `.sdlc/`, the plugin's
allow rules in `.claude/settings.json` (every other key and rule kept), and the
`.claude/worktrees/` line when the record says setup added it. It refuses while a change is open,
stands in a worktree, or is shipped and not closed, and while anything it would remove has
uncommitted edits, so history keeps everything it removes. It leaves `.sdlc/work/`, `AGENTS.md` and
`CLAUDE.md` (listing their lines that name the plugin), the tracker's issues, tags and history,
and commits nothing. A later setup numbers on from that history.

## `.sdlc/work/` and worktrees

**The change folder** is `.sdlc/work/`, beside the rest of what the plugin keeps, so adopting it
adds no top-level folder. Its path is fixed. A repo set up before 1.4.0 has the old `work/` at
its root, which 1.5.0 no longer reads: move it once by hand, from the main checkout on the base
branch with no change open and, if you release, after `/sdlc:release`, as
`git mv work .sdlc/work` in a commit of its own (`Move work to .sdlc/work`). History isn't
rewritten, so release, retro and `bugs --introduced` read only `.sdlc/work/` from then on;
change numbers and register ids keep counting across the move, since they read history at both
names. Moving the folder again isn't supported.

`.sdlc/work/` is committed. A change's folder, `.sdlc/work/NNN-slug/`, lives on its own branch, in its own
worktree (`.claude/worktrees/NNN-slug`), so the session working on it writes its artifacts where
it works, and `/sdlc:ship` commits them with the code: the review reads the spec next to what was
built. `sdlc.py status` lists the open changes in every worktree, from any of them, and marks
one whose branch lacks commits `main` has (`behind main by N`). Since close only fast-forwards,
`/sdlc:ship` brings such a branch up to date before the gate runs (`sdlc.py base`): a
fast-forward that carries the uncommitted work, or a rebase of the branch's own commits from a
clean tree, reported with the command that undoes it. When that would conflict, ship resolves it
in the same run (`sdlc.py resolve`): the uncommitted work is set aside as a commit kept under
`refs/sdlc/aside/<branch>`, the branch rebases, the agent merges each conflicted file so both
sides survive, and the work comes back uncommitted on the new base. The files resolved are
recorded in the change's `conflicts.md` and named in ship's question, and `sdlc.py resolve <NNN>
--abort` puts the worktree back until ship commits. Anything else `base` refuses stops ship,
untouched, for the person. A Tier 1 change that turns out to need a spec is upgraded in place
with `sdlc.py upgrade <NNN>`, from its own worktree, at `stage: plan` or `build`: it sets
`tier: 2` and `stage: plan` by editing those lines, scaffolds `spec.md` and `plan.md` from
your templates where they are missing (a file there already is kept), and refuses on the base
branch, at any other stage, or for a change already at Tier 2. It is one-way: there is no
downgrade. The factory runs it when the person's answer to a blocking decision starts `upgrade
to Tier 2` (`plugins/factory/README.md`). Once a change
lands, `/sdlc:close` takes its folder off `main` in a commit of its own, so `.sdlc/work/` never fills up
with finished changes: the change's commit keeps them in history. `.sdlc/work/inbox.md` is committed
too; a closed seed is deleted from it, history keeping that as well. A change's branch never edits
it, so no landing conflicts on it: what `/sdlc:ship` or the factory's landing files (carried seeds,
bugs, nits, a seed split off an issue) and each nit it retires (a `Retire <id>: <reason>` line) is
held in the change's own `.sdlc/work/NNN-slug/entries.md`, committed with it, and `/sdlc:close`
files those entries and deletes the seed the intent's `idea:` names, the bugs its `fixes:` names and
the retired nits in the change's `Close` commit, under the lock `inbox-commit` takes. Close checks
the file before it merges, and refuses one it can't read or a held id the register holds with
other text; a rerun files nothing twice. `ship` refuses while the register has uncommitted edits,
and `/sdlc:drop` while `entries.md` holds an entry, which a drop would never file. Every entry there is a
seed, and its tag is its kind: `[idea]`, `[bug]` or `[nit]` (the process doc's "Seeds, and the
changes they become" says what each is, and the change types they grow into). Any other tag reads
as an idea, and `[seed]`, what ideas were tagged before they had their own, does so for good.
It was `.sdlc/work/ideas.md` before 1.2.0; since 1.4.0 that file, and a host template
`.sdlc/templates/ideas.md`, are not read at all. `sdlc.py config`'s `work.register` names the
inbox, and every skill that writes an entry writes there, never a second file. The findings `/sdlc:ship`, or the factory's landing, approved unfixed are entries there too,
tagged `[nit]`, each with `Theme:`, `Paths:`, `Cost:`, `Value:` and `Raised by: NNN-slug (pass)`
lines under the process doc's rubric, offered by `/sdlc:intent` and `/sdlc:spec` to a change on
the same paths, retired by the ship whose diff fixes it, and counted by theme and age by
`/sdlc:retro`.
`sdlc.py nits` lists them (`--change NNN` or `--touching <path>…` to narrow), and `check` reports
an entry it can't read.

**Bugs** are entries there too: something shipped and broken, tagged `[bug]`, with `Severity:`,
`Paths:` and, once someone confirms it, `Introduced by: NNN-slug` lines. The severity words are the
process doc's, from the `- **severity:**` bullet in its section headed `Bugs…`, most severe first
(`high` · `med` · `low` when it has none). `/sdlc:bug` files one, retires one that needs no fix
(`duplicate`, `not-a-bug`, `wontfix` or `cant-reproduce`) or retags one filed as the wrong kind,
or, given the path of a report `/sdlc-factory:review` wrote, files the proposed bugs the person
picks from it, each with its own id, behind one approval, and `sdlc.py inbox-commit` commits the inbox alone, on the base branch in
the main checkout, as `File <id>`, `Retire <id>` or `Update <id>`, a retired bug's
`Sdlc-Retired:` trailer saying why. `/sdlc:idea` files, edits or retires an idea the same way,
its reasons `duplicate`, `superseded` or `declined`, written as a `Reason <id>:` line. Both run
from any checkout: from a change's worktree, `inbox-commit <id>` files the entry it names into
the main checkout's register, which must be clean and on the base branch, so it never waits on
the change's branch, and the worktree gets it when it next comes up to date. A nit, or an
entry an open change builds or fixes (its `idea:` or `fixes:` line), is never retired this way.
`sdlc.py bugs` lists them (`--touching <path>…` to narrow), and `--introduced <path>…` names the
closed change that last touched each path, a candidate for `Introduced by:` and never written
without a person's word. `check` reports a bug with no id, a severity outside the words, or an
`Introduced by:` that names no change, and `status` prints a `■ Bugs` line. A change that fixes one
names it on a `fixes: [<id>]` line in its intent (`/sdlc:intent <id>` writes it); `status` leaves
it out while the change is open, `sdlc.py ship` deletes it with the fix, and `/sdlc:close` writes
an `Sdlc-Fixes:` trailer for it on the `Close` commit.

**Issues people file.** With `archive.target = "github"`, anyone can file an issue, and
`/sdlc:triage` reads the open ones that carry neither `sdlc` (a change's own) nor `triaged` nor
`landed`, through `sdlc.py intake`. It checks each against the code and the closed changes, and
after one approval records each issue once, in one of three ways:

- **An entry** carrying an `Issue: #12, #15` line: the issues it was filed from, the first the
  parent of the rest, so a duplicate follows the original. `check` reports a value that isn't
  `#N` and an issue on two entries.
- **A change's `closes: [12]` line**, in its intent, for an issue an open change already covers,
  whatever its kind. `/sdlc:intent` copies an entry's `Issue:` numbers onto the new change's
  `closes:`. `check` reports a value that isn't a bare number, the change's own number, and one
  issue on two open changes' lines. `sync` makes the change's issue the parent of each, and `/sdlc:ship` asks about
  each one before it lands: one the change didn't resolve comes off the line and becomes a new
  seed carrying its `Issue:` and a `Split from NNN-slug:` line. `/sdlc:close` closes the rest:
  a `Closes #N` line on the `Close` commit, or closed at once where no push would, and a failure
  listed under `archive.closes_errors`, never a refusal. A dropped change's issues lose their
  `triaged` label and parent and go back to triage.
- **A verdict that closes it now**, when nothing more will be done: `resolved` (naming the change
  or commit that did it), `wontfix`, `not-a-bug` or `duplicate`. `inbox-commit
  --triaged <N>=<verdict>[:<ref>] --why <N>=<reason>` records each as an `Sdlc-Triaged: #N
  verdict=… ref=…` trailer, on an empty `Triage #N` commit when nothing else changed, and retro
  counts them under `bugs.triaged`.

An issue too thin to judge gets its author asked, by `sdlc.py needs-info`, and the `needs-info`
label; `intake` leaves it out until the author comments. Then `sdlc.py mark-triaged`, from the
main checkout, tells each open issue the repo records where it stands: one comment each, the
`triaged` label, and its parent (the entry's first issue, or the change's issue), closing those a
verdict closed. It reads only what is committed on the base branch and the open changes, so a run
that stops halfway is finished by the next. `/sdlc:close` reruns the marking once the change's
entries are on the base branch. An issue the marking labelled whose record went (an entry's
`Issue:` line removed by hand) goes back to triage, with a comment saying so, unless a commit
the base branch hasn't pushed closes it (every commit on it, with no remote-tracking ref): that
one is left for the push. `intake` lists as `dangling` an issue labelled `triaged` that nothing
records anymore, which includes one whose send-back failed, or that waits on that push, flagged
`waits_on_push` so triage leaves it be (null for each, with `dangling_unread`, when the unpushed
commits can't be read, and triage offers none). `sdlc.py
sync` marks a change's own `closes:` issues as soon as its intent names them, so a filer hears
the change took the issue on, and sends one that left the line back to triage, with a comment saying so, unless another record holds it now.

**What comes next.** `sdlc.py status` ends with a `■ Next up` section: what to start once the open
changes are done, from the main checkout's `.sdlc/work/inbox.md` and direction doc. A
missing file adds nothing. Each entry's heading starts with its id, `## [2026-10-25-3] [idea] Title`:
the day it came in and a count, from `sdlc.py next-entry`, which counts every checkout's register
and every change's `entries.md`, and every commit that ever held either, so an id is never handed
out twice. A heading without its
count, a bare date, is not an entry. An `idea:`, `After:` or `Groups:` line names an
entry by its id, written bare, or by its title, quoted, and titles are read for good, since the
intents in history name seeds by them; `check` reports an id used twice. Two optional forms in
`.sdlc/work/inbox.md` feed it: `[bug]` in place of `[idea]` marks something already broken, and an
`After: <id>, <id>` line in a seed's body makes it wait while any seed it names is still in the
register and not being built. An idea or a bug may also carry a `Theme:` line, as every nit
does, and a `Priority: high|med|low` line (`check` reports any other word, and a `Priority:` on a
nit, whose `Cost:` and `Value:` rank it). Each line's command is `/sdlc:intent <id>`. A seed
being built is never listed: one an open change names on its `idea:` or `fixes:` line, which is
all intent writes for it (the register is never edited on the change's branch, so an inbox commit
on the base branch never conflicts with it), or one carrying the `[building]` tag older versions
wrote. `status` counts them, `status --all` lists each with its change (or `tagged [building]`),
and `sdlc.py bugs` and `sdlc.py nits` give each entry a `building` key, the open change's folder
name or null.
Candidates come in this order, each once, under the first rule it meets:

1. ideas and bugs marked `Priority: high`, bugs most severe first, then oldest (`priority high`);
2. `[bug]` entries, most severe first, then oldest;
3. each open milestone's first `Groups:` seed that is ready, in the doc's order;
4. a seed whose `After:` seeds have all left the register, the next in its series;
5. nits of cost `S`, one line per theme, oldest theme first;
6. every other ready idea, oldest first (`idea`);
7. ideas and bugs marked `Priority: low`, oldest first (`priority low`).

An entry with no `Priority:` line, or `med`, ranks as it would with none. The first five rules are
**Ready to build**, what a person or a review already weighed, and the last two **Needs a
decision**, the seeds no one has ranked, with its `Priority: low` ones counted; status prints them
under those two headers, ready first. Ten are shown across both, each with
its `[theme]`, then a count, and `status --all` lists every candidate, grouped by theme, with
`/sdlc:intent <id> <id> …` under a theme holding two or more ideas: one change that takes them all
writes every id on its `idea:` line, `idea: [2026-10-24-4, 2026-11-12-2]`, and ship deletes each.
Several changes open from one run as a batch, its groups separated by `;`, each `<id> … as <slug>
tier <1|2>`, with `after <slug>` for one that waits on another group and `— <words>` for the
person's own: `/sdlc:intent 2026-10-24-4 2026-11-12-2 as keep-drafts tier 1; 2026-11-14-1 as
reopen-drafts tier 2 after keep-drafts`. `sdlc.py groups`, which writes nothing, reads the groups
against the register and the open changes, refuses an unknown or taken id, a shared slug, an
`after` naming no group and a cycle, and gives the creation order; intent drafts every change,
asks one question for all, and creates them in that order, each `depends_on:` the number `new`
gave the change it waits on. The session stays where it started, and the same command run again
after a stop makes only what it didn't.
Below
them, `Themes:` counts each theme's open entries by kind (nits of every cost included), the theme
with the best-ranked line first and `(no theme)` last, then how many seeds wait on an `After:`.
With five or more open ideas and bugs lacking a `Theme:`, a line names `/sdlc:idea --themes`, which
proposes one for each behind a single approval, from the main checkout, and commits them as one
`Update <id>, …`.
An open milestone whose grouped changes and seeds are all closed says so, for `/sdlc:retro` to
settle, and an `After:` line that can never be met (it names nothing, or seeds that wait on each
other) is a `⚠`, never a `check` problem.

Each open change's line ends with when it was last touched: its branch's own last commit, or the
newest file its worktree has changed. One untouched for a day is `quiet`, and `/sdlc:status`
recommends finishing an open change only once it is: one touched since has a session on it. A
factory run its supervisor stopped (`runs/stopped.md`, at `stage: build`) reads `stopped` in place
of `quiet`, with each problem on a `⚠` line and the step that moves it on, ship it by hand or rerun
`/sdlc-factory:build NNN`, on a `→` line under its title.

`status` groups the open changes by the board's columns (below), in its order, by the same rule
(`column()` in `sdlc.py`, which the board calls): `■ Planned`, `■ Designing`, `■ Building`, `■ Ready`
and `■ Landing`, each with its count, and one with nothing under it printed alone. `Landing` lists
each shipped or dropped change waiting on close, a stopped rebase's included, on a `→ /sdlc:close
NNN` line, and a factory landing in flight on its change's line.

`status` ends with `■ Needs you`, the board's sixth column: each change waiting on the person, its
line, and under it a `needs you:` line saying what it waits for, or `nothing` when none is. The
texts are the board's (below), read by the same rules: `fix:` and
each problem, at any stage; at `build`, a stop's way on in plain words (`stopped: fix its cause and
rerun`, `stopped: rerun to ask an agent again`, `stopped: review an agent's commit`, or `stopped:
read runs/stopped.md` for a record that won't read) and `decide D<n>` for each unticked blocking
decision; for an ESCALATE at `test`, `decide D<n>`, `confirm N defaults`, `reconsider the
approach` (its `decision.md` holds that section), `acknowledge D<n>` for each `look` the approver
escalated for (`- ESCALATED: look: <what to look at> — <why>`, filed in the ledger as
`(approver round <R>, look)`, its decide question quoting the target before ` — `),
`gate it green` while a `gate` reason (`- ESCALATED: gate: <why>`) has no green hand gate on the
change as it stands (below), and, with no such reason and no decision line at all in its ledger,
`read the escalation` (a default the approver settled, `→ settled by the approver:`, is no decision
line here and never counted as an answer, nor as a default to confirm), the line ending with
`/sdlc-factory:decide NNN`, where the person answers them one at a time, while it holds a
decision, a default or a look; `landing stopped at <step>` for a factory landing that stopped
(`runs/land-step.md`), at `test` before its commit or on a shipped change, whose Landing card says
so too; and `approve its spec` for a Tier 2 at `plan` whose `spec.md` is written
but whose stage never moved. `status` reads the board's reading of a landing (`runs/land-step.md`,
whether it is in flight and whether its record reads), but no more, so a problem only the board
finds (a reply that isn't a review, a findings file that won't read) is on the board alone, and
that change is under its stage's state in `status`.

**The board.** `/sdlc:dashboard` runs `sdlc.py board [--port N]` (5170 unless named), which serves
the same open changes as a live page on `127.0.0.1` until it is stopped, in columns that name the
state of the work, the same for a change built by hand or by the factory: **Planned** (an intent,
nothing built), **Designing** (a Tier 2's spec, a factory change at `stage: plan` included while
its spec-writer runs or its draft waits for the yes, its `stage:` untouched), **Building** (code being written, by hand or in
the factory's rounds), **Ready** (built and checked, nothing committed: a factory change the
approver called READY or whose escalation is answered, or a change built by hand whose review is
written or whose gate is green), **Landing** (committed and on its way to the base branch: shipped
or dropped and waiting on close, or a factory landing or train in flight), and **Needs you** for
one with a file that won't read, at any stage, or whatever else it needs from the person, each
card naming it on a `needs you:` line (the texts `/sdlc:status`'s `■ Needs you` gives, above):
a run that stopped or a blocking decision at `build`, an ESCALATE at `test` while its ledger holds
an unticked line, a look is unacknowledged, a gate reason isn't green, it asks to reconsider the
approach, or it holds no decision at all, a landing that stopped, before its commit or after, and
a written spec waiting on its approval. Each card's `next:` line names its own tool's command.
An escalation whose every reason is cleared (each ledger line ticked, each look acknowledged in
`/sdlc-factory:decide`, each gate reason by a current green hand gate) moves to Ready, badged
`escalated: answered`, its `decision.md` never rewritten: the landing still asks, and shows how
each reason was cleared; an open `- [ ]` line the ledger can't read is a problem, so it never
counts as an answer. The stage is the only mark that the person has answered a stop or a blocking decision, so a change they shipped,
dropped or put back to `build` leaves Needs you for the column that answer leads to, whatever the
run's files still say; one sent back to the factory keeps its old decision as `decision-<n>.md`, a
file of its folder, and is in Building again. A change built by hand moves on from its `stage:`
line by what it has touched: to Building once its branch or worktree changes a path outside
`.sdlc/work/`, to Ready once ship's review has written its `findings.md` or its gate run by hand is
green on the build as it stands (below), never while that record is current and red, with a
`gate green` or `gate red` badge while it is current, and beside it what the gate ran and how it
ended, from the record: its command, the last line of its output holding a test runner's count (on
red with none, its last line), and its exit, as `./check.sh: 3309 passed, exit 0`. A card with
acceptance checks says how many (`acceptance: 2`), and once a factory landing has run them, how its
last run went (`acceptance: 2, passed`).
A change whose worktree is stopped mid-rebase (by `resolve`, or a landing) keeps its card, shipped
or not, with a
`rebasing` badge, its branch read from the rebase's own record, and `sdlc.py resolve`'s
`--continue` or `--abort` as its next step, saying that `--abort` keeps the resolved work under
`refs/sdlc/end/<branch>`; a factory landing whose agent is resolving the conflict says so, its
next step to wait for it, or `/sdlc-factory:land NNN` if its session ended. A card with a file
that won't read names that as its next step, at any
stage. Its next step follows its `needs you:` line: a decision still to make (`decide D<n>`) is
named first, before the problem a card also has; on an escalation at `test`, a decision or
default to confirm makes it `/sdlc-factory:decide NNN for D2 and 1 default`, then `/sdlc:ship`; a blocking decision at
`build` names the session running `/sdlc-factory:build NNN`, which asks it again when rerun. A stop
record that won't read is a stop, its next step `read runs/stopped.md`, on the board as in
`/sdlc:status`.
Each card gives the change's tier,
artifacts, open questions, undone notes, findings, how far behind `main` it is, when it was last
touched, and the command to run next; a change the factory ran on (its folder holds `runs/`) adds
each round's verdicts, the arbiter's answers, its decisions and what its agents cost, each build
round labelled `B<n>` (a landing's `L<n>`), and a step
track of the round under way (build, gate, reviews *n/m*, arbitrate, rework, approve) read from the
`runs/step.md` its supervisor's `verdicts --record` writes; a run that stopped early reads
`approve (stuck)` or `(untestable)` there, each reason a line on the card. The current step shows how long it has
run against the median time that step took at that tier in the last 20 closed factory changes, a
bar labelled an estimate that never fills past 95%, or its elapsed time alone with fewer than 3 of
them; a Tier 2's card adds how many of the files `plan.md`'s `## Files to change` names its branch
has touched (so an overriding `.sdlc/templates/plan.md` keeps that heading). A change the factory
is landing shows the landing's track instead (its acceptance checks or cases, then ship, rebase,
resolving, stacking or waiting, gate, acceptance run again after the commit, review, arbitrate,
close), from the
`runs/land-step.md` each landing command writes as it starts its step: the landing round, how
often the base branch has moved out of `[land] moves`, a change's place in a train (`2 of 3`) and
what it waits on there (`waiting to stack on 140`), the current step timed against closed
changes' landings (each step's time is kept in `runs/land-times.jsonl` as the next replaces it),
or, for a step with no history or one that is open-ended (a conflict, a fix, a mend, a paid case
run, a turn in a train), its elapsed time and `running`, never a made-up bar; and a stopped
landing marked at its step with why, in Landing before its commit and after. Its next step names the landing, not
`/sdlc:close` or `/sdlc:ship`, while it runs; once it stops, the card is in Needs you (`landing
stopped at <step>`), each reason a plain line with the tool's own words under it, and names the way
on: fix what it names, then `/sdlc-factory:land`, or by hand `/sdlc:ship` before its commit and
`/sdlc:close` after. After the landing's yes no session acts on it: `factory.py train --run`,
started in the background by `/sdlc-factory:land`, takes each step itself, ejects a change the gate
found at fault and lands the rest, and stops at any other ejection, a train stop, checks to run
again as stacked or a refused push, recording the stop and the way on in the change's
`runs/land-step.md`. One loop runs at a time, under a run lock in the git common dir
(`sdlc-factory-train-run.lock`), and `train --cancel` stops it after the step in flight. While
a loop holds that lock, each train card not stopped says `running unattended: train --run takes
each step`; the board reads the lock only while a train card is under way, opening it read-only
and never creating it, and `runs/land-step.md` alone never claims a live loop. A
click opens
any file in the change's folder, a markdown file rendered (its text never parsed as HTML; a link
followed only to the web, in a new tab, or to another file of the change) with a `Raw` toggle for
its exact text. It writes nothing, answers only `GET` for the page, `/state.json`
and `/file` (one file inside the folder of a change it shows), refuses a request naming another host,
and a second `board` on a port this repo's board holds says so rather than starting again (each
board's `/state.json` names its repo by a hash of the main checkout's path, never the path);
another repo's board on the port, or anything else, is a refusal naming the port. `--port 0` takes
a port the OS picks, and prints it. A running board serves `board.py` as it is on disk, loading it
afresh when it changes, so a change to the board that lands needs no restart; a file that won't
load leaves it serving the code it had, and the page says it is stale. The page polls every two
seconds but rebuilds only when what it shows has changed, and puts focus back on the card that
held it when it does; its one live region is the status line (`live`, `live · N need you`, or that
the board isn't answering), with the time of the last poll beside it.

**The gate, run by hand.** `sdlc.py gate NNN` runs the base branch's `[commands] check` (never the
checkout's, so a change can't edit the gate that judges it) from the change's checkout, for up to
30 minutes, and adds the attempt to `.sdlc/work/NNN-slug/build/gate.md` in the factory's gate
record's shape: a first line `GATE: PASS` or `GATE: FAIL` for the latest attempt, then one
`## Attempt <k>` section each with its `Verdict:`, `Command:`, `Build:`, `Exit:`, `Seconds:` and
`Tree:` lines and the last 80 lines of its output, the main checkout and the change's checkout
written `<path-to-clone>`, the home directory `<home>` and the temp directory `<tmp>`, and the login
name `<user>` inside any such path (pytest's `<tmp>/pytest-of-<user>/…`), never in prose. PASS only
on exit 0, in time, with every path
the build covers as it was. `Build:` is a hash of where the branch left the base branch and the
content of every path it changed since (committed, uncommitted or untracked, outside `.sdlc/work/`),
so committing the same work keeps a record current, and any other edit, or a rebase onto a moved
base, makes it stale. It prints a JSON summary and exits 0 on PASS, 1 otherwise, and refuses a
factory run still building (its folder holds `runs/`, at `design` or `build`; `factory.py gate`
gates it), a checkout not on the change's branch, and a base branch with no check. A factory run at
`stage: test` it gates like any change: its record is no round's, never counted as the factory's
gate, and while it is current and green it clears the approver's `gate` reasons. It is the person's step after building, never
pre-approved, since it runs a command: no skill runs it, and ship's own gate is unchanged. The board
and `/sdlc:status` read the record (`· gate green` or `· gate red` on the change's line) only while
it is current, and ship commits it with the change's folder. While `sdlc-factory` is enabled,
the hand gate shares the factory's gate slots (`gate_jobs`, read from the base branch's
`.sdlc/factory.toml`, 1 by default), so a hand gate and the factory's gates never run more checks
at once than that. A hand gate that finds every slot taken prints `NNN-slug: waiting for a gate
slot (1 of 1 in use), up to 30 minutes`, and its wait is not in its `Seconds:`; when no slot comes
free in 30 minutes it refuses with `no gate slot came free in 30 minutes (…): nothing was judged,
run it again`, exits 1, and leaves the record as it was. Without the factory it takes no slot.

A change may keep its **acceptance checks** in `.sdlc/work/NNN-slug/checks.md`: proof that only a
deliberate revert could break, which the suite shouldn't carry forever. Each `## ` section is one
check holding one `sh` block, which passes when it exits 0 within 300 seconds and leaves the
working tree as it found it. `sdlc.py checks NNN` lists them and runs nothing; `sdlc.py accept NNN`
runs each from the change's checkout root. `/sdlc:ship` lists them after the gate, shows each
command, then runs `accept`, which no skill and no setup allow rule ever pre-approves: an agent may
have written them, so a person sees them and answers the prompt. A failing check stops ship like a
failing gate. The file reaches history and the change's issue with the folder; a check that can't
run (looking at a rendered page) is written in `notes.md` instead.

Ship's review writes what it found to `.sdlc/work/NNN-slug/findings.md`, after every run, one
that stops on an Important finding included: the one file, besides bringing the branch up to date,
ship writes before it asks, since it holds no decision and the next run rewrites it. Each finding
is a `## F<n>. [rank] [pass] title` section, its rank `important`, `nit` or `pre-existing` (a fault
in lines the diff didn't touch, which never blocks the change and is filed as a `[bug]`), with
its `Evidence:` (`path:line`), `Class:` and `Disposition:`: `open` until it is answered, `fix`
when ship recommends fixing it before the commit (a change of cost S in files the diff already
touches, said on a `Fix:` line), then `fixed`, `recorded` (as a nit or a bug), or `wrong`,
`intentional` or `minor` with a `Reason:`. A rerun keeps each id, marks one the diff no longer
shows `fixed`, and never raises again one the person dismissed. On a diff that touches a sensitive
path, the file's note says `Fresh review: ran` or `Fresh review: skipped, <why>`. Each of ship's
further passes that applies (*Risky paths*) adds its own line, `ran` or `skipped, <why>`:
`Security review:`, `Behaviour check:`, `UI review:` and `UX review:`. A behaviour check that ran
ends the file with an `## Evidence` section: each command on a `$ ` line, the tail of its output,
then `exit: <n>`. `sdlc.py findings` reads it as evidence, never as a finding, and reports a
command without its `exit:`, or `Behaviour check: ran` with no command. A finding's `By:` line names
who raised it: none on ship's own, `fresh` for the fresh-context reviewer, `ship-security`,
`ship-behaviour`, `ship-ui` or `ship-ux` for ship's further passes, or a factory role (`code`,
`security`, `test`, `behaviour`, `ui`, `ux`). A factory run writes its agents'
findings into the same file (`factory.py carry`, at its approve step, and its landing's review
rounds at `land --close`), each with its role's `By:`, and ship keeps those sections as they are
and numbers its own after them. `sdlc.py findings NNN`
reads it and prints the counts of ship's own, the agents' as `agents`, and the `Sdlc-Findings`
line the commit carries; `sdlc.py ship` refuses while a finding is `open` or `fix`, a deep
diff whose note says neither, and a pass that applies whose line is missing. The file reaches history and the change's issue with the folder.

The guide's *Review dimensions* list what a review covers and who covers each in a ship and in a
factory run, a way that leaves one uncovered saying so.

Ship's question leads with its recommendation, so `yes` always takes it. `sdlc.py preflight NNN
--question` words it from `findings.md`: `Commit this, …? (yes / edit the message)` when nothing is
proposed; `Fix F2 and F4, then commit this, …? (yes / fix all 5 first / commit without fixing,
recording F2 and F4 as nits / edit the message)` when some are, a yes making those fixes, rerunning
the gate and the review, and committing only when `sdlc.py ship NNN --fixed F2,F4 --through F5`
finds each `fixed` and nothing new; and `Fix F1, then review again? (yes / fix all 3 first / edit
the findings)` while one is `open`, which commits nothing. `fix all N first` is there only when more
could be fixed than ship recommends, and fixes them all, then asks again; `commit without fixing`
only when every `fix` finding is a nit.

Ship asks it, as every skill asks its approval, in an `AskUserQuestion` dialog: the text before the
parentheses is the question and each answer in them an option, in order (publish's put `no`
first). Only a chosen `yes`, or a yes typed in Other, approves; a dialog dismissed or timed out
writes nothing. Where no dialog can be shown, as in a non-interactive run, the same question is
asked as text.

`/sdlc:ship` reads all of this in one call, `sdlc.py preflight NNN`: the change's undone notes,
the nits its diff touches, the issues on its `closes:` line, its acceptance checks, its earlier
findings and the context docs its diff could have made wrong, each part as `undone`,
`nits --change`, `closes`, `checks`, `findings` and `context` give it, then `branches`, the files
beside ship's skill those parts call for, which ship reads and no others. It writes nothing, and
setup's read-only rules allow it, `nits` and `findings` too.
`preflight NNN --question` words ship's approval question from what its review decided
(`--context`, `--nits`, and each issue on `closes:` once as `--closing N` or `--split N`), and
refuses an issue left out.

`.claude/worktrees/` belongs in `.gitignore`, and `.sdlc/work/` must not be in it: `sdlc.py new` refuses
an ignored `.sdlc/work/`, and `sdlc.py vet` flags it. The main checkout stays on `main`: close
fast-forwards it there, and refuses while it is on another branch or has uncommitted changes.

## Numbering

`/sdlc:intent` settles a change's number before its folder, worktree and branch exist, all named
after it.

- **From GitHub**, when `archive.target = "github"`: the change's number is the issue
  `/sdlc:intent` opens for it, labelled `sdlc`. GitHub hands each number out once, so two people
  or two machines can never collide. Issues and pull requests share the sequence, so numbers run
  `142`, `157`, `1203` rather than one after another. Never a local number instead when GitHub
  can't be reached: `new` refuses.
- **From a counter**, otherwise: `.sdlc/last-id` holds the last number handed out, and is
  committed. `new` writes it in the change's own worktree, so it reaches `main` with the change's
  commit. Until then `main`'s counter trails what is open, so a number is one past the highest of
  the counter, the folders in `.sdlc/work/` and the open change worktrees, claimed under a lock
  (`sdlc.lock` in the repo's git dir, which every worktree shares and `git status` never shows). A change
  removed by hand before it reaches `main` frees its number; one dropped with `/sdlc:drop` keeps
  it, since its `Drop` commit brings the counter to `main`. A fresh clone carries on from the
  committed counter. Two changes open at once both edit it; the second to close rebases and keeps
  the higher number. This only numbers safely on one machine: two machines that take the same
  number offline write the same line, which merges without a conflict.

The tracker decides: GitHub numbers its changes, and every other target (`none`, the default, and
`command`) numbers them from the counter. An issue whose number a local folder already holds is
refused. IDs are at least three digits.

## Trackers

The change's own commit is the copy that counts; a tracker is where people read it, and it is
optional. `archive.target` chooses one, loaded only then: with `none`, no tracker code runs and
nothing needs `gh`. Only Tier 1 and 2 changes reach one: Tier 0 has no folder and no issue.

- **`github`**: one issue per change, labelled `sdlc`, `tier: N`, `stage: <stage>`
  and, once ship settles it, `impact: <impact>`, and assigned to whoever opened it. The body is
  rendered from `templates/issue.md`: a table of the frontmatter, the intent's Problem and Outcome,
  then each artifact in its own collapsed section. It is rewritten after the approvals of
  `/sdlc:intent`, `/sdlc:spec` and `/sdlc:ship`, so it shows the change as it is, its title the
  intent's heading without the number; edit the artifacts, never the issue, which the next sync
  overwrites. A change listed in the intent's
  `depends_on:` line shows as blocking it. `/sdlc:close` renders it a last time, labels it
  `landed` and reads it back before it removes the folder. The issue stays open until the change is on GitHub: the `Close` commit
  says `Closes #N`, so GitHub closes it when that commit reaches the default branch, by close's
  own push (`[git] push`, on by default with GitHub), `/sdlc:publish`, a push of your own, or a
  merged pull request. Where the default branch isn't
  `main`, close closes the issue itself and says why. An artifact too long for the body becomes a
  comment. A dropped change's issue is closed as not planned. Each issue on the intent's
  `closes:` line is a sub-issue of the change's, so the person who filed it follows the change;
  one triage recorded that leaves the line is let go, and one a person added stays. The labels
  `triaged` and `needs-info` are triage's, never removed by sync. Setup offers a repo on GitHub
  two issue forms, `.github/ISSUE_TEMPLATE/sdlc-bug.yml` (with a severity dropdown from the
  process doc's words) and `sdlc-request.yml`, which are the repo's once written.
- **`command`**: the repo's own command (`archive.command`) archives the folder at close. It has no
  live view.
- **`none`**: nothing is mirrored, and the folder still goes: history has it.

## The project doc

`docs.project` (`.sdlc/PROJECT.md`) is for a repo whose issues follow its own project
management. While it doesn't exist, a change's issue gets the plugin's labels and its opener as
assignee, nothing more. Its frontmatter turns on the fields it names, and says where each one's
values come from:

```yaml
---
milestone: tracker               # the tracker's own list: GitHub's open milestones
project: [Roadmap, Ops]          # a fixed list: only these
assignees: ./scripts/team.sh     # a command, run from the repo root, printing one per line; {field}
---
```

Its body is prose on how to choose: which milestone a change goes in, who owns what.
`/sdlc:intent` reads it, offers only the values `sdlc.py lookup` lists, and writes the answers
into the intent's frontmatter (`milestone:`, `project:`, `assignees:`). `/sdlc:spec` may revise
them. `sdlc.py vet` reports a field the doc doesn't turn on, and a value outside a fixed list;
it never asks the tracker, since the gate is offline.

A field the doc turns on is mirrored **exactly**: the intent decides it, and the issue is made to
match, so a person the intent doesn't list is unassigned, its opener included. A field it doesn't
turn on is never read or written. Each field is set in an edit of its own, so one GitHub refuses
(projects need the `project` scope, listing them `read:project`) is reported and the rest still
land. `/sdlc:setup` drafts the doc from `defaults/PROJECT.md` when you say a team runs the repo and
tracks changes on GitHub, with `assignees: tracker` on and the other fields asked about; one
person, or a repo tracked locally, gets none. `/sdlc:setup project` drafts it later.

## The product doc

`docs.product` (`.sdlc/PRODUCT.md`) is for a repo that wants its retrospectives to ask whether the
work is the right work, not only whether it was done well. While it doesn't exist nothing below
applies. It says who the users are, the problem the product solves for them, the bets it rests on,
and its **outcomes**, each with how it is measured:

```markdown
- O1. **Unaided setup.** A new user finishes setup without asking for help. Measured by: setups finished / started
- ~~O2. Exports open in a spreadsheet~~ Done: no failed-export reports since 1.4.0
```

The plugin reads only those ids and the short name in bold after each, the way it reads the
direction doc's goals and milestones: an outcome ends struck as `Done`, `Dropped: <reason>` or
`Revised → O5: <reason>`, never silently gone. Every open outcome needs a name, two or three words
a person remembers: the skills show it beside the id, `O1 (Unaided setup)`, and `sdlc.py config`
reports an open outcome without one. The rest of the doc is prose for people.

With a product doc, every open change's intent says what it serves: `serves: [O1]`, or
`serves: none` for a change that serves no outcome on purpose (a refactor, process work).
`sdlc.py vet` reports a missing line and an id the doc doesn't have. Each change is held to the
product doc on its own branch, so changes opened before the doc landed owe the line only once they
rebase onto it. `/sdlc:intent` proposes the line in its draft, from the open outcomes only, and
names them in its question, so the yes is the person's choice. Each one served gets a line in the
intent's Outcome saying what should change for users if it works:
`- **Moves O1:** setups finished rises above half`.

`retro.evidence` names commands, run from the repo root by `sdlc.py retro` only (never by
`check`), that print what users did: counts and summaries, never anyone's personal data. Each gets
60 seconds and its first 20,000 characters are kept; one that fails is reported, never fatal. The
retrospective's product pass reads them beside what each change served and should have moved, and
which release first held it, scores every open outcome, and its one approval covers the product
doc's outcome lines as well as the direction doc; it never edits the doc's prose.
`/sdlc:setup` drafts the doc when you say the repo is a product: it interviews you for the users,
the problem and the outcomes, proposing each from the repo, then asks for the evidence commands.
A lightweight repo gets none. `/sdlc:setup product` drafts it later.

## Releases

The change loop runs once per change; the release loop runs after a batch of them, from the main
checkout. Each change settles an `impact:` at ship, as seen by someone holding the previous
release:

| `impact:` | The person holding the previous release… |
|---|---|
| `major` | has to change what they do: something renamed, removed or moved |
| `minor` | can do something new |
| `patch` | does the same things, working or described better |
| `none` | receives nothing different: tests, tooling, anything outside what is released |

**When one is due.** `sdlc.py status` shows **Release due** once the unreleased batch holds a
`major` change, `release.due_after_changes` changes of impact `minor` or higher (5 by default), or
a change closed `release.due_after_days` days ago or more (14 by default); 0 turns either count
off. Below that, *Unreleased* lists the batch and says how far it is from due, and
`/sdlc:status` recommends what's next instead. It is a nudge: `/sdlc:release` runs whenever you
choose. A host reading the plugin from a clone has every landed change already, so the release is
for everyone else and for the version's record.

`sdlc.py unreleased` reads them back from history: every `Close NNN-slug` commit since the tag of
the version the repo is on, and the change's own commit before it. `/sdlc:release` proposes the
version they add up to (the highest impact; below 1.0 a `major` is released as `minor`), and
after one approval sets it in `release.version_files`, adds the notes to `release.changelog` if
set, runs `release.after_bump` if set (a lock file regenerated from the new version, which can't
be a version file when it holds a `version` line per package), commits `Release X.Y.Z` with
every tracked file that changed, and tags it, all locally. The command must leave committing and
pushing to the plugin; a new untracked file it makes is listed, never committed. Then it runs
`release.prepare` if set: a build of what publish will upload, which must change no tracked file
(one it changes is put back and the release refused), and the end of whose output is kept on the
tag as a git note (`refs/notes/sdlc-prepared`). Until it is
published, `git tag -d <tag> && git reset --keep HEAD~1` takes it back. `/sdlc:publish`, behind an approval
of its own, pushes `main` and the tag release didn't, never forced, and runs `release.publish` if the repo has
one, showing at that approval what `release.prepare` built. Every command release and publish
run (`after_bump`, `prepare`, `publish`) runs non-interactively, with no terminal, stdin closed
and its output captured: one that asks a question fails at once, so give it its non-interactive
flag, or build in `prepare` and keep `publish` to the upload. Once the tag is on the remote,
publish pushes what landed on `main` since, alone. A repo without a tag for its current version
is told the `git tag -a` command that makes one; a repo with no `version_files` gets the listing
and nothing else. Dropped changes are never released.

**Version files.** Each holds exactly one version line, the key opening the line: JSON's
`"version": "1.2.0"`, TOML's `version = "1.2.0"`, or Python's `__version__ = "1.2.0"`. Release
changes only the value and keeps every other byte. When no tag exists for the current version, the
`git tag -a` hint names the last commit that changed the version files. If the plugin was adopted
after that commit, it names the adoption commit instead: the first commit to add
`.sdlc/config.toml`. That way the first release doesn't take in every change closed before the
repo used the plugin. Only a tag that `release.tag` makes from a version is read. A tag outside
that pattern is outside the loop: it is never a boundary, and nothing since it is counted by it.

**The changelog.** By default each release's section goes at the top of `release.changelog`,
under its `# ` title when it has one. A changelog that opens with prose, a table or a Keep a
Changelog `## [Unreleased]` section marks where releases go with a line of its own:

```markdown
<!-- sdlc:releases -->
```

Release puts each new section right after the first such line, with one blank line on either side.
Everything above the marker, and the marker itself, is kept byte for byte. The section is rendered
from the `changelog.md` template (*Templates*), so `## [{{version}}] - {{date}}` there gives Keep a
Changelog's heading.

**Publishing.** The tag's message holds the release's notes, so
`publish = "gh release create {tag} --notes-from-tag"` makes a GitHub release that carries them.
`release.prepare` can also show what a push will upload without building anything:
`prepare = "git lfs push --dry-run origin {tag}"` lists the large files, and publish's approval
shows that list.

Publish marks a tag `published` in `refs/notes/sdlc` once `release.publish` succeeds, so a rerun
skips the upload. After that mark, publish pushes the notes ref to `release.remote`, never forced,
and reports it as `push notes`. Before its steps run, publish fetches the remote's notes into
`refs/notes/sdlc-remote` and merges them into its own. So a second clone skips an upload another
clone already made. A refused notes push (`notes_push_failed`) doesn't fail the publish, but until
it succeeds, another clone may run the upload again. A failed fetch (`notes_fetch_failed`) leaves
publish with this clone's notes alone. Without `release.publish`, no notes move.

**Shims: `release.deprecations`.** A shim is code kept working for something older: an old key
still read, an old name still accepted. Each one the repo keeps is a `[[shim]]` in
`.sdlc/deprecations.toml`, with the release that drops it:

```toml
[[shim]]
name = "old-flag"                                  # unique
remove_in = "2.0.0"                                # quoted X.Y.Z
where = "src/config.py"                            # where the shim is
test = "tests/test_config.py::test_old_flag_reads" # optional: the compatibility test that goes with it
```

`sdlc.py unreleased` lists each shim as `overdue` (the current version still carries it), `due`
(the next release would) or `unversioned` (no `version_files` to compare with). `/sdlc:release`
refuses to cut any version at or past a shim's `remove_in`, a `--version` included, until the shim
and its test are gone and the entry with them. `/sdlc:status` shows the overdue and due ones under
*Unreleased*; it never counts them as problems, so `vet --strict` still refuses only on the change in
hand. A bad entry is reported, and blocks a release, rather than raised. Without the file nothing
changes. A path kept for good (the no-manifest drift, and whatever reads what history holds,
which never migrates) is not a shim and has no entry.

## Retrospectives

`sdlc.py status` says **Retro due** after `retro.after_releases` releases since the last one (2
by default), or after any major release, and never runs it for you. `sdlc.py retro` counts, from
history, everything since the last `Retrospective YYYY-MM-DD` commit: the changes closed and
dropped (tier, impact, size, days open, the first paragraph of each problem, what they cost),
rework (each change that fixed an earlier one, as declared on its intent's `reworks: [041]` line
or by a fixed bug's `Introduced by:`, with `rework_questions` beside it: lines an earlier change
wrote that a later one replaced, found by blame and asked about, never counted), open changes and
seeds, release tags, the size of each skill, and what each change cost, from its `Close` commit's
trailers. Its `bugs` are the bugs reported, fixed and retired in the window, by severity and
reason, the issues triage closed without a change by verdict (`triaged`), the days from report
to fix, the open ones by age, and the escapes: each introducing change with its tier, its `way`
of building (`unknown` when history doesn't hold it), its bugs
and their paths (`escaped`), and the review it got (`review`): `state` is `file` when its
`findings.md` is in history, each finding marked `on_paths` when its `Evidence:` sits on a bug's
paths (null when they weren't recorded), `trailer` when only the `Sdlc-Findings` counts are, and
`unknown`, never a clean review, when neither is. Then how many no one tied to a change
(`unattributed`); `rate`, the escapes per closed change in this window (with `window.by_way`,
the same rate for each way: the bugs whose introducing change was built that way, over that way's
changes closed in the window, null with none) and the one between the
two retrospectives before it, by the bugs' reported dates, with a `trend` of `up`, `down`, `flat`,
or `unknown` when either window has fewer than five closed changes; and `important`, the window's
Important findings with their class, beside `important_unknown`, the changes with no
`findings.md`, or one that no longer parses, whose review's `problems` say which sections, each
with its `by`. `review_sources` compares the two ways of building from the one record: for each
source (`ship`, `fresh`, then each factory role) the findings by rank, those answered `wrong`, and
the changes it reviewed, counted from every `findings.md` in the window; a change with none read
is in `review_unknown`, never a review that found nothing. The report gives one line per source.
`landing_catches` says how often a factory change's landing caught what its build rounds passed:
`reviewed`, the window's changes with any finding a factory role raised, and `caught`, those of
them with an Important finding a landing round raised, fixed or recorded, each change once. The
report gives it as `Landing catches: <caught> of <reviewed> factory-reviewed changes`.

`process.lead` is lead time from each change's `Sdlc-Lead` (see *Metrics*): per tier and way of
building, the changes, the median and the 85th percentile (nearest rank); each part's `share`,
its sum over the changes that recorded it against their leads' sum, with how many `changes` that
is; and `measured` and `unmeasured`, the changes with and without the line, which move no figure.
`ways` gives the count, median and 85th percentile for each way alone, over every tier. It sits
beside `process.cycle`'s `elapsed`, which is unchanged, and the report shows it under the *Cycle
time* table. Each week of `process.throughput` counts its changes by tier, by way (`ways`) and by
work class (`classes`, `unclassed` for a change no rule classed), every key given with its 0, and
the report's throughput table shows the last two beside *Tiers*.

`by_way` compares the factory's changes with the person's. A change's way is its `Close` commit's
`Sdlc-Mode` alone: `factory`, `manual`, or `unknown` when it records none, never guessed from its
folder; so a change the factory built and the person shipped by hand is `factory`. Each of
`changes`, `lead` (`process.lead.ways`), `throughput` (each way's `closed`, the window's `weeks`
from `since`, or the first close, to today, and `per_week`, null with `why` `window under a week`
when the window spans fewer than seven days, where a day's changes would read as a week's), `cost`
and `escapes`
(`bugs.rate.window.by_way`) gives all three ways. `cost` gives each way `tokens`, the median of
`in + cache_read + out` over its changes whose totals came from transcripts, and `usd`, the median
dollars over its landed changes with `costs.jsonl` dollars, each with its `n` and
`missing_because`: a hand-built change has no dollars and is counted `built by hand`, never $0.
Tokens are measured the same way on both sides; dollars are never priced from tokens. The report's
*Speed* section holds a *By way of building* table of these, columns *Factory*, *By hand* and
*Unknown*, each figure followed by its `n` in brackets and `–` where it is null.

Three figures say whether the work was aimed right, each with its `n` and what it left out,
never a zero for missing data, and the report gives one sentence each, opening its *Scorecard*
(the Value band), from the
same function as the JSON. `work_mix` classes each closed change once, as its record's `work`
(`class`, the signal it was classed `by`, and `also`, the other classes whose rules applied):
`fix` when its intent's `fixes:` names a bug, its `reworks:` names a change, or a seed its `idea:`
names was a `[bug]` in the register at its base; else `capability` for `impact: major|minor`;
else `process` when every path it touched, past the change folders and the register, is under
`.sdlc/` (setup's `.sdlc/setup.json` included) or is the configured process, review or policy
doc; else
`debt` for a seed that was a `[nit]` or has a theme among the guide's nit themes (`docs`,
`refactor`, `robustness`, `tests`, `style`), or `impact: patch|none`. It counts each class and its
share of `n`, the changes classed; `unmeasured` are those no rule classes (an unreadable impact
and nothing else), in no share, and `mixed` those with an `also`. `time_to_users` is the median
days, to one place, from each change's `Close` commit to the creation of the first release tag
holding it, over the `n` released; a change no release holds yet is counted under `why` as
`unreleased`, one whose tag has no readable date as `no date`, and `releases` is the window's
release tags. `follow_through` scores the last retrospective's plans: the seeds its commit added
to the register, each `done` (a change in the window names it on `idea:` or `fixes:`), `dropped`
(an `inbox-commit` subject since says `Retire` with its id), `carried` (still in the register) or
`vanished` (gone with neither); and the milestones open in its direction doc, `done` when struck
Done or when every change and seed they group has closed, shipped or been dropped with at least
one closed or shipped, `dropped` when struck Dropped or Revised or when every row they group was
dropped, `vanished` when gone from the doc, unmeasured when a grouped change is
unknown, and `carried` otherwise. `share` is done and dropped over the `n` scored. `missing` names
each source that couldn't be read, and always the intent titles a retrospective proposes, which
nothing records; with no earlier retrospective `since`, `share`, `seeds` and `milestones` are null.

Each headline says how far it can be trusted. `process.lead`, `process.escapes`, `metrics` (the
person's response and stops) and `spend` each carry `coverage: {measured, of, greyed}` (`of` being
the window's closed changes) and `missing_because`, the rest by reason, whose counts sum to
`of - measured`. The reasons are fixed words, read from what each `Close` commit carries:

- **Lead time:** `not measured at close` (no `Sdlc-*` at all), `no opened: line`, `opened:
  unreadable`, `timing failed` (` lead=none`, ` lead=bad-opened`, ` lead=failed`), or `closed
  before lead time was recorded`.
- **The person's minutes:** `not measured at close`, or the reason a `Sdlc-Coverage: none:` gives
  (`no transcripts for this repo`, `metrics.transcripts is off`). `process.response` gives the
  same per tier, over every change of that tier, so the scorecard's median response says why it
  is null even when no change was measured.
- **Spend:** its `why`.
- **Escape rate:** none; it rests on every closed change.

`greyed` is true when fewer than half the window's changes are measured. The report's Trust band,
after the pillar table in *Scorecard*, gives one *Coverage* line per headline, giving the changes it rests on and why
the rest are missing. A greyed line is in italics and ends `a hint: under half the changes`.

`process.underneath` is what the changes ran on, from their `Sdlc-Runtime` (see *Metrics*), for
this window (`window`) and the last one (`previous`): each of `claude`, `models` and `plugin` as
`{value: changes}`, and how many changes `recorded` the line and how many didn't (`unrecorded`). A
change closed before the line gives its models from its `Sdlc-Role` `model=`, and counts as
unrecorded. `changed` says, per dimension, whether the values differ, and is null when either side
recorded none. The last window runs from the retrospective before this window's boundary (the
start of history with only one) to it; with no retrospective `previous` is null. The report's
*What changed underneath* line, after the coverage lines, gives each dimension against the last
window and says which changed. It is read from history alone: retro reads no transcript and runs
no `claude`.

`process.window.factory` counts the window's changes with `Sdlc-Mode: factory`, and
`mode_unknown` those with no `Sdlc-Mode`. With no factory change, `process.landing_catches` is
null and the report says `No factory changes in this window.` in place of the catches line,
naming the changes with no way recorded. In a host, neither `retro` nor its report mentions the
skills' cases, which belong to this plugin's own repo; `prose` leaves out ship's branch for them.

Its `surface` is how much of the plugin the window used, read-only like the rest. `items` lists
every skill, every `sdlc.py` command and every config key, built from the code as it runs, never
from a list kept by hand, with the factory's skills and `factory.py` commands (`plugin:
"sdlc-factory"`) when the factory is enabled or the repo is the plugin's own. Each item has its
`uses` and a `state`: `used`; `unused`, only where a record could have shown it; or `unmeasured`,
with its `why`, where none could: a skill that runs outside a change's sessions (`/sdlc:idea`,
`/sdlc:status`, `/sdlc:release` and the rest, whose sessions no `Close` commit measures), a
command no skill's bash runs, or a skill or command when no change in the window recorded its
kind of line. A skill's use is the runs on its `Sdlc-Skill` lines, a command's the calls on the
`Sdlc-Tool` lines naming it (`Bash:sdlc.py:<command>`), never `Sdlc-Calls` on top, and a key is
used when the base branch's `.sdlc/config.toml` sets it, a default being no setting. The
factory's supervisor keeps a change's typed `/sdlc-factory:build` or `land` but none of its calls,
so a command only those skills run is unmeasured; one an agent ran is still used. `share` is used
over used and unused, per kind (`skills`, `commands`, `keys`) and `overall`, the unmeasured in
neither, beside `coverage` and `missing_because`: the window's changes whose `Close` carries
`Sdlc-Skill` or `Sdlc-Tool` lines. `retire` names each item unused in each of the last
`RETIRE_AFTER` (3) windows that measured it, the current one first: a window that couldn't
measure it is passed over, and the walk back stops for a kind at a window closed before that kind
was counted. Its `windows` says how many windows the answer rests on, the windows actually read:
below `RETIRE_AFTER` when every item was decided early (each used, or never a candidate), and no
candidate is hidden then; with fewer than three measured, it names nothing. `footprint` is what setup left: the paths `.sdlc/setup.json`'s
`created` names, the keys the config sets, and the lines of the tracked files under `.sdlc/` but
the change folders, `retros/` and `reports/`, all on the base branch; with no `setup.json` it is
null and `why.footprint` says so. `growth`, in the plugin's own repo only (null elsewhere, with
`why.growth`), is one row per release tag in the window and the tag before the first: `skills`,
`commands`, `keys` (from that tag's `setup.json`) and `doc_lines`, each read at the tag and null
where it can't be, their `change` since the row before, and `capability`, the `major` and `minor`
changes between the two tags. `docs/FEATURES.md` maps the features these count.

Its `architecture` is where the code is going, from git alone, for any language. Each closed
change carries `added`, `deleted` and `by_kind`: its lines and files as `code`, `tests` or `docs`.
A path is tests when a directory in it is `test`, `tests`, `spec` or `__tests__`, or its name
matches `test_*`, `*_test.*`, `*.test.*` or `*.spec.*`; docs when it ends `.md`, `.rst`, `.adoc` or
`.txt` or sits under `docs/`; code otherwise. `retro.test_paths` and `retro.doc_paths` replace
either rule, and `kinds` says which held. `size` is each tier's medians over the window.
`hotspots` (the ten files the most changes touched, with the lines changed and the file's size)
and `co_change` (pairs of files three or more changes touched together, leaving out a change of
more than 50 files) read the last 30 closed changes, past the retrospective (`lookback`), since
one window is too few to show structure. `largest` is the ten largest text files and `totals` each
kind's files and lines, each now and at the last retrospective, with the growth between. Nothing
times the gate: a host that wants it, or complexity or dependency cycles, names a command in
`retro.indicators`, run as `retro.evidence` is (with or without a product doc, stopped after 60
seconds, kept up to 20,000 characters), one row each in `host`, in config order.

An indicator's output is read as rows when every non-blank line of its stdout is one JSON object
(JSON Lines) with a `name` (a non-empty string on one line, at most 200 characters), a `value` (a
finite number, never a boolean) and, if it likes, a `unit` (a string on one line, at most 40
characters, or null, never `—`, which the report writes for none); neither the name nor the unit
may start or end with a space, or it would read back from the report as another row. Any other key is kept as `extra` and never rendered, and a row is known by
its `name` and `unit` (a missing unit is `""`). For example
`{"name": "src/drafts.py::save", "value": 3, "unit": "commits"}`. Its `host` row then holds
`rows`, each with its `name`, `unit`, `value`, `extra`, `last` (the same row's value in the last
retrospective's committed report, read back from its `## Indicators` table, null with no
retrospective, no report, no such row or the row twice) and `change` (`value − last`, to three
decimal places, null with no `last`), with `output` null and `not_rows` null. Anything else
passes through as before, `output`, `exit`, `error` and `truncated` kept, with `rows` null and
`not_rows` saying why: a line that isn't such an object, no line at all, a row twice, an output
cut at the limit, a non-zero exit (`failed: exited N`) or a timeout (`timed out`). Plain text
never breaks: it just stays out of the report.

Its `tests` is what the pruning pass reads. `times` comes from `retro.test_times`: commands each
printing a JUnit XML report of the suite on stdout, the format nearly every runner can write
(pytest's `--junitxml`, jest-junit, go-junit-report, Surefire, Gradle, cargo-nextest), so the
plugin never learns which runner a host uses. A command may run the suite, `cat` a report the
gate left, or fetch CI's. Each runs as `retro.evidence` does, but stopped after 600 seconds rather
than 60 and kept up to 5,000,000 characters rather than 20,000; a report cut at that limit is a
failure, never read in part. Every `<testcase>` is read at any depth, its id `classname::name` (or
`file::name`), its `time` in seconds (a missing, unreadable or zero `time` is `untimed`), and a
`<skipped>` child counted apart and never timed. The cases of every command are pooled. `state` is
`unset` with no command, `failed` when no command gave a test case (each row in `commands` says
why: its exit, a timeout, a cut report, or XML that doesn't parse), and `ok` otherwise, with the
counts, the total `seconds`, the `median`, the ten `slowest` with each one's share of the total,
and `slow`: those at least ten times the median and at least a second. No command's output is
kept. `drifted` reads the same 30 changes as `architecture`: a test file still on the base branch
whose last change also touched code files that three or more later changes moved without it,
with that change, the code and how many `later` (null with no base branch). `due` is true when
any test is `slow` or `drifted`, and `/sdlc:retro` then proposes a pruning pass: one seed naming
every candidate and why. The retrospective never edits or deletes a test; pruning is a later
change, reviewed at ship. A test a newer one repeats, or one that passes for the wrong reason, is
in `unmeasured`: it needs per-test coverage or mutation results no host records here.

Its `spend` sets what each closed change in the window spent beside its size. Each change's row
(printed only with `--metrics`) holds its tier, its added code lines, how many of them are line
comments, its agent `out` tokens, the person's `words` per stage, and its tool calls and their
errors. A comment is told by line alone: an added line in a code file whose text starts with its
suffix's marker (`#` for `.py .sh .toml .yaml .yml .rb`, `//` for `.js .ts .go .rs .java .c .h
.cpp .swift .kt`, `--` for `.sql .lua`, `<!--` for `.html`), never parsed, so a docstring is code
and a `#` line inside a string is a comment; prose is never counted, and a suffix with no marker
is counted as `unknown_lines`. `tiers` gives each tier's median comment share, `out` tokens per
added code line and tool calls per added code line, over the changes that have each, and none
for a tier with fewer than three; `outliers` names each change more than twice its tier's median
on any of them, with by how much. `tools` ranks the window's tool names by calls and by errors,
each with its error share and the changes it was called in. A change whose `Close` commit carries
no `tools=` or `words=` (closed before they were counted, or measured from history alone, with
`metrics.transcripts` off) is `recorded: false`, counted in `unrecorded` with its reason in `why`,
and is in no call figure: its comment lines still count, since git gives them.

Its `autonomy` is how often the factory needed the person, read from the records each factory
run left in its change's own commit (`decision.md`, each `decision-<n>.md` a restart kept,
`decisions.md` and `runs/mended`), never from a trailer, so it counts every factory change in the
window, however long ago it landed. `factory` and `by_hand` say how many of each closed; a change
built by hand (no `decision.md`) is in no other figure, never a zero. Every figure carries `n`, the
count it is over, and a rate or per-change figure is null when `n` is 0. `escalations`: the
`DECISION: ESCALATE`s, current and archived (`total`), the changes with any, and `per_change`; a
decision file no answer reads leaves its change out of `n` and is a problem naming the change and
the file. `asked`: the questions the person answered, `blocking` decisions, `default`s they kept
or changed and `look`s they cleared, and `per_change`. `kept_default`: `rate` is kept over kept
and changed; `confirmed`, the defaults the landing's one yes confirmed, and `settled`, those the
approver settled, sit beside it and never enter it. `auto_landed`: from each change's own
`Sdlc-Landed`, `auto` (the landing's WAIT approved itself), `person`, or `shipped` (no line: shipped
by hand), with `share`, auto over `n`. `spurious_stops`: the mends, the one stop a run clears
without the person, a build's (`build`) apart from a landing's (`landing`), the changes with any,
and `per_change`. `looks`: `seen` (answered `seen`), `checked` (any other answer) and `open`, with
`seen_share`. `overturned` has no count: no record holds an approver's settled call the person
overturned, and it is in `unmeasured`, as a factory stop that cleared with nothing changed is. The
report's *Autonomy* section shows each, with its `n`.

Its `cost` is what the window's factory runs cost, read from each closed change's own commit and
each dropped change's tip (`runs/costs.jsonl`, and `runs/ejections.jsonl`, which a landing train
writes in each change it puts back). Every row a factory run writes names what it was for, its
`purpose`: `spec`, `build`, `rework` (a round after the run's first), `gate-fix`, `mend`,
`rerun` (the same step for the same agent in the same round, again) or `land`. A row's dollars are
the change in its session's running total, so a resumed builder counts once. Each row lands in one
part: `untagged` (a row from before purposes, never waste), `dropped` (any row of a dropped
change), `ejected` (a landing's run that ended by an ejection), or its purpose; `rework`,
`gate-fix`, `mend`, `rerun`, `ejected` and `dropped` are waste. `per_change` gives each tier's
`n`, and the median and total of `usd` and `minutes`, over the landed changes that report
dollars. `waste` gives the waste's `usd` and `minutes`, what they are of, their `share` and
`minutes_share` (null with nothing to divide by), `n`, and every part's `usd`, `minutes` and
`runs`, over the changes, landed and dropped, with dollars and no untagged row. `by_role` and
`by_model` split every run's dollars and minutes; `unknown` counts the rows with no dollars and
`untagged` the rows with no purpose. A change with no dollars is in no figure, never a $0: `cost`
and `waste` each carry `coverage` and `missing_because`, under `built by hand`, `no agent runs
recorded`, `no cost reported`, and, for `waste`, `runs recorded before purposes`. `changes`, each
change's own figures, is printed only with `--metrics`. The report's *Coverage* lines say how far
`cost per landed change` and `waste share` rest, and its *Cost* section shows the figures.

Its `pipeline` is where the factory's pipeline spends time and takes risks, read from the records
each factory run left in its change's own commit (the gate records `build/round-<N>.gate.md` and
`build/land-<n>.gate.md`, `runs/step.md`, `runs/land-step.md`, `runs/land-train.md`,
`runs/land-times.jsonl`, `runs/ejections.jsonl`, `build/land-accept.md` and `conflicts.md`) and
from its `Sdlc-Landed`. `factory` and `by_hand` are as in `autonomy`; a change built by hand is in
no other figure. Every figure carries `n`, and a rate, share, median or percentile is null when
`n` is 0. `gates.window` and `gates.previous` (the window before this one; null with no
retrospective before it) give the `round` and `land` gates' attempts, each its `seconds` and
`wait` (the slot wait, each attempt's `Waited:` line) as `n`, `median` and nearest-rank `p85`; an
attempt from before `Waited:` counts in `seconds` alone, and the hand gate's `build/gate.md` is in
neither. `red_gate`: the round gate files (`builds`), those with any failed attempt (`red`), and
`rate`. `landing` is over the factory changes a factory landing made (with a `runs/land-step.md`),
its `coverage` and `missing_because` under `built by hand` or `no landing record`: the landing
gates' attempts (`gates`, `total` and `per_change`); `ejections` by cause (`gate`, `review`,
`refusal`, `stop`), with a `total` and the changes with any; `bisections`, the distinct red gates
over a prefix of more than one change, which a train must bisect, counted once though every change
in the prefix names it, with `per_change`; `base_moves`, each change's last `MOVES:` (a train change's is its
train's: the moves seen while landing, not a train total), with `per_change` and the changes with
any; `accept_stops`, the attempts in `build/land-accept.md`, each a stop for the person, with
`per_change` and the changes with any; and
`conflicts`, the landing's resolved conflicts (`landing`) and the files ship's `conflicts.md`
names (`ship`). `depth`: the runs whose last `runs/step.md` says `DEPTH: full` or `light`, with
`share`, full over both; a run never lightens, so its last reading is its deepest, and a run from
before the line is in `missing_because` as `depth not recorded`, never light. `unreviewed`: over
the landings `Sdlc-Landed` says were the factory's (`auto` or `person`), those whose
`unreviewed=` is a count above 0 (`with_paths`, and `paths`, their sum), `unknown`, or 0
(`none`); a landing from before the field is missing, `unreviewed not recorded`. Mends aren't
counted here: `autonomy.spurious_stops` gives them, a build's apart from a landing's. `changes`,
each change's own figures, is printed only with `--metrics`. The report's *Speed* section shows the
gates and the landing, and its *Quality* section the red gates, depth and unreviewed landings, with
no factory change a sentence saying so.

Its `simplicity.workarounds` counts what the process didn't plan for, from history alone, so
nobody logs a workaround by hand. Every first-parent commit on the base branch in the window (from
the last retrospective, else the commit that first added `.sdlc/config.toml`, to the tip) is a
closed change's own (from where it started to its commit), a command's (`Close`, `Drop`, a
register commit whose every `; ` part is `File`, `Retire`, `Update` or `Triage`, `Release X.Y.Z`,
`Retrospective YYYY-MM-DD`, or setup's and uninstall's own subjects), or outside the loop:
`hand_record` when it touches a record (a change folder or the register, a retrospective's report,
`.sdlc/setup.json` or `.sdlc/last-id`), `outside` when not, each listed by its short sha and
subject over `n`, the window's commits. `restored` lists each register entry a commit in the
window added back after an earlier commit removed it, over the entries the window added. A closed
change whose start can't be found claims only its own commit, and the commits before it back to
the last `Close` or `Drop` are `unknown`, never outside, with a problem naming the change.
`overrides` is read from each closed change's own commit and each dropped change's tip, over the
changes a factory run built (`n`): `ejections`, the landing train's ejections by `cause` (`gate`,
`review` or `refusal`; a `gate` one is a fault the train found, not the person's call), `stops`,
the trains stopped, each once by the `train` its rows name (a row from before rows named their
train counts once per change), and `fixes`, the fixes the person asked for at landing
(`build/land-<n>.ask.md`). A stop before any change was committed records nothing. Each count is
null, never 0, when its `n` is 0. It is a reading, not a guard: a hand commit worded as a
command's counts as the command's, and an edit to a change's own records on its branch is the
change's, which `unmeasured` names.

`/sdlc:retro` makes five passes over that (cost, architecture, process, product, direction),
turns every finding into a seed, an intent title or a reason for dropping it, and after one
approval rewrites the direction doc (`docs.direction`), the product doc's outcome lines when there
is one, and appends the seeds. It also re-ranks the register for the new direction: the same
approval sets `Priority: high` or `low`, removes a `Priority:` that no longer holds, and gives an
unthemed entry a `Theme:`, on open ideas and bugs only (never a nit, or an entry being built), and
names the seeds it judges no longer wanted for you to retire with `/sdlc:idea`. `sdlc.py
retro-commit` commits those files and nothing else, as the next retrospective's boundary, and
refuses a register entry removed or changed beyond those two lines. With them it commits a report
it writes itself, `.sdlc/retros/<date>.md`, rendered from `templates/retro.md`: its figures from
history, and its *Insights* from the answers approved at the retrospective's question.
After the window's sentence it opens with the scorecard (`## Scorecard`): the Value band (work mix,
time to users, follow-through), the pillar table, and the Trust band (the *Coverage* lines, *What
changed underneath*, and the signals no record holds). Then `## Insights` (below). Each pillar's
figures then follow in a
section of its own: *Speed* (cycle time per tier, changes closed per week, where the time went, how
many changes ran at once and what that did to them, the *By way of building* table and the
pipeline's gates and landing), *Quality* (escapes, who found what, rework, and the pipeline's red
gates, depth and unreviewed landings), the host's *Indicators*, *Autonomy*, *Cost*, *Spend* and
*Simplicity* (the workarounds; in the plugin's own repo, its surface's share, retire candidates,
footprint and growth too, never in a host's).

`sdlc.py retro`'s `scorecard` is that table: `rows`, each with its `pillar` (Speed, Quality,
Autonomy, Cost, Simplicity), `role` (`headline` or `guardrail`), `figure`, `unit`, `value`, `n`,
`last`, `trend` and `note`, and `since`. Each row's value is a figure another block already gives,
one row a way or tier present where that block gives it only that way: lead time's median by way,
rework links per closed change, the escape rate, the person's median response by tier, questions
answered per factory change, the escape rate by way, the median dollars per landed change by tier,
the surface's share used (the plugin's own repo alone), and the commits outside the loop, records
edited by hand and register entries restored. A null value reads `—`, with its block's most
counted `missing_because` reason (`none in the window` without one) as its note, never 0: the
person's response by `process.response`, a question answered per factory change `built by hand`,
the escape rate by way `no <way> change in the window`, the commits outside the loop and records
edited by hand `no commit on the base branch in the window`, and the entries restored `no
register entry added in the window`. A greyed block's note says `a hint: under half the changes`.
Minutes are written to one decimal place, so a short median response isn't flattened to a whole
minute; the first retrospective after 189 compares against its predecessor's whole-minute values,
so a response row's trend there can move by rounding alone. `last` is the same row's value in the last
retrospective's committed report, read back from its table as the indicators are (the escape rate
keeps `process.escapes`' own `previous` and `trend`), and `trend` is `up`, `down` or `flat`
against it, the value compared as the table writes it, `unknown` with no `last` or when either side rests on fewer than five changes. The
report and the JSON come from one function, so they never disagree.

**Insights.** `## Insights` answers the synthesis questions: one per pillar from the plugin's
`guide/insights.md`, Value, Speed, Quality, Autonomy, Cost, Simplicity and Tradeoffs, and any your
`docs.insights` adds. `sdlc.py retro --insights` prints each question (`title`, `pillar`,
`question`) with its `data`: only the figures of `retro`'s output that pillar is given, its
scorecard rows (every row for Tradeoffs), `process.window` and `process.underneath`, and
`problems`, your question doc's. It writes nothing and runs no host command: the figures are
counted with `retro.evidence`, `retro.indicators` and `retro.test_times` emptied, and no bundle
holds their output. `/sdlc:retro` gives each question to its own `sdlc:insight` agent at once
(`Read`, `Grep` and `Glob` alone), which returns one shape, fixed by the script and never by a
question doc:

```
Headline: <one sentence>
Evidence: <the figures, each with its n>
Recommendation: <one thing to do, or nothing>
Disposition: seed <entry id> | intent: <title> | dropped: <reason> | none: <why>
```

"Nothing to act on this window" is a valid `none`. After the retrospective's yes the skill writes
the answers to `.sdlc/retros/<date>.insights.md`, one `## <title>` block per question, and
`retro-commit` refuses, before writing anything, a draft that misses a question or a field,
answers an unknown title or one twice, gives a Disposition of no known kind, or names a seed the
register doesn't hold. It renders each answer as `### <title>: <headline>`, the question, and the
Evidence, Recommendation and Disposition, and removes the draft once its commit is made: the draft
is never committed. With no draft the section says `Not answered: this report was written without
the retrospective's insights.` `sdlc.py retro --report` renders a draft that is there, and writes
nothing.

Override the template in `.sdlc/templates/`: an override without its `## Scorecard`, `## Spend` or
`## Indicators` section and their `{{scorecard}}`, `{{spend}}` and `{{indicators}}` is reported as
breaking after an update, since the next retrospective reads the scorecard and indicator tables
back. The pillar sections (`{{speed}}`, `{{quality}}`, `{{autonomy}}`, `{{cost}}`,
`{{simplicity}}`) and `{{insights}}` are optional: an override without one just doesn't show it. An override without
`{{scorecard}}` renders as before, its `{{window}}` holding the Value band, the coverage lines and
the *By way of building* table, and every older placeholder (`{{cycle}}`, `{{throughput}}`,
`{{time}}`, `{{capacity}}`, `{{rework}}`, `{{escapes}}`) still filled. Its figures are `sdlc.py
retro`'s, which counts changes close couldn't measure but never reads them as zero. The report runs
one host command, `retro.indicators`, as `retro` does, and never `retro.evidence` or
`retro.test_times`: `## Indicators` names each command in a code span, then its rows as a table
headed `| Indicator | Unit | Value | Last retrospective | Change |` (a `|` in a cell escaped as
`\|`, a missing figure `—`, a change signed `+3` or `−2`), or one sentence saying it failed,
timed out, or printed output that isn't rows, which is in `retro`'s output only; a command's raw
output or stderr is never written there. With `retro.indicators` empty it says no indicators are
set. `sdlc.py retro --report` prints it without writing anything. It never edits code, skills, the process doc, the review doc or
`.sdlc/config.toml`: a lesson an escape holds for the review (a failure class for the review doc,
a path for `[review]`) is a seed with the exact text, made by a change that ship reviews.

Goals and milestones in the direction doc keep ids across retrospectives (`- G1. …`, `### M1. …`
with a `Groups:` line naming its changes and seeds), and each one ends struck through as `Done`,
`Dropped: <reason>` or `Revised → M5: <reason>`, never silently gone: `retro` reports what each
milestone's seeds and changes became (`direction.milestones`: a change `closed`, `open` or
`unknown`; a seed `shipped`, `open`, `dropped` when it left the register in an `inbox-commit`
`Retire`, matched by id or by its title as the register held it, or `vanished` with none of
these), and `retro-commit` refuses a doc that drops an open id. `status` says a milestone has
nothing left in its groups when every row is `closed`, `shipped`, `dropped` or `vanished`.
A goal ends with the outcomes in the product doc it answers to (`- G1. … (O1, O3)`), and a
milestone has a `Serves:` line beside `Groups:` naming its goal, its outcomes or both
(`Serves: G1, O4`). With a product doc, `retro`'s `product.uncited` reports each open goal or
milestone that reaches no open outcome, and `product.none_themes` groups the changes serving
`none` by their seeds' themes; an uncited item is reported, never refused.

## Metrics

`/sdlc:close` measures the change it lands and writes the numbers as `Sdlc-*` trailers on its
`Close` commit (a dropped change's on its `Drop` commit), so history keeps them after the
transcripts are gone. By default it reads this repo's Claude Code session transcripts on the
machine, for numbers only: never message text, a path or a session id
(`metrics.transcripts = false` turns it off). Per stage it records four clocks:

- **elapsed**: calendar time, never effort;
- **agent**: the time the agent was working;
- **response**: time waiting on the person, up to `metrics.idle_minutes`;
- **away**: waits longer than that.

Waits while a `depends_on:` change is still open count as **blocked**. It also records the stops
(approvals, questions and anything else that waited on the person) against the approvals the way of
running requires (by hand or by the factory) plus `metrics.stop_allowance`, and tokens per stage and
per sub-agent role. A factory change owes `intent`, `run`, `ship` and `close`, and `spec` too when
its spec was approved at a stage of its own. The factory's supervisor is a session in the main
checkout carrying several changes: a change counts of it only the `/sdlc-factory:build` naming it
and the dialogs whose question names its `NNN-slug`. Each agent the factory ran as a session of its
own (`runs/<agent>.sessions` in the change's folder; its permission mode is `.sdlc/factory.toml`'s
`mode`, read from the base branch, see the factory's README) counts as a run of that role, its own
read-only sub-agents as runs of theirs, never as the person's stages. A change `/sdlc-factory:land`
landed owes `land` in place of `ship` and `close`: one approval per batch, which approves itself on a
batch with no risk signal (`[land] auto` in `.sdlc/factory.toml`, read from the base branch, default
on; `[land] batch`, default 5). The batch lands as a train: stacked in order, the base branch's
check run once at the tip, each change closed in order by close's fast-forward, so the base
branch's first-parent line reads as it does for changes landed one at a time. Its commit says who passed it, `Sdlc-Landed: by=person|auto`; a pass
nobody gave is `auto=1` on `Sdlc-Totals`, never a stop, and its ship and close read `auto` on
`Sdlc-Happy`, which no first-time rate counts. A change landed with paths that changed after its
last review round (a hand edit after the approver) says how many on the same line,
`Sdlc-Landed: by=person unreviewed=<n>`, or `unreviewed=unknown` when the run left no snapshot to
compare, with the paths in the commit's body, never in a trailer. Close carries it to
`Sdlc-Totals` as `unreviewed=`, beside `auto=`, on a landed change whose commit has it; no other
change has the field.

A stop is the person: an entry the harness sent (a background task's notice, a compaction summary)
is counted as `harness=`, and a slash command other than the plugins' skills (`/reload-plugins`)
as `command=`, both on `Sdlc-Totals`, and neither is a stop. Each stop beyond the gates and
questions gets a kind, read from its shape, never its words: `after_gate` (typed once a skill's
WAIT was answered), `revise` (a revision before it), `asked` (an answer to a question the agent
put in prose), `interrupt`, `fix` (asking for the review's own findings to be fixed, before it,
as ship's question offers: never a revise), or `unprompted`, one `Sdlc-Extra: <stage>
after_gate=<n> revise=<n> asked=<n> unprompted=<n> interrupt=<n> fix=<n> harness=<n> command=<n>`
line for each stage with any; a line from before `fix` reads it as 0. A `Close` commit without
`harness=` counted both as stops, and `/sdlc:retro` reads its kinds as unrecorded. Each gated
skill with an `after_gate` stop also gets `Sdlc-AfterGate: <skill> stops=<n>`, naming the skill
whose WAIT the stop followed; `/sdlc:retro` adds them up as `metrics.extra.after_gate_by`, and
counts the `after_gate` stops of a commit without the lines, closed before them, as
`after_gate_unnamed`, never under a skill.

Beside the stops, never among them, it records the tool prompts the person answered: a tool use
they were asked to allow and allowed or rejected, never their own questions or plan approvals
(counted as stops already), and never one the rules, the mode or the classifier decided. Each is
named by the tool, and for `Bash` by the program it ran, with the subcommand for `git`, `gh` and
the plugin's scripts (`Bash:git:push`, `Bash:sdlc.py:accept`, `Edit`), never an argument or a
path: one `Sdlc-Prompt: <name> asked=<n> rejected=<n>` line each, `prompts=` on `Sdlc-Totals` and
each `Sdlc-Stage`, and `prompt_modes=` on `Sdlc-Totals`, the permission modes the change ran in
(`auto` asks no one, so its zero says nothing about a skill's rules). An older `Close` commit
carries `permission=` instead, which counted questions and plan approvals, not prompts:
`/sdlc:retro` reads it as unrecorded.

It also counts every tool call, prompted or not, named the same way: one `Sdlc-Tool: <name>
calls=<n> errors=<n> <stage>=<n> …` line a name, with `tools=` on `Sdlc-Totals` for all of them.
An error is a call whose result the transcript marks as one, a rejected prompt included; a call
with no result is no error. A sub-agent's calls, and a factory agent's, count with the change.
And it counts the words the person typed (a slash command's name and arguments, a reply's text,
never the text itself) as `words=` on each `Sdlc-Stage` and on `Sdlc-Totals`. A `Close` commit
without `tools=` or `words=` is read as unrecorded, never as none.

Each agent role's `Sdlc-Role` line also says how that role worked, counted in the same pass over its
transcripts: `model=`, the model `runs/costs.jsonl` records for a factory agent's sessions (several
joined with `,`, left off when none is recorded), then `edits=` (Edit and Write tool calls),
`shell_edits=` (shell commands that write a file: a redirect outside `/dev/` or a temp dir, `tee`,
`sed -i`, `perl -i`, `patch`, `git apply`, or an inline Python script that writes), `bg=` (commands
that went to the background), `tool_errors=`, `test_runs=` (runs of `[commands] check`, `sdlc.py
gate`, or a common test runner) and `broke=` (a test run that couldn't parse or import the code,
right after an edit). Each is a lower bound: a shape not named isn't counted. One `Sdlc-Calls:
<role> <name>=<n> …` line a role names every tool it called, as `Sdlc-Tool` names them. Numbers and
names only, never a command, a path or an output; if counting fails, the role keeps its other fields
and `Sdlc-Coverage` says `behaviour=failed`. `/sdlc:retro` compares them by role and model in an
"Agents by role and model" table under *Spend* (each change's own rows only with `--metrics`); a
role line without `edits=` was closed before they were counted and is unrecorded, never zero.

Ship adds its review's findings as an `Sdlc-Findings` trailer on its own
commit, counted from `findings.md` by `sdlc.py findings`: `important`, `nit` and `preexisting`,
each pass's count, then each disposition's count by pass (`fixed=correctness:2,context:1`, or `0`),
then `fresh` and `fresh_wrong`: how many findings the fresh-context reviewer raised, and how many of
those were answered `wrong`, then `agents`: how many findings a factory run's agents left in the
file, then `passes`, each of ship's further passes' count (`security:1,ui:2`, or `0`), and
`passes_wrong`, how many of those were answered `wrong`. Every other key counts ship's own alone
(no `By:`, `By: fresh`, or a `ship-*` pass), so an agent's finding is never counted as the
person's review; a factory landing writes no `Sdlc-Findings` at all. A
trailer from before dispositions, `fresh`, `agents` or `passes` keeps its counts, and `/sdlc:retro` reads
what it lacks as unknown.

Close also records whether the change went through first time: `Sdlc-Happy` says, per stage, yes,
no or unknown, ship also `fixed` when it ran again only for findings its own review raised and
the change fixed (no `revise` answer, a `fixed` finding in its `findings.md`), which retro counts as
first time and reports apart as `ship_fixed`; a trailer from before has only yes and no. And `Sdlc-Rework` counts the trial and error inside the change (the spec or plan
edited after their stage, `revise` answers, failed gate runs, ship reruns, lines written against
lines kept, and for the factory its rounds, verdicts and decisions, with an `Sdlc-Review` line per
reviewer: its `CHANGES` verdicts, its requests and, from a run with an arbiter, how many of them
the arbiter `dropped`; a run from before that has no `dropped`, read as unknown; and
`gate_fail`, the red attempts of the factory's script gate, which runs `[commands] check` from the
base branch's `.sdlc/config.toml` on each build before its review and on a change a landing
rebased, absent for a run with no gate
file and read as unknown). Exploration you
mean to throw
away goes under `stage: spike`, which owes no artifact; its cost is reported apart as
`Sdlc-Spike`, never as rework.

The bugs a change fixes are recorded too, one `Sdlc-Fixes: <id> severity=<w> reported=<date>
introduced_by=<NNN-slug|unknown> paths=<p1>,<p2>|unknown` line each, from its intent's `fixes:`
and the entry as the branch last held it (a line from before `paths=` reads as paths unknown); a bug retired without a fix gets `Sdlc-Retired: <id> severity=<w>
reported=<date> reason=<word>` on its `Retire` commit. A dropped change fixes nothing. An issue
triage closed gets `Sdlc-Triaged: #<N> verdict=<word> ref=<what it rests on>` on its `Triage` or
`File` commit, its reason as a `Why #<N>:` line in the body.

Close also records the change's lead time and where it went, on one line: `Sdlc-Lead: lead=<m>
queued=<m> agents=<m> idle=<m> ready_wait=<m> landing=<m> source=<runs|transcripts|git>`, in
minutes. Lead time runs from when `new` opened the change, the `opened:` line it writes into
`intent.md` (UTC, to the minute, under either numbering), to the close; it starts at `new` even
for a change opened from an issue someone filed earlier. `queued` is the time before the first
agent or edit, `agents` the time agents were working up to ready (reviewers running together count
once), `idle` the rest of that span, `ready_wait` the time from ready to the landing, and
`landing` the landing itself. A factory change is ready when its last approver run before the
landing ended, and its landing begins at its first landing step: both read from the run files its
commit holds (`runs/costs.jsonl`'s `started` and `ended`, `runs/land-times.jsonl`'s `since`), so
a close on another machine still records them (`source=runs`). A change built by hand is ready
at ship's commit, and its close is its landing, so it has no `landing`. Without run times, the
transcripts give the agents' runs (`source=transcripts`); without those, the line holds `lead`
and `ready_wait` alone for a change built by hand, and `lead` and `landing` for a factory change,
where with no approver run nothing says when it was ready (`source=git`). A part that can't be
known is left out, never 0. A change with no `opened:` (one opened before it was written) gets
no line, and `Sdlc-Coverage` says ` lead=none` (` lead=bad-opened` for a value that doesn't fit,
` lead=failed` when timing it failed); a dropped change has none.

What the change ran on goes on the line after it, on every `Close` and `Drop` commit:
`Sdlc-Runtime: claude=<v>[,<v>…] models=<m>[,<m>…] plugin=<v>`. `claude` is each Claude Code
version the change's transcript entries carry (the main session's, each factory agent's session's
and each sub-agent's), and `models` each model they ran (never the harness's `<synthetic>`), with
the factory roles' models from `runs/costs.jsonl`. `plugin` is this plugin's version at close.
Each part is sorted and deduplicated, every value a word (no space, `/`, `~`, `,` or `:`), and a
part that isn't known is left out, never empty: without transcripts the line is `plugin=` alone.
When building it fails, the line is left out and `Sdlc-Coverage` gains ` runtime=failed`; the
close still lands. A `Close` commit without it was closed before it was recorded: unrecorded,
never unchanged.

Where a change started is recorded as `Sdlc-Base: <sha>`: the base branch's tip just before close
merged it, which close keeps in `refs/sdlc/base/<branch>` between its runs and removes with the
branch. Retro's sizes, the rework `final` counts and `bugs --introduced` measure a change from
it, so a commit the change made before its folder is counted. A `Close` commit from before the
trailer existed is measured from the parent of the commit that first holds the change's intent. A
dropped change has none.

`sdlc.py retro` reads all of them, and prints their medians; each change's own numbers it prints
only with `--metrics`, as do `unreleased` and `release`. Measuring never stops a close: without transcripts,
`Sdlc-Coverage` says why, and the numbers are what history gives. `git log --format=%B` on a
`Close` commit shows them.
