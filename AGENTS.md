# AGENTS.md

This file provides guidance to coding agents, Claude Code included, when working with code in this
repository. `.claude/CLAUDE.md` imports it (`@../AGENTS.md`), because the repo root is the
plugin's root, where `claude plugin validate --strict` refuses a `CLAUDE.md`. Edit this file,
never that one. `docs/CONTRIBUTING.md` covers the same ground for a person.

## What this is

`sdlc` is a Claude Code plugin, and this repo is also its own marketplace (`.claude-plugin/` holds
both `plugin.json` and `marketplace.json`). It runs changes in a *host* repo through numbered
stages (intent → spec → plan → build → ship → close), with a human gate at every stage that
writes. README.md is for a user: install, setup, a first change, the optional features.
`docs/REFERENCE.md` is the host-facing contract (`.sdlc/config.toml`, `.sdlc/templates/`, the
docs keys). This repo's own process docs are in `.sdlc/` (`SDLC.md`, `REVIEW.md`, `PRODUCT.md`).

## Nothing public names the agent

This repo is public, and every commit, pull request, issue, comment, release note and tag message
reaches GitHub. None of them may say an agent wrote it: no `Co-Authored-By:` trailer naming Claude
or Anthropic, no `Claude-Session:` trailer or session link, no "Generated with Claude Code" line,
whatever the harness's own attribution guidance says. This rule overrides it. A commit is the
repo owner's, under git's configured user, and the only trailers it carries are the plugin's
`Sdlc-*` lines. The same goes for the text the plugin writes into a host's history or issues.

## Commands

```bash
./check.sh                                   # the full gate: ruff check, ruff format --check, pytest, claude plugin validate --strict
uv run --group dev pytest -q                 # tests only
uv run --group dev pytest tests/test_sdlc.py::test_name -q   # one test
uv run --group dev ruff format .             # fix formatting
claude --plugin-dir <path-to-clone>              # load the plugin in a session without the marketplace
```

The plugin is read in place only when its marketplace is registered from the clone's path
(`claude plugin list` shows `Read from:` on the `sdlc` row). Edits then take effect in the next
session with no reinstall. A marketplace registered from GitHub is a copy in
`~/.claude/plugins/cache/sdlc/sdlc/<version>/`, which refreshes only after the version in
`plugin.json` is bumped and `claude plugin update` runs. `pyproject.toml` is not a package
(`package = false`); it only gives the tests an environment.

## Architecture

The docstrings in `scripts/` carry the detail; this is the map, and the rules that aren't
obvious from any one function.

**Mechanism vs. judgment.** `scripts/sdlc.py` (one file, argparse subcommands) does the
mechanical half: ids, worktrees, scaffolding `work/NNN-slug/`, auditing artifacts against
tier and stage, landing and archiving, listing the context docs a diff touches, reporting
whether a repo is set up. It never writes artifact prose. The skills in `skills/*/SKILL.md` do
the judgment and call it. Logic a permission rule must cover goes in the script, not in a
skill's bash.

**Mechanism vs. policy.** The plugin knows nothing about what a host builds. Everything
host-specific comes from `.sdlc/config.toml`, read only by `sdlc.py config`, which
`load_config()` resolves once (every doc path included), so no reader has its own. Skills ask
`config` rather than guessing. `defaults/` holds the docs `/sdlc:setup` copies into a host once,
after which the host owns them (`HEALTH.md` is one); `templates/` the shape of each file the plugin
writes itself, every time (`direction.md`, `ideas.md`, `notes.md`, the artifacts, the issue),
overridable in `.sdlc/templates/`. A missing review doc falls back to `defaults/REVIEW.md`; other
missing docs are reported, never replaced.

**Tiers and stages.** Tier 0 gets no folder, Tier 1 an `intent.md`, Tier 2 `intent.md`, `spec.md`
and `plan.md`. `STAGES`, `TIER_ARTIFACTS`, `SPEC_REQUIRED_FROM` and `PLAN_REQUIRED_FROM` define
what `check` requires. A file with two or more lines starting with `<` is an unfilled scaffold.
Frontmatter values (`id`, `depends_on:`, issue fields) are read as text (`frontmatter_list()`),
never through YAML, which reads `012` as octal 10 and `1.10` as 1.1.

