# sdlc — a change pipeline for Claude Code

A Claude Code plugin that takes each change to your repo from an idea to a reviewed commit, in
stages, with you approving every step that writes. You say why a change is worth making; Claude
drafts the spec, plans and builds it, reviews the diff, and stops before anything is committed for
your yes. Changes are sized by risk, so a typo costs nothing and a change that alters what others
rely on gets a spec and a plan.

| Skill | When |
|---|---|
| `/sdlc:setup` | once per repo, and after each update: set it up, or refresh what the update changed |
| `/sdlc:status` | any time: where every change stands, and the one thing to do next. Read-only |
| `/sdlc:intent` | to start a change: say why, in your words; it gets its own worktree and branch |
| `/sdlc:spec` | for a substantial (Tier 2) change: numbered requirements and the design |
| plan mode | to build: Claude reads the code, you approve the plan, then it implements |
| `/sdlc:ship` | when it's built: the gate, a review in passes, one commit |
| `/sdlc:close` | after ship: land it on `main` and tidy away its worktree and branch |
| `/sdlc:drop` | for a change that won't ship: record why, and keep what it cost |
| `/sdlc:idea` | when you think of something for later: file it in the inbox, or edit or retire one |
| `/sdlc:bug` | when something shipped is broken: file it with a severity, or retire or retag one |
| `/sdlc:triage` | when people have filed GitHub issues: check each, then file, attach or close it |
| `/sdlc:health` | now and then: run the repo's scans and route every finding |
| `/sdlc:release` | after a batch of changes: the version they add up to, committed and tagged |
| `/sdlc:publish` | after release: push `main` and the tag, then run your publish command |
| `/sdlc:retro` | after a few releases: look back across them and set the direction |
| `/sdlc:uninstall` | when a repo stops using the plugin: remove what setup wrote, once nothing is open |

Every skill that writes shows you exactly what it will write and asks a literal yes/no question
first. Nothing is pushed except by `/sdlc:publish`.

## Install

You need [Claude Code](https://claude.com/claude-code), git, and
[`uv`](https://docs.astral.sh/uv/): every skill runs the plugin's script through
`uv run --script`, which brings its own dependencies, so your repo needs no Python setup of its
own. For GitHub issues (optional, below), the `gh` CLI, logged in.

The plugin's marketplace is this repo, `faeldon/sdlc`, holding two plugins: `sdlc`, and
the optional `sdlc-factory`.

```bash
claude plugin marketplace add faeldon/sdlc
claude plugin install sdlc@sdlc
claude plugin install sdlc-factory@sdlc   # optional: agents for the change loop
```

## Set up an existing project

From your repo's root, in Claude Code:

```
/sdlc:setup
```

It reads the repo the way `/init` does and first asks what kind of repo it is, proposing each
answer: lightweight (a throwaway, a spike) or a product with users, one person or a team, and
changes tracked on GitHub or locally. Then it asks only what it can't work out (your gate command,
anything slow worth checking separately, what a design here must never break), and drafts:

- `.sdlc/config.toml`: the commands the skills run, such as your test-and-lint gate;
- `.sdlc/SDLC.md`, your answers to the plugin's process guide: the failure your process stops,
  what is always Tier 2 here, your gate, how a commit reaches your users. The guide itself (tiers,
  stages and gates) is read from the plugin, so an update reaches you without a setup diff;
- `.sdlc/REVIEW.md`, what you add to the review passes `/sdlc:ship` works through: the ways your
  code has failed;
- `AGENTS.md`, with a one-line `CLAUDE.md` importing it, when the repo has neither. When it has
  either, setup proposes additions to that file instead;
- a `.claude/worktrees/` line in `.gitignore`, and read-only permission rules in
  `.claude/settings.json`;
- for a product, `.sdlc/PRODUCT.md`, from a short interview about your users and outcomes; for a
  team on GitHub, `.sdlc/PROJECT.md`, with assignees on. A lightweight repo gets neither, and a
  local one is numbered by a counter, with no issues.

It writes after one approval and never commits: it ends by printing the `git add` and
`git commit` for you to run. Run `/sdlc:setup` again any time to check the repo is still set up.

`docs/` stays yours: the plugin's own documents live in `.sdlc/`.

Your default branch needn't be `main`. Setup finds it (a local `main`, else the branch
`origin/HEAD` names) and writes it as `[git] base` when it isn't `main`; wherever these docs
say `main`, they mean that branch.

## A first change

1. **`/sdlc:intent`**, with what's wrong in your own words. It asks only about the gaps, proposes
   a tier, and shows the draft `intent.md`. On your yes it opens the change, numbered `NNN`, in a
   worktree and branch of its own (`.claude/worktrees/NNN-slug`), with its folder
   `.sdlc/work/NNN-slug/`, and moves the session there. Several changes can be open at once, each in its
   own worktree.
2. **`/sdlc:spec`**, for a Tier 2 change only: numbered, checkable requirements, the design and
   what it rejected, inside your repo's invariants.
3. **Plan mode**: start it, let Claude read the code against the spec, approve the plan (it's
   saved as `plan.md`), and let it build. Run your gate as you go.
4. **`/sdlc:ship`**: runs the gate, reviews the diff in passes (correctness against the
   requirements, your invariants, cost, and whether the docs a session reads still tell the
   truth), shows the findings, settles what the change means for a release, and on your yes makes
   one commit holding the code and the change's folder.
