# Setup — drafts

> What setup reads when it has something to draft: a first setup, a repo that isn't
> `complete`, or the argument `product`, `project` or `reset`. `SKILL.md` names this file in
> its Step 0 and holds the WAIT that approves every draft below.

## What `drift` found

`drift` compares what setup copied with this plugin's defaults, block by block (each section, each
`- **lead**` bullet), against the record `.sdlc/setup.json` keeps of what setup last offered. It
sorts what it finds three ways, and Step 3 keeps them apart in that order:

- **`breaking`**: what the plugin would now misread: a config key a release retired, a template
  override in `.sdlc/templates/` that lacks a heading or key the script reads, a project or product
  doc it can't parse. Each comes with its `fix`.
- **`refresh`**: per host doc, the blocks the plugin changed that the host never touched
  (`added`, `refreshed`, `removed`), and `proposed`, the whole doc with them taken and every
  other block exactly as the host wrote it.
- **`report`**: what only a person can decide: a block both sides changed (`conflict`), a block
  that differs where there's no record to say who changed it (`differs`, `base: none`), a config
  key the plugin doesn't read (`unknown`) or one new since the record (`new`), a plugin template
  that changed under an override (`changed`). For the process and review docs, which hold only
  this repo's answers (`layout: answers`), only two: the plugin's guide changed since the record
  (`guide-changed`, a note to read, never a refresh), and a block whose heading the guide has
  nowhere (`unknown`), which no reader can place.

Blocks the host wrote (`own`), edited (`edited`) or took out (`host-removed`) are listed under
`docs` and never proposed back.

## The arguments

**`product` or `project`**: that doc is the one item to draft, even though `readiness` reports
it `ok` while it's off, and Steps 1 to 6 run for it alone, without the profile round. A doc that
already exists is never rewritten: propose additions as a diff.

**`reset <doc | template | all>`** puts the plugin's default back where the host changed it: a doc
by its `docs` key (`process`, `review`, `health`, `product`, `project`), a template override by its
file name (`intent.md`), or `all` of both. For a doc, the draft is its default again with every
`<` prompt filled the way a first setup fills it (Steps 1 to 3), and above it the blocks the reset
loses: each one `drift` lists as `own` or `edited`, shown as a diff, so nobody loses an edit
without seeing it. The process and review docs hold nothing but this repo's answers to the
plugin's guide, so `drift` lists none of their blocks: every block but the title and note is what
the reset loses, shown as the whole doc against the template. A repo set up before 1.5.0 holds a
whole copy of the guide there, which the skills read twice; its reset is how it gets back to
answers, carrying over only what it changed. For an override, there's nothing to draft: the reset deletes it and the
plugin's template is used again, so show the override against `templates[...]` in `config` and
what it loses. A reset is a write like any other, behind Step 4.

## Step 1 — Learn the repo

Read it the way `/init` does: the README, the task files `candidates` came from, the test layout,
the main entry points, and enough of the code to see its architecture. Look too at the CI workflow
files (`.github/workflows/`) and any release or install scripts: they are the candidates Step 2
offers for the risky paths. Read the existing
`CLAUDE.md` or `AGENTS.md` (`docs.policy`, and anything in `docs.context`) in full if there is
one. This is what
the drafts in Step 3 are made from; a draft written without it is a template with the blanks
guessed.

## Step 2 — Ask only about the gaps

**First, what kind of repo this is.** On a first setup (`readiness`'s `config` item is `missing`:
there is no `.sdlc/config.toml` yet), open with three questions in one round, each with a
proposed answer. A repo already set up skips them, even with other items `missing`. They decide which optional
docs Step 3 drafts and what goes in them. Nothing records them: no config key holds the answers,
so a later setup reads what was written, not what was said.

