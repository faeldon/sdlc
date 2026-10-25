# sdlc reference

What a repo using the plugin can set, and how the plugin behaves in it. The
[README](../README.md) is the place to start; this is the place to look things up.
`sdlc.py config` shows every setting as your repo resolves it, and `sdlc.py readiness` whether
the repo is set up.

- [Configuration: `.sdlc/config.toml`](#configuration-sdlcconfigtoml)
- [The docs](#the-docs)
- [Templates: `.sdlc/templates/`](#templates-sdlctemplates)
- [After an update: refresh, reset, uninstall](#after-an-update-refresh-reset-uninstall)
- [`work/` and worktrees](#work-and-worktrees)
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
build = "make integration"                  # a slower gate, run when a changed path matches:
build_when = "^src/"                        #   a regex over `git diff --name-only`
scan = "make scan"                          # drift across the whole repo; /sdlc:health runs it
worktree_setup = "make setup {worktree}"    # after /sdlc:intent makes a worktree, run from the main checkout
close_list = "ls /tmp/cache-{suffix}"       # read-only: what a closed change left outside git
close_cleanup = "! make drop {id}"          # handed to the human by /sdlc:close; never run by a skill

[docs]
process = ".sdlc/SDLC.md"                   # the default: tiers, stages, releases
review = ".sdlc/REVIEW.md"                  # the default; falls back to the plugin's defaults/REVIEW.md
policy = "CLAUDE.md"                        # the default (AGENTS.md when that's the only one): the invariants /sdlc:spec designs inside
read_before_design = ["docs/conventions.md"]
explore = "/db:explore"                     # a skill or command for looking at the system itself
health = ".sdlc/HEALTH.md"                  # the default: each scan finding's meaning and response tier; off while absent
context = ["CLAUDE.md", ".claude/CLAUDE.md", "AGENTS.md"]  # the default: what gives a session its context
direction = ".sdlc/DIRECTION.md"            # the default: goals and milestones, rewritten by /sdlc:retro
project = ".sdlc/PROJECT.md"                # the default: which issue fields to fill; off while absent
product = ".sdlc/PRODUCT.md"                # the default: users and outcomes every intent serves; off while absent

[archive]
target = "github"                           # a module in scripts/trackers/; "none", the default, numbers locally
command = "my-tracker save {dir} {id}"      # target = "command": archive {dir}, print where it went

[release]
version_files = ["package.json"]            # each with one `version` line, edited in place; unset = no releases
tag = "v{version}"                          # the default: the release tag, and the next release's boundary
changelog = "CHANGELOG.md"                  # optional: the notes are added to the top of it
after_bump = "uv lock"                      # optional: run by /sdlc:release after the bump; the tracked files it changes are committed too; {version}, {tag}
prepare = "npm pack"                        # optional: run by /sdlc:release after after_bump; builds into untracked or ignored paths only; what it prints is shown at /sdlc:publish; {version}, {tag}
remote = "origin"                           # the default: where /sdlc:publish pushes main and the tag
publish = "npm publish"                     # optional: run by /sdlc:publish after the push, with no terminal and stdin closed; {version}, {tag}
deprecations = ".sdlc/deprecations.toml"    # the default: each shim and the version that removes it; off while absent

[retro]
after_releases = 2                          # the default: releases before status says Retro due; 0 = only a major one
evidence = ["./scripts/usage-summary.sh"]   # optional: what users did, printed for the product pass; only with a product doc

[metrics]
transcripts = true                          # the default: close reads this repo's transcripts, numbers only
idle_minutes = 30                           # the default: a longer wait is the person away, not answering
stop_allowance = 1                          # the default: stops beyond a change's gates its person should expect

[git]
base = "master"                             # optional: the branch changes start from and land on; unset = detected
```

The placeholders:

- `archive.command`: `{dir}` is the shipped folder's path, `{id}` and `{slug}` the change's, and
  `{sha}` the commit it landed as. It must exit 0 and print where the change went, or close stops
  before removing the folder.
- `commands.worktree_setup`: `{worktree}` is the new worktree's path.
- `commands.close_list`: `{suffix}` is the change's branch name with `-` as `_`.
- `commands.close_cleanup`: `{id}` is the change's number.

A version line is `"version": "1.2.0"` (JSON) or `version = "1.2.0"` (TOML). A file with none,
or more than one, is refused rather than guessed at.

A `[docs]` path under `work/` is read like any other, from the checkout `config` runs in.

### The base branch: `[git] base`

Every change branches from the base branch and lands back on it. Ship brings a branch up to date
with it, close fast-forwards it, release tags it, publish pushes it, and status, release and the
retrospective read history along its first-parent line. Wherever these docs say `main`, they
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

With no base branch, or one that doesn't exist here, every command that writes refuses before it
does anything: `new` before it claims a number, so no GitHub issue is opened for a change that
can't be made, and `base`, `close`, `release`, `publish` and `retro-commit` too. `status`,
`unreleased` and `retro` report it and list no landed changes.

Changing `base` in a repo that has already closed changes points every history reader at the new
branch's line. The changes closed on the old one aren't found there unless the old branch was
merged into it by fast-forward.

## The docs

The process's own docs live in `.sdlc/`, beside its config, so `docs/` is left to your project.

- **`docs.process`** (`.sdlc/SDLC.md`) holds the tier table and what each stage means here.
  `defaults/SDLC.md` is the plugin's generic one, which setup fills in.
- **`docs.review`** (`.sdlc/REVIEW.md`) holds the review passes. Without one, `/sdlc:ship` works
  through `defaults/REVIEW.md` and says so.
- **`docs.policy`** holds the invariants a design has to stay inside: `CLAUDE.md`, or `AGENTS.md`
  when the repo has no `CLAUDE.md`. Set it to name another file.
- **`docs.health`** (`.sdlc/HEALTH.md`) holds what each finding your scan can report
  means, and the response tier it usually gets. Off while absent; `/sdlc:setup` drafts it from
  `defaults/HEALTH.md` once `commands.scan` is set.
- A missing doc is reported, never silently replaced (except the review).

**Three commands, three questions.** `commands.check` is the gate `/sdlc:ship` runs on this diff:
is it correct, pass or fail. `commands.build` is a slower gate, run when a changed path matches
`build_when`. `commands.scan` looks for drift across the whole repo: `/sdlc:health` runs it,
and it produces findings rather than a pass or fail. A task of your own named `doctor` or `health`
is usually your scan; setup proposes it for `commands.scan`. It is unrelated to the plugin's
`sdlc.py readiness`, which only says whether the repo is set up for the plugin.

**`defaults/` and `templates/`.** A file in the plugin's `defaults/` is a doc `/sdlc:setup` copies
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
quickly? A proposed edit is shown with the findings, approved with the commit, and lands in it.
`sdlc.py context` does the listing, and flags their lines naming a path the diff deletes or
renames.

## Templates: `.sdlc/templates/`

`intent.md`, `spec.md` and `plan.md` here replace the plugin's own (`templates/`), file by file,
and so does `direction.md`, the sections `/sdlc:retro` fills. The plugin's are generic. A repo's
own can add the sections its domain needs and prompts in its own words; keep the placeholders
(`NNN`, `SLUG`, `TITLE`, `YYYY-MM-DD`) and the frontmatter, which `sdlc.py` reads. Prompt lines
start with `<`: two or more left in a file is how `sdlc.py status` tells a scaffold nobody has
written from a real artifact.

`inbox.md` here replaces what `work/inbox.md` starts as, when `/sdlc:retro` or `/sdlc:ship` first
adds a seed to a repo with none, and `notes.md` what a change's `notes.md` starts as, when a skill
or the factory first writes one. None has prompts: its note carries the rules. `checks.md`
is what a change's acceptance checks start as; its one example section's prompts make an untouched
copy a scaffold, which `sdlc.py check` reports rather than runs.

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
replacement: `metrics.target_stops` became `metrics.stop_allowance` in 1.2.0, and the note goes in 1.4.0), a template override lacking a heading, frontmatter key or placeholder the script
reads (`TEMPLATE_READS`), or a project or product doc it can't parse. `report` also lists config
keys the plugin doesn't read, keys new since the record (with their default; this page says what
each does), and plugin templates that changed under one of your overrides.

**`/sdlc:setup reset <doc | template | all>`** puts the default back: a doc with its prompts
filled as a first setup fills them, after a diff of every block of yours it loses; a template
override by deleting it (`sdlc.py reset <name>`, which refuses any other path, and an override with
uncommitted edits).

**`/sdlc:uninstall`** removes what setup wrote: the committed files in `.sdlc/`, the plugin's
allow rules in `.claude/settings.json` (every other key and rule kept), and the
`.claude/worktrees/` line when the record says setup added it. It refuses while a change is open,
stands in a worktree, or is shipped and not closed, and while anything it would remove has
uncommitted edits, so history keeps everything it removes. It leaves `work/`, `AGENTS.md` and
`CLAUDE.md` (listing their lines that name the plugin), the tracker's issues, tags and history,
and commits nothing. A later setup numbers on from that history.

## `work/` and worktrees

`work/` is committed. A change's folder, `work/NNN-slug/`, lives on its own branch, in its own
worktree (`.claude/worktrees/NNN-slug`), so the session working on it writes its artifacts where
it works, and `/sdlc:ship` commits them with the code: the review reads the spec next to what was
built. `sdlc.py status` lists the open changes in every worktree, from any of them, and marks
one whose branch lacks commits `main` has (`behind main by N`). Since close only fast-forwards,
`/sdlc:ship` brings such a branch up to date before the gate runs (`sdlc.py base`): a
fast-forward that carries the uncommitted work, or a rebase of the branch's own commits from a
clean tree, reported with the command that undoes it. Anything that would conflict is refused,
untouched, for the person to resolve. Once a change
lands, `/sdlc:close` takes its folder off `main` in a commit of its own, so `work/` never fills up
with finished changes: the change's commit keeps them in history. `work/inbox.md` is committed
too; a closed seed is deleted from it, history keeping that as well. Every entry there is a
seed, and its tag is its kind: `[idea]`, `[bug]` or `[nit]` (the process doc's "Seeds, and the
changes they become" says what each is, and the change types they grow into). Any other tag reads
as an idea, and `[seed]`, what ideas were tagged before they had their own, does so for good. It was `work/ideas.md`
before 1.2.0, and a repo with only that file is read from it until 1.4.0, as a host template
`.sdlc/templates/ideas.md` is read as `inbox.md` (`sdlc.py drift` says to rename it); `check`
reports a repo holding both. `sdlc.py migrate-inbox`, which `/sdlc:setup` offers, moves a repo
over: it renames `work/ideas.md` with `git mv`, gives every entry an id, folds a `work/nits.md`
into `[nit]` entries, retags each `[seed]` entry `[idea]`, and rewrites the titles that name an open entry to its id, in `After:`, the
direction doc's `Groups:` and the open changes' `idea:`. It never commits, and refuses while one
of those files has uncommitted edits, or one it can't read. Run it with no change open: one in
another worktree keeps a title `idea:`. Until a repo migrates, `sdlc.py config`'s `work.register`
names `work/ideas.md`, and every skill that writes an entry writes there, never a second file. The findings `/sdlc:ship` approved unfixed are entries there too,
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
behind one approval, and `sdlc.py bug-commit` commits the inbox alone, from the main checkout, as
`File <id>`, `Retire <id>` or `Update <id>`, a retired bug's `Sdlc-Retired:` trailer saying why.
`sdlc.py bugs` lists them (`--touching <path>…` to narrow), and `--introduced <path>…` names the
closed change that last touched each path, a candidate for `Introduced by:` and never written
without a person's word. `check` reports a bug with no id, a severity outside the words, or an
`Introduced by:` that names no change, and `status` prints a `■ Bugs` line. A change that fixes one
names it on a `fixes: [<id>]` line in its intent (`/sdlc:intent <id>` writes it); `status` leaves
it out while the change is open, `sdlc.py ship` deletes it with the fix, and `/sdlc:close` writes
an `Sdlc-Fixes:` trailer for it on the `Close` commit.

**What comes next.** `sdlc.py status` ends with a `■ Next up` section: what to start once the open
changes are done, from the main checkout's `work/inbox.md` and direction doc. A
missing file adds nothing. Each entry's heading starts with its id, `## [2026-10-25-3] [idea] Title`:
the day it came in and a count, from `sdlc.py next-entry`, which counts every checkout's register
and every commit that ever held one, so an id is never handed out twice. A heading with a bare
date is an entry from before ids, read the same until 1.4.0: run `migrate-inbox` before. An `idea:`, `After:` or `Groups:` line names an
entry by its id, written bare, or by its title, quoted, and titles are read for good, since the
intents in history name seeds by them; `check` reports an id used twice. Two optional forms in
`work/inbox.md` feed it: `[bug]` in place of `[idea]` marks something already broken, and an
`After: <id>, <id>` line in a seed's body makes it wait while any seed it names is still in the
register and not being built. Each line's command is `/sdlc:intent <id>`. A seed
being built (tagged `[building]`, or named by an open change's `idea:`) is never listed.
Candidates come in this order, each once, under the first rule it meets:

1. `[bug]` entries, most severe first, then oldest;
2. each open milestone's first `Groups:` seed that is ready, in the doc's order;
3. a seed whose `After:` seeds have all left the register, the next in its series;
4. nits of cost `S`, one line per theme, oldest theme first;
5. every other ready idea, oldest first (`idea`).

Five are shown, then a count. Below them, an open milestone whose grouped changes and seeds are all
closed says so, for `/sdlc:retro` to settle, and an `After:` line that can never be met (it names
nothing, or seeds that wait on each other) is a `⚠`, never a `check` problem.

A change may keep its **acceptance checks** in `work/NNN-slug/checks.md`: proof that only a
deliberate revert could break, which the suite shouldn't carry forever. Each `## ` section is one
check holding one `sh` block, which passes when it exits 0 within 300 seconds and leaves the
working tree as it found it. `sdlc.py checks NNN` lists them and runs nothing; `sdlc.py accept NNN`
runs each from the change's checkout root. `/sdlc:ship` lists them after the gate, shows each
command, then runs `accept`, which no skill and no setup allow rule ever pre-approves: an agent may
have written them, so a person sees them and answers the prompt. A failing check stops ship like a
failing gate. The file reaches history and the change's issue with the folder; a check that can't
run (looking at a rendered page) is written in `notes.md` instead.

`.claude/worktrees/` belongs in `.gitignore`, and `work/` must not be in it: `sdlc.py new` refuses
an ignored `work/`, and `sdlc.py check` flags it. The main checkout stays on `main`: close
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
  the counter, the folders in `work/` and the open change worktrees, claimed under a lock. A change
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
  `/sdlc:intent`, `/sdlc:spec` and `/sdlc:ship`, so it shows the change as it is; edit the
  artifacts, never the issue, which the next sync overwrites. A change listed in the intent's
  `depends_on:` line shows as blocking it. `/sdlc:close` renders it a last time, labels it
  `landed` and reads it back before it removes the folder. The issue stays open until the change is on GitHub: the `Close` commit
  says `Closes #N`, so GitHub closes it when that commit reaches the default branch, by
  `/sdlc:publish`, a push of your own, or a merged pull request. Where the default branch isn't
  `main`, close closes the issue itself and says why. An artifact too long for the body becomes a
  comment. A dropped change's issue is closed as not planned.
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
them. `sdlc.py check` reports a field the doc doesn't turn on, and a value outside a fixed list;
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
`sdlc.py check` reports a missing line and an id the doc doesn't have. Each change is held to the
product doc on its own branch, so changes opened before the doc landed owe the line only once they
rebase onto it. `/sdlc:intent` offers only the open outcomes, and each one served gets a line in
the intent's Outcome saying what should change for users if it works:
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
of its own, pushes `main` and the tag, never forced, and runs `release.publish` if the repo has
one, showing at that approval what `release.prepare` built. Every command release and publish
run (`after_bump`, `prepare`, `publish`) runs non-interactively, with no terminal, stdin closed
and its output captured: one that asks a question fails at once, so give it its non-interactive
flag, or build in `prepare` and keep `publish` to the upload. It is the only step in the plugin that pushes. A repo without a tag for its current version
is told the `git tag -a` command that makes one; a repo with no `version_files` gets the listing
and nothing else. Dropped changes are never released.

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
*Unreleased*; it never counts them as problems, so `check --strict` stays a gate for the change in
hand. A bad entry is reported, and blocks a release, rather than raised. Without the file nothing
changes. A path kept for good (the no-manifest drift, and whatever reads what history holds,
which never migrates) is not a shim and has no entry.

## Retrospectives

`sdlc.py status` says **Retro due** after `retro.after_releases` releases since the last one (2
by default), or after any major release, and never runs it for you. `sdlc.py retro` counts, from
history, everything since the last `Retrospective YYYY-MM-DD` commit: the changes closed and
dropped (tier, impact, size, days open, the first paragraph of each problem, what they cost),
rework (leaving out the files more than a third of them touch, listed apart), open changes and
seeds, release tags, the size of each skill, and what each change cost, from its `Close` commit's
trailers. Its `bugs` are the bugs reported, fixed and retired in the window, by severity and
reason, the days from report to fix, the open ones by age, and the escapes: each introducing
change with its tier, and how many no one tied to a change.

`/sdlc:retro` makes five passes over that (cost, architecture, process, product, direction),
turns every finding into a seed, an intent title or a reason for dropping it, and after one
approval rewrites the direction doc (`docs.direction`), the product doc's outcome lines when there
is one, and appends the seeds. `sdlc.py retro-commit` commits those files and nothing else, as the
next retrospective's boundary. It never edits code, skills or the process doc.

Goals and milestones in the direction doc keep ids across retrospectives (`- G1. …`, `### M1. …`
with a `Groups:` line naming its changes and seeds), and each one ends struck through as `Done`,
`Dropped: <reason>` or `Revised → M5: <reason>`, never silently gone: `retro` reports what each
milestone's seeds and changes became, and `retro-commit` refuses a doc that drops an open id.

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
(gates, questions and anything else that waited on the person) against the gates the way of
running requires (by hand or by the factory) plus `metrics.stop_allowance`, and tokens per stage and
per sub-agent role. Ship adds its review's findings as an `Sdlc-Findings` trailer on its own
commit.

Close also records whether the change went through first time: `Sdlc-Happy` says, per stage, yes,
no or unknown, and `Sdlc-Rework` counts the trial and error inside the change (the spec or plan
edited after their stage, `revise` answers, failed gate runs, ship reruns, lines written against
lines kept, and for the factory its rounds, verdicts and decisions). Exploration you mean to throw
away goes under `stage: spike`, which owes no artifact; its cost is reported apart as
`Sdlc-Spike`, never as rework.

The bugs a change fixes are recorded too, one `Sdlc-Fixes: <id> severity=<w> reported=<date>
introduced_by=<NNN-slug|unknown>` line each, from its intent's `fixes:` and the entry as the
branch last held it; a bug retired without a fix gets `Sdlc-Retired: <id> severity=<w>
reported=<date> reason=<word>` on its `Retire` commit. A dropped change fixes nothing.

`sdlc.py retro` reads all of them. Measuring never stops a close: without transcripts,
`Sdlc-Coverage` says why, and the numbers are what history gives. `git log --format=%B` on a
`Close` commit shows them.