5. **`/sdlc:close`**: back in the main checkout, fast-forwards `main`, archives the change, takes
   its folder off `main` in a commit of its own (history keeps it), then removes the worktree and
   branch.

The tiers:

| Tier | For | You write |
|---|---|---|
| 0 | a typo, a comment, a one-line fix | nothing: commit it directly |
| 1 | a small, contained change | `intent.md`, with a short Approach |
| 2 | anything others rely on, or near an invariant | `intent.md`, `spec.md`, `plan.md` |

`/sdlc:status` tells you where every open change is and what to do next, from any worktree. Requests
not ready to be a change go in `.sdlc/work/inbox.md`, where `/sdlc:idea` files them from any
checkout and `/sdlc:intent <id>` can start from one; give one
an `After: <id>` line to make it wait for another, and status's **Next up** puts forward the one to
start once the open changes are done. Something already broken is a bug: `/sdlc:bug` files it
with a severity, and it comes first.

## Optional features

Each is off, or at a sensible default, until you turn it on. `docs/REFERENCE.md` has every setting.

- **GitHub issues.** With `archive.target = "github"` (setup sets it when you track changes on
  GitHub) and `gh`, each change's number is the issue
  `/sdlc:intent` opens for it, so two people never take the same number. The issue follows the
  change through its stages and holds its artifacts once it closes. Without GitHub, a counter in
  `.sdlc/` numbers changes, safe on one machine; your own archive command, or none, can stand in
  for the issue.
- **Issues people file.** On GitHub, setup offers bug and request issue forms, and
  `/sdlc:triage` reads what comes in: it checks each issue against the code, then files it in
  `.sdlc/work/inbox.md`, puts it on the open change that covers it, or closes it as already resolved or
  not to be done, behind one approval. Each filer gets a comment and a parent issue to follow, and
  the change that takes an issue on closes it when it lands, once `/sdlc:ship` has asked.
- **A project doc** (`.sdlc/PROJECT.md`). Gives each change's issue a milestone, a project or
  assignees, chosen from lists the doc names. `/sdlc:setup` drafts it for a team on GitHub, and
  `/sdlc:setup project` adds it later.
- **A product doc** (`.sdlc/PRODUCT.md`). Who the users are and the outcomes you're after, by id.
  Every change then says which outcome it serves, and retrospectives ask whether the work moved
  them. `/sdlc:setup` drafts it for a product, and `/sdlc:setup product` adds it later.
- **Releases.** Each change records at ship whether it is a `major`, `minor`, `patch` or no change
  for your users. `/sdlc:release` proposes the version the closed changes add up to, bumps your
  version files, commits and tags it locally; `/sdlc:publish` pushes it and runs your publish
  command.
- **Retrospectives.** After a couple of releases, `/sdlc:status` says **Retro due**.
  `/sdlc:retro` looks across what shipped (cost, architecture, process, product, direction), rewrites
  the direction doc (`.sdlc/DIRECTION.md`) and turns findings into seeds in `.sdlc/work/inbox.md`. It
  never edits code.
- **What each change cost.** `/sdlc:close` records each change's time, tokens, stops and rework
  on its `Close` commit, read from this repo's Claude Code transcripts on your machine, numbers
  only, never text. `metrics.transcripts = false` turns it off.
- **Dropping a change.** `/sdlc:drop` closes a change that won't ship: it records why and how far
  it got, closes its issue as not planned, and keeps its commits reachable from `main`.
- **The factory** (`sdlc-factory`). Hands a change's spec, build and review to agents working in
  rounds, behind the same approvals; nothing an agent does is committed. See
  [`plugins/factory/README.md`](plugins/factory/README.md).

## Updating

An install is a copy pinned to the version in the plugin's manifest, so it changes only when a
release bumps that version:

```bash
claude plugin marketplace update sdlc
claude plugin update sdlc@sdlc     # "already at the latest version" until the version moves
```

Then run `/sdlc:setup` in each repo that uses it. The docs it copied are yours, so an update
never changes them; setup shows what the new defaults changed, drafts the blocks you never edited,
and lists apart anything the plugin would now misread. `/sdlc:setup reset <doc>` puts one back to
the default. See [After an update](docs/REFERENCE.md#after-an-update-refresh-reset-uninstall).

A repo set up before 1.4.0 keeps its changes in the old `work/` at its root, which 1.5.0 no
longer reads. Move `work/` to `.sdlc/work/` once by hand, in a commit of its own
(`git mv work .sdlc/work`, Move work to .sdlc/work), when no change is open and, if you release,
after `/sdlc:release`.

A repo set up before 1.5.0 has the whole process and review guides copied into `.sdlc/SDLC.md` and
`.sdlc/REVIEW.md`, which 1.5.0 reads after the guides, so every rule twice. Run
`/sdlc:setup reset process` (and `review`) to get back to only what you wrote.

## More

- [`docs/REFERENCE.md`](docs/REFERENCE.md): every config key, the templates, the docs, numbering,
  trackers, releases, retrospectives and metrics.
- [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md): working on the plugin itself, its design, and
  how a change to it is made.

## License

MIT. See [LICENSE](LICENSE).