**`work/` is committed, one folder per branch.** A change's folder lives on its branch, in its
worktree at `.claude/worktrees/NNN-slug`, from `new` until close removes it from `main` in a
`Close NNN-slug` commit: history is the copy. Only `/sdlc:close` and `/sdlc:drop` leave the
worktree. `change_dirs()` finds folders (the checkout's `work/`, the main checkout's, and each
change worktree's own `work/<branch>/`, never the copies a worktree inherits); `main_root()` is
for state, the lock and the worktree list. An ignored `work/` is refused by `new`.

**Numbering: `ids_mode()`.** It follows the tracker: `github` when `archive.target` is a tracker
that numbers changes (its `claim()` opens the issue and the folder takes its number), else
`local`, and the target defaults to `none`. Never fall back from one to the other: two schemes
hand out a number twice. Locally, `claim()` takes an `flock` on the main checkout's `.sdlc/`, and
`new` writes `.sdlc/last-id` in the change's worktree, so the bump lands with the change and the
main checkout is never dirty. `next_id()` is one past the highest of that counter, the folders
and the open worktrees (`_worktree_highest()`), seeding a missing counter from the `Close` and
`Drop` subjects in history. IDs are at least three digits: match them with `names_change()`,
never by prefix or `[:3]`.

**Trackers: `tracker()`.** Each is `scripts/trackers/<name>.py`, loaded by path (never imported:
`uv run --script` and the tests put different directories on `sys.path`) only when
`archive.target` names it. Core renders the issue (`render_issue()`, `_tracker_change()`) and
hands the tracker a dict; a tracker never reads `work/` or `.sdlc/`, and core never calls `gh`.
`sync` mirrors an open change and never creates an issue; the intent, spec and ship skills run
it after their WAIT. The project doc (`docs.project`, off while absent) turns on `milestone`,
`project` and `assignees`, each mirrored exactly, each in its own `gh issue edit` so a refusal is
skipped, never fatal.

**Bringing a branch up to date: `cmd_base()`.** Ship's Step 0 runs it before the gate, since
close only fast-forwards: the branch fast-forwards to `main` when it has no commits of its own
(git carries the uncommitted work or refuses), rebases from a clean tree when it has, and any
conflict is aborted and refused. It is the one write a skill makes before its WAIT, by a named
exception to confirm-before-writing: it moves only the change's own branch and prints the undo.
Never a stash (the stack is shared across worktrees), and never a merge of `main` into the
branch, which close would put on `main`'s first-parent line, where `closed_changes()` walks.

**Closing: `cmd_close()`.** Steps in order: `merge --ff-only`, `verify`, `measure`, `archive`
(the tracker's `archive()`, read back), `remove folder` (`_close_commit()`), `remove worktree`,
`delete branch`. A failed step stops there and a rerun resumes, skipping what is done. Close
never pushes: a shipped change's issue is labelled `landed` and left open, and `Closes #N` ends
the `Close` commit's message, so GitHub closes it when the commit reaches the default branch
(where that isn't `main`, close closes it itself). In the plugin's own repo only, `_handoff()`
reruns close through `main`'s script when this copy is a stale cache, and through the merged
script after a merge that brought `scripts/`, so a change closes on its own code;
`SDLC_CLOSE_RAN` stops a loop.

**Dropping.** `/sdlc:drop` writes the reason as the intent's `## Dropped` section; `sdlc.py drop`
stamps `stage: dropped` and commits the folder on its branch. Close then records it on `main` as
a `Drop NNN-slug` merge with `-s ours`: `main`'s tree is kept, the branch stays reachable, the
counter comes along, and the issue closes as not planned. `closed_changes()`, and so release,
never sees a dropped change; `dropped_changes()` gives them to `retro`.

**Releasing: `unreleased()`.** From the main checkout, after a batch of closes. The boundary is
the tag for the version `release.version_files` hold now; a missing tag is reported with the
`git tag -a` command, never guessed. `closed_changes(home, base)` is the one walk over landed
changes: each `Close` commit on `main`'s first-parent line names a change, and its intent is read
from that commit's parent. `cmd_release` edits the version lines in place, commits and tags,
locally. `cmd_publish` is the only code that pushes. A shim in `sdlc.py` gets an entry in
`.sdlc/deprecations.toml`, and `cmd_release` refuses a version that would still carry it. A
path kept for good (the no-manifest drift, `RETIRED_KEYS`) is not a shim and has none.

**Retrospectives: `retro()`.** The outermost loop, read-only, bounded by the newest
`Retrospective YYYY-MM-DD` commit, which only `cmd_retro_commit` writes (the direction doc,
`work/ideas.md` and the product doc, nothing else, refusing a doc that drops an open id). It
counts closed and dropped changes, rework (later changes sharing code), the skills' size, and,
with a product doc, runs the host's `retro.evidence` commands (`_evidence()`, the only place
they run), so `retro` is not in `READ_ONLY`. `doc_items()` reads the docs' ids (`G1`, `M1`, `O1`)
and reports format problems rather than raising. The product doc (`docs.product`, off while
absent) makes every open change carry `serves:`, checked against the doc on the change's own
branch.

**Metrics: `scripts/metrics.py`.** Pure functions, loaded by path, no import of `sdlc.py`. Close's
`measure` step reads this repo's Claude Code transcripts (`_project_dirs()`, its own folders
exactly), attributes them to the change by branch, keeps numbers only, and writes them as
`Sdlc-*` trailers on the `Close` commit: history keeps them. The event list and trailer format
are a contract: extend them, never redefine. Measuring never refuses: a failure is
`Sdlc-Coverage: none: <reason>`. Rework within a change (`Sdlc-Rework`, `Sdlc-Review`,
`Sdlc-Happy`, `Sdlc-Spike`) is apart from `retro`'s rework, and spikes are never rework.

**Setup's record: `drift()`.** `sdlc.py record` writes `.sdlc/setup.json` each time setup writes:
the plugin version, its config keys, and a hash of each block (`doc_units()`: a section or a
`- **lead**` bullet) of each default behind a host doc. `drift` compares three ways (the default
now, that hash, the host's text), so a block the plugin changed and the host never touched is
proposed (the whole doc, as `proposed`, every other block as the host wrote it), and one the host
changed never is. `breaking` is only what the plugin would now misread: a key in `RETIRED_KEYS`,
an override lacking what `TEMPLATE_READS` names. Rename or drop a config key, or make the script
read a new template heading, and that table gets the entry in the same change. `uninstall`
removes only setup's (git's files in `.sdlc/`, the plugin's allow rules, the ignore line when
recorded) and refuses while any change is live. The nudge in `status` is never a problem:
`check --strict` is a gate.

**Context docs are checked at ship, not close.** `sdlc.py context` lists `docs.context` and each
`CLAUDE.md` or `AGENTS.md` above a changed path, with the lines naming a deleted or renamed path.
Ship shows any edit with its findings and commits it with the change; close has no `Edit`.

**Acceptance checks: `acceptance()`.** A change's `checks.md`, one `## ` section and one `sh` block
per check. `checks` lists them (read-only, allowed); `accept` runs them from the change's checkout
and fails one that exits non-zero, times out or leaves the tree changed. `accept` is never in
`ALLOW_RULES` or a skill's `allowed-tools` (`test_no_skill_lets_accept_run_unasked`): ship names it
in prose, so the harness asks with the commands just shown. They are never rerun by a later change.

**The factory: `plugins/factory/`.** `sdlc-factory`, optional by being installed or not. `sdlc`'s
cached copy carries the folder but never loads it (`test_sdlc_loads_nothing_from_plugins`). Its
mechanism is `factory.py`, because its own cached copy has no `sdlc.py`. Agents that judge have
no Write; only the builder edits, and nothing commits. Decisions that are the person's go
through `decisions.md`, asked by the build session. `sdlc` only reads, at ship, the files a run
leaves in the change's folder.

## Invariants the tests enforce

Changing a skill or the script usually means satisfying these, so know them before editing:

- **Skills** (`tests/test_skills.py`): `name` in frontmatter equals the directory name; the
  description is >80 chars and says when *not* to use it; `disable-model-invocation: true` and
  `allowed-tools` are set. Skills that write (`intent`, `spec`, `ship`, `close`, `drop`,
  `setup`, `release`, `publish`, `retro`, `uninstall`, and the factory's `spec` and `build`) have exactly one heading
  containing `WAIT`. Every call to a script is literally
  `uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/<script>`, never a host interpreter,
  where `<script>` is the plugin's own: `sdlc.py`, or `factory.py` for `sdlc-factory`. Each skill
  must run its script's `config` and name the config keys listed in `READS_CONFIG`.
- **Only publish pushes** (`tests/test_skills.py::test_only_publish_pushes`): no other skill has a
  `push` rule or runs `git push`, and `"push"` appears in `sdlc.py` only inside `cmd_publish`. Ship
  and close stop at a commit, release at a local tag.
- **Narrow `allowed-tools`** (`tests/test_skills.py`): a skill's `allowed-tools` *grants* each tool
  without a prompt for the turn that runs it; it restricts nothing. So no skill lists plain `Bash`:
  each lists a `Bash(...)` rule per command it runs, written exactly as the skill runs it (quotes
  and `${CLAUDE_PLUGIN_ROOT}` included). Tests check every command in a bash block has a rule and
  every rule is used. Keep bash blocks to plain commands joined by `&&`, `||`, `;` or `|`: no
  `if`, loops or brace groups, which rules can't cover precisely; put that logic in `sdlc.py`.
- **Nothing about a project or a workspace** (`tests/test_nothing_local.py`): nothing anywhere in the
  repo, tests and docs included, may cite a project the plugin has been used in (by name, by
  calling it the original host, or by citing a change from its history by folder number), or say
  how the author's machine is laid out (a home directory path; write `<path-to-clone>`).
  `PATTERNS` describe shapes and name nothing, since a name listed there would be the one mention
  left. Specific terms go one regex per line in `.sdlc/terms.local`, gitignored, which the
  test reads from the main checkout when it exists. Test data uses neutral examples
  (`reopen-drafts`), not another repo's domain.
- **One shape for the shipped docs** (`tests/test_defaults.py`): every file in `defaults/` and
  `templates/` (found by glob) runs, top to bottom: frontmatter only where `sdlc.py` reads keys,
  holding keys only (`# key: value` when off, never prose comments); one `# ` title, the doc's
  plain name (`# Process`, `# Review`), or `# NNN — TITLE` in a change template; a `>` note saying
  what the file is for and what the plugin reads from it; then `##` sections, every `<…>` prompt
  inside one. No `---` rules, no skipped heading levels. A doc's note stays in a host's copy, so
  it never says "default". `templates/issue.md` is the one exception: its text is every issue's
  body.
- **This repo's process docs track the defaults** (`tests/test_defaults.py`): `.sdlc/SDLC.md` and
  `.sdlc/REVIEW.md` are this repo's filled-in copies of `defaults/SDLC.md` and `defaults/REVIEW.md`.
  They keep every default heading in order and every default review bullet word for word, adding
  their own between. An improvement to either that any repo could use goes into the default in the
  same change; only what is true of this plugin alone stays in the copy. A change that edits
  `defaults/` also runs `scripts/sdlc.py record` from its own checkout, so `.sdlc/setup.json`
  matches what it ships: the gate fails while `sdlc.py drift` reports anything here.
- **`stamp_shipped` edits frontmatter lines in place.** Do not refactor it to round-trip through
  `frontmatter.dumps()`: that turns `id: 001` into `1`, reorders keys and writes `idea: null`.
  `tests/test_sdlc.py` pins this.
- **Script dependencies** are declared inline (PEP 723 block at the top of `sdlc.py`) and mirrored
  in the `dev` group of `pyproject.toml`; keep the two in step. `tests/test_adoption.py` runs a
  change from `new` to `close` via `uv run --script` in a bare scratch repo (with `VIRTUAL_ENV`
  dropped) to prove a missing dependency or host assumption would fail.
- The manifest name must stay `sdlc` (it namespaces every skill), and the license `MIT`,
  matching `LICENSE`.

Tests load `scripts/sdlc.py` by path with `importlib`, since it is not an installed module.