- **Kind:** *lightweight* (a throwaway, a spike, a personal tool) or a *product* (it has users
  who aren't the person running it). Propose it from Step 1's reading of the README and what the
  code serves.
- **Who runs it:** *one person* or a *team*. Propose a team only when Step 1 found a `CODEOWNERS`
  file (`Glob`) or a README that names maintainers; otherwise propose one person.
- **Where changes are tracked:** *GitHub* or *local*. Propose local for a lightweight repo. For a
  product, propose GitHub when `readiness`'s `archive` is `github` and its `gh auth` is `ok`;
  otherwise local.

**Then attribution, whenever `config`'s `git.attribution` is null**, a first setup or a later one
(`readiness`'s `attribution` item says `not chosen`): ask "Should Claude's attribution appear in
this repo's commits and pull requests? (on / off)". Propose no answer: it is the host's to make,
and the answer is written down, so it is asked once.

Then one short round, only for what Step 1 couldn't settle:

- **The gate** (`commands.check`): which candidate it is, or the command if none fits. It's the
  gate `/sdlc:ship` runs on this diff, pass or fail: fast, offline, no side effects.
- **The slow gate** (`commands.build` and `commands.build_when`): a second gate, run when a
  changed path matches: anything needing real services or data, and the paths that should trigger
  it. None is a fine answer.
- **Scans** (`commands.scan`): what looks for drift across the whole repo. `/sdlc:health`
  runs it, and it produces findings rather than a pass or fail. A repo task named `doctor` or
  `health` is usually this, not the plugin's own `readiness`. And **worktree setup**
  (`commands.worktree_setup`): what a fresh worktree lacks that the repo's tools need. None is fine
  for either.
- **Risky paths** (`review.sensitive` and `review.irreversible`): the paths whose changes always
  get `/sdlc:ship`'s deep review (a fresh-context reviewer, the slow gate whatever `build_when`
  says, the paths named in its question), and the paths a revert doesn't undo (migrations, data,
  what's published or copied elsewhere), for which ship's commit says how to recover. Offer
  candidates Step 1 found: CI workflow files, release and install scripts, `migrations/`. Each entry
  is a `dir/` prefix or an fnmatch glob. None is a fine answer for either, and ship then reviews
  every change alike.
- **The invariants**: what a design here must never break. These go in the policy doc
  (`docs.policy`: `CLAUDE.md`, or `AGENTS.md` when that's the repo's only one), which ship's
  contract pass reads.
- **Numbering and archive** (`archive.target`): from where changes are tracked, which also
  decides where their numbers come from. GitHub sets `target = "github"`: each change is numbered
  by its issue. Local sets `target = "none"`, the default written out so the choice reads in
  the file: the counter numbers changes, nothing is mirrored and close files no issue. When the person picks GitHub and `readiness`'s `gh auth` isn't `ok`,
  still set github, and say that `/sdlc:intent` refuses until `gh auth login` has run. Never leave
  it local in its place: a repo that later moves to GitHub would hand out a number twice.
- **The base branch** (`git.base`), only when `config` gives it as null (`git.base_source` is
  `unset`: no `main`, and `origin/HEAD` names no local branch): which branch every change starts
  from and lands on. Every change refuses to start until it is set.
- **Evidence** (`retro.evidence`), only when a product doc is being drafted: commands that print
  what users did with the product, as counts and summaries, for the retrospective's product pass.
  Ask; never guess them from task files. None is a fine answer, and the pass then has only the
  history.
- **Indicators** (`retro.indicators`), only when `config` gives it empty: commands that print
  figures only a language can tell (function hotspots, complexity, dependency cycles) for the
  retrospective's architecture pass, each line a JSON row, `{"name": "src/drafts.py::save",
  "value": 3, "unit": "commits"}`, which its report shows as a table against the last
  retrospective's. Propose what Step 1 found a tool for. None is a fine answer, and the report
  then says no indicators are set.

Propose an answer for each from what Step 1 found; the human corrects rather than composes.

## Step 3 — Draft everything

Each item `readiness` reported as `missing` or `warn` gets a draft. Show new files in full and every
edit to an existing file as a diff. A doc drafted from a default keeps the `>` note under its
title: it says what the plugin reads from the doc, which whoever edits it later needs.

- **`.gitignore`**: a `.claude/worktrees/` line, where each change's worktree lives. Never `.sdlc/work/`:
  a change's artifacts are committed with it, and `readiness` reports an ignored `.sdlc/work/`.
- **`.sdlc/config.toml`**: only the keys that differ from their defaults, each with a comment
  saying why. Include `[archive] target`, either way. Include `[git] base` when the base branch
  isn't `main`: the branch Step 2 was given, or the one `config` detected (`git.base_source` is
  `detected` and `git.base` isn't `main`), so a later change to `origin/HEAD` never moves it.
  Include `[git] attribution` when Step 2 asked: `true` for on, `false` for off. Include
  `[review] sensitive` and `[review] irreversible` when Step 2's answer named any, and
  `[retro] indicators` when Step 2's answer gave a command.
- **The process doc** (`docs.process`, `.sdlc/SDLC.md` by default): start from `defaults.process`,
  this repo's answers to the plugin's guide (`docs.process.guide`), which the skills read with it.
  Fill in every line that starts with `<`. Those are where this repo differs: the failure it most
  needs to stop, its always-Tier-2 carve-outs, its gate and slow gate, how a commit reaches its
  users. A prompt whose answer is the guide's is deleted, its heading kept. Copy a block of the
  guide in only to change it here. A `<` line left in is a blank the human has to fill.
- **The review passes** (`docs.review`, `.sdlc/REVIEW.md`): start from `defaults.review`, this
  repo's additions to the plugin's review guide (`docs.review.guide`), and list the ways this
  repo's code actually fails, found in Step 1: what its tests guard against, what its history
  fixes. Don't invent failure classes the code gives no sign of.
- **The health doc** (`docs.health`, `.sdlc/HEALTH.md`), when `readiness` reports it
  `missing`, which it does only once there is a scan. Start from `defaults.health`, and fill its
  table from what Step 1 found the scan checks (its task file, its script) and what the human says
  it reports: each finding, what it means here, and the response tier it usually gets. Fill its
  blind spots from what the scan needs to reach. Setup never runs the scan, and a finding nobody
  can explain yet is left out, not guessed.
- **The project doc** (`docs.project`, `.sdlc/PROJECT.md`), for a team tracked on GitHub, or
  with the `project` argument; `readiness` reports it `ok` and off while absent. One person needs
  none (each change's issue is assigned to whoever opens it), and a local repo has no issue for
  its fields to go on: say so in Step 6 rather than drafting it. When it's drafted, start from
  `defaults.project` with `assignees: tracker` uncommented in its frontmatter, and ask whether
  each change's issue also takes a milestone (`milestone: tracker`) or a project; uncomment those
  named, with the lookup each one uses. Fill in each field's section from the answers: who is
  assigned (whoever opens a change, an owner per area), and what decides the milestone. Delete
  the section of a field left off, so no `<` prompt is left behind.
- **The product doc** (`docs.product`, `.sdlc/PRODUCT.md`), for a product, or with the `product`
  argument; `readiness` reports it `ok` and off while absent. A lightweight repo gets none. Start
  from `defaults.product`, and interview for it the way `/sdlc:intent` does for an intent, asking
  only what Step 1 left open, with its reading of the README as the proposals:
  - **Users:** who reaches for this, and what they're trying to get done.
  - **Problem:** what's hard for them without it, in their terms rather than the code's.
  - **Outcomes:** two or three, `- O1.` on, each with a short `name` in bold
    (`- O1. **Unaided setup.** …`), two or three words a person remembers, and `Measured by:`
    with the signal that says so. Every skill shows the name beside the id, as
    `O1 (Unaided setup)`, so propose one with each outcome.
    Push back once on an outcome that is a feature in disguise ("add an export" is a feature;
    "users get their data out without asking for help" is an outcome), then take their answer.
  - **Bets:** no question of their own. Draft one or two from what the outcomes assume, for the
    human to correct.

  Say that from then on every open change needs a `serves:` line, and add the `retro.evidence`
  commands to `.sdlc/config.toml`.
- **Lightweight**: no product or project doc. Everything else above and below is drafted as it
  would be for a product, and every gate stays.
- **`AGENTS.md` and `CLAUDE.md`**: when the repo has neither, write the guide as `AGENTS.md`, which
  other coding agents read too, by `/init`'s rules: the commands to build, lint and test,
  including one test alone; the architecture that takes several files to see; nothing generic,
  and no file listing. Add an **Invariants** section with Step 2's answers. Then a `CLAUDE.md`
  holding only `@AGENTS.md`, so every Claude Code version loads it, and `docs.policy = "AGENTS.md"`
  in `.sdlc/config.toml`, since that `CLAUDE.md` holds no invariants. When the repo has either
  file, never rewrite it and never add the other: propose the Invariants section, or other
  additions, to that one as a diff. If the human would rather keep invariants out of it, set
  `docs.policy` to a separate file instead.
- **`.claude/settings.json`**: the rules `readiness` lists under `permissions.missing`, merged into
  `permissions.allow`, keeping everything already there. They cover only the script's read-only
  subcommands; everything that writes keeps asking. With attribution off, also the object
  `readiness` gives as `attribution.merge`, as the file's `attribution` key, exactly as given:
  never `"attribution": false`, which older Claude Code rejects along with the whole file. Say
  that the file is shared: it is committed and applies to everyone who works in the repo. A
  `.claude/settings.local.json` that sets its own attribution wins over it, which `readiness`
  warns about; that file is each person's, never setup's to edit.
- **Issue forms**, only when `archive.target` is `github`: each of `readiness`'s `issue_forms`
  not yet `present`, copied from its `from` file to its path under `.github/ISSUE_TEMPLATE/`, with
  the bug form's `<severities>` line replaced by one `- <word>` option per word of the process
  doc's severities, most severe first. They give a person filing an issue the fields
  `/sdlc:triage` reads into an entry. One already `present` is the repo's: never redraft it. Once
  written, both are the repo's too: no later setup proposes changes to them, and
  `/sdlc:uninstall` leaves them.
- **What the plugin update changed** (`drift`), on a repo already set up. Show `breaking` first,
  each with what it breaks and its `fix`: a retired key is edited to the key that replaced it, an
  override lacking a heading or key gets it back (or a `reset`). Then each `refresh` doc as one
  diff from the host's text to its `proposed`, naming each block taken and whether the plugin
  `added`, `refreshed` or `removed` it. Then `report`, with no edit drafted: for a `conflict`,
  both texts side by side, for the human to merge by hand or leave; for `differs`, that there is
  no record of who changed the block, so it's theirs to judge; for `new` keys, the default and
  where `docs/REFERENCE.md` says what it does. A `report` item the human asks to take becomes a
  draft like any other, and goes back through Step 4.

Then Step 4 in `SKILL.md`: the WAIT that approves every draft above.
