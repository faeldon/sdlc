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
./check.sh                                   # the full gate: ruff check, ruff format --check, pytest -n auto, claude plugin validate --strict
uv run --group dev pytest -q -n auto         # tests only, across the machine's cores (pytest-xdist)
uv run --group dev pytest -q -m portable     # what CI's Windows job runs
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

This is the map: the boundaries, and the rules no one function shows. Each rule's detail is said
once, where the pointer leads: `docs/REFERENCE.md` for what a host sees, `docs/CONTRIBUTING.md`
for working on the plugin, `plugins/factory/README.md` for the factory, and a named function's
docstring for the rest. Change a rule there; change this map only when it stops being true.

**Mechanism vs. judgment.** `scripts/sdlc.py` (argparse subcommands) does the mechanical half:
ids, worktrees, scaffolding `.sdlc/work/NNN-slug/`, auditing artifacts against tier and stage,
landing and archiving, listing the context docs a diff touches, reporting whether a repo is set
up. It never writes artifact prose. The skills in `skills/*/SKILL.md` do the judgment and call
it. Logic a permission rule must cover goes in the script, not in a skill's bash.

**Mechanism vs. policy.** The plugin knows nothing about what a host builds. Everything
host-specific comes from `.sdlc/config.toml`, read only by `sdlc.py config`, which
`load_config()` resolves once (every doc path included), so no reader has its own. Skills ask
`config` rather than guessing. `guide/` is read in place and never copied, `defaults/` is copied
into a host once and is the host's after, and `templates/` is the shape of each file the plugin
writes itself, overridable in `.sdlc/templates/`. A host's process and review docs are always its
answers to the guides, read block by block (`doc_units()`). REFERENCE.md, *The docs* and
*Templates*.

**Modules loaded by path.** `retro.py`, `board.py`, `metrics.py`, `indicators.py` and the
trackers are loaded by path, never imported: `uv run --script` and the tests put different
directories on `sys.path`. `retro.py` and `board.py` are bound to a live view of `sdlc.py`'s
globals and call what they share as `sdlc.<name>`, so a test's stand-in reaches them; `board.py`
loads only when `board` runs. `metrics.py` and `indicators.py` are pure: no subprocess and no
import of `sdlc.py`. Each module's docstring is its contract.

**The base branch: `git.base`.** `main` in this file means the base branch a host names in
`[git] base`, or that `_resolve_trunk()` detects (`main`, else `origin/HEAD`'s branch). The code
passes it as `trunk`, since `base` already means a boundary or a merge base there. Never write
`main` into a git call: `test_no_git_call_names_main_itself` fails on one, and a host on `master`
would get stuck at that step. A command that writes asks `trunk_refusal()` first.

**Tiers and stages.** Tier 0 gets no folder, Tier 1 an `intent.md`, Tier 2 `intent.md`, `spec.md`
and `plan.md`. `STAGES`, `TIER_ARTIFACTS`, `SPEC_REQUIRED_FROM` and `PLAN_REQUIRED_FROM` define
what `check` requires. A file with two or more lines starting with `<` is an unfilled scaffold.
Frontmatter values (`id`, `depends_on:`, issue fields) are read as text (`frontmatter_list()`),
never through YAML, which reads `012` as octal 10 and `1.10` as 1.1.

**`.sdlc/work/` is committed, one folder per branch.** A change's folder lives on its branch, in
its worktree at `.claude/worktrees/NNN-slug`, from `new` until close removes it from `main` in a
`Close NNN-slug` commit: history is the copy. Only `/sdlc:close` and `/sdlc:drop` leave the
worktree. `change_dirs()` finds folders, never the copies a worktree inherits; `main_root()` is
for state, the lock and the worktree list. Every path to the folder, on disk and in git, is built
from `work_rel()`, never a literal (`test_no_literal_work_path_in_the_script`). The old `work/`
is `HISTORY_WORK`, named only where history is read, for good: `CHANGE_FOLDERS`,
`next_entry_ids()` and `checkout_of()`. REFERENCE.md, *`.sdlc/work/` and worktrees*.

**Numbering: `ids_mode()`.** It follows the tracker, and never falls back from one scheme to the
other: two schemes hand out a number twice. A local number is claimed under `_main_lock()`, on a
lock in the git common dir that every worktree shares, never in a tree, and `new` writes
`.sdlc/last-id` in the change's worktree, so the main checkout is never dirty (`claim()`,
`next_id()`, REFERENCE.md *Numbering*). IDs are at least three digits: match them with
`names_change()`, never by prefix or `[:3]`.

**Trackers: `tracker()`.** Each is `scripts/trackers/<name>.py`, loaded only when
`archive.target` names it. Core renders the issue (`render_issue()`) and hands the tracker a dict;
a tracker never reads `.sdlc/` (the change folder included), and core never calls `gh`. `sync`
mirrors an open change and never creates an issue. The interface: CONTRIBUTING.md, *Writing a
tracker*; what a host sees: REFERENCE.md, *Trackers* and *The project doc*.

**Writes before a WAIT.** Three, each a named exception to confirm-before-writing: ship's `base`
and `resolve`, which move only the change's own branch and print the undo, and ship's
`findings.md`, which decides nothing. Never a stash (the stack is shared across worktrees), and
never a merge of `main` into the branch, which close would put on `main`'s first-parent line,
where `closed_changes()` walks. `cmd_base()`, `cmd_resolve()`.

**Closing: `cmd_close()`.** Every git step is one git refuses when something would be lost, and
a rerun resumes where a failed step stopped. A refused push is `push_failed` and a failed cleanup
`cleanup_failed`, never a failed close: the change has landed. The host's `close_cleanup` is read
from the base branch's config as it was before the merge (`_config_at()`), so a change can't turn
on its own, and it is the one thing close deletes beyond the change's own folder, worktree and
branch, only behind the question's yes. In this repo, close hands itself to `main`'s script and
then to the merged one (`_handoff()`), and the commands ship runs from a change's worktree to the
change's own script (`_own_script()`): CONTRIBUTING.md, *When a change lands*.

**Dropping.** `/sdlc:drop` writes the reason; `sdlc.py drop` stamps `stage: dropped` and commits
the folder on its branch (`cmd_drop()`); close records it on `main` as a `Drop NNN-slug` merge
that keeps `main`'s tree (`_drop_record()`). `closed_changes()`, and so release, never sees a
dropped change; `dropped_changes()` gives them to `retro`.

**Releasing: `unreleased()`.** `closed_changes()` is the one walk over landed changes, each
`Close` commit on `main`'s first-parent line. `cmd_release` takes every tracked file it changed
into the release commit, which is safe only because `_release_refusals()` refuses a main checkout
with uncommitted tracked changes: loosen that and the release commit sweeps up unrelated work. A
shim in `sdlc.py`, a `RETIRED_KEYS` entry included, gets an entry in `.sdlc/deprecations.toml`; a
path kept for good (whatever reads what history holds) is not a shim. REFERENCE.md, *Releases*.

**Retrospectives: `retro()`.** Read-only but for its report, and bounded by the newest
`Retrospective YYYY-MM-DD` commit, which only `cmd_retro_commit` writes, holding the direction
doc, the register, the product doc and the report, nothing else. It runs the host's
`retro.evidence` and `retro.indicators` (`_evidence()`, the only place they run), so `retro` is
not in `READ_ONLY`. Rework across changes is only what a change declares (`_rework()`); blame's
matches are questions, never counted. `scripts/retro.py`'s docstring; REFERENCE.md,
*Retrospectives* and *The product doc*.

**The board: `scripts/board.py`.** It writes nothing, `stage:` included, serves `127.0.0.1`
alone, and is in neither `READ_ONLY` nor `ALLOW_RULES`: no model starts a server unasked. A change
built by hand moves across its columns by what it touched, whether ship's review ran, and whether
`sdlc.py gate` left a green record on the build as it stands (`_seen()`, `hand_gate()`;
`cmd_gate()` writes `build/gate.md` in `factory.py`'s record shape, its copies pinned by
`tests/test_hand_gate.py`), never by a stage the board stamps. It
reads a factory run's files with copies of `factory.py`'s parsing, pinned by
`tests/test_board.py`, and the page builds every node with `textContent`, never from a string of
HTML. Its docstring; REFERENCE.md, *`.sdlc/work/` and worktrees* (The board).

**The register: `inbox_entries()`.** `.sdlc/work/inbox.md` is the one register of change
requests. Every entry is a seed, and its tag is its kind (`[idea]`, `[bug]` or `[nit]`), so say
"seed" for any entry and "idea" for the kind. Ids come from `next_entry_ids()`, a space of their
own, never a change number. A reference is an id, bare, or a title, quoted (`ref_matches()`,
`same_ref()`); titles are read for good, but never match an entry by title alone.
`inbox-commit` (`cmd_inbox_commit()`) is the only code that commits the register on its own,
always on the base branch in the main checkout, so an entry never rides on a change's branch,
where a drop would lose it. `sdlc.py` only reads nits, and the skills write them. Release,
publish and measuring never read the register
(`test_release_publish_and_measuring_never_read_the_register`). Entries, bugs, nits and their
ranking: REFERENCE.md, *`.sdlc/work/` and worktrees*.

**Intake: `recorded_issues()`.** Each issue the repo records has exactly one record (an entry's
`Issue:` line, a change's `closes:` line, or an `Sdlc-Triaged:` trailer), and `recorded_issues()`
is the one reader of all three and decides what each issue shows; the tracker only sets it. The
record is always committed before the issue is told, so a rerun finishes a run that stopped and
nothing is filed twice. REFERENCE.md, *`.sdlc/work/` and worktrees* (Issues people file).

**Metrics: `scripts/metrics.py`.** Close's `measure` step writes a change's numbers as `Sdlc-*`
trailers on its `Close` commit: numbers and names only. The event list and trailer format are a
contract (the module's docstring): extend them, never redefine. Measuring never refuses: a
failure is `Sdlc-Coverage: none: <reason>`. A change's own numbers are printed only with
`--metrics` (`_lean()`), and every summary is built from the full records first. REFERENCE.md,
*Metrics*.

**Setup: `drift()` and `readiness`.** `sdlc.py record` writes `.sdlc/setup.json` each time setup
writes, and `drift` compares three ways (the default now, the recorded hash, the host's text), so
a block the host changed is never proposed. `breaking` is only what the plugin would now misread:
rename or drop a config key, or make the script read a new template heading, and `RETIRED_KEYS`
or `TEMPLATE_READS` gets the entry in the same change. `git.attribution` has no default on
purpose: unset is a question setup asks. `readiness`'s `complete` lets a rerun read setup's
`SKILL.md` alone, and errs towards false: a wrong true skips a host's setup without a word. The
`setup` case's fixture must stay complete (`test_the_set_up_fixture_is_complete`). A nudge in
`status` is never a problem: `check --strict` is a gate. REFERENCE.md, *After an update*;
`cmd_record()`, `cmd_readiness()`.

**Ship.** Context docs are checked at ship, not close: `sdlc.py context` lists them, and ship
shows an edit with its findings and commits it with the change; close has no `Edit`. Ship reads a
change through one read-only `preflight` call and asks the question `preflight --question` words
(`ship_question()`), never one worded by hand. A new list ship needs is a new part of
`cmd_preflight()`, not a new command in the skill; what only some runs need is a side file
`preflight`'s `branches` names (`SHIP_BRANCHES`), while the WAIT and every rule that binds each
run stay in `SKILL.md`. Ship writes `findings.md` and the script only reads it
(`findings_entries()`); `fix` never reaches a commit. `[review] sensitive` and `irreversible` are
matched by the script (`risk_paths()`), never judged by a skill, and read from the base branch's
config, so a change can't lighten its own review; risk never changes a tier. The fresh review is
`agents/reviewer.md` (`sdlc:reviewer`), the core plugin's one agent, with `Read`, `Grep` and
`Glob` and nothing that writes. Acceptance checks (`acceptance()`) run only through `accept`,
and are never rerun by a later change. REFERENCE.md, *`.sdlc/work/` and worktrees* and *Risky
paths*.

**The skills' cases: `evals/`.** A `claude plugin eval` suite, in this plugin's repo only
(`_cases_report()`). No command name holds `eval`, which the harness refuses from a worktree
session. Every run is a paid model call, so `run-cases` is never in `ALLOW_RULES`, a skill's
`allowed-tools`, `check.sh` or CI. `tests/test_evals.py` builds every fixture and runs `check
--strict` on it, so a script change that breaks one fails the gate, not a paid run.
CONTRIBUTING.md, *The skills' cases*.

**The factory: `plugins/factory/`.** `sdlc-factory`, optional by being installed or not; its
README and `factory.py`'s docstring describe it. `sdlc`'s cached copy carries the folder but never
loads it (`test_sdlc_loads_nothing_from_plugins`), and knows only whether it is enabled, from
Claude Code's settings files (`factory_enabled()`, `config`'s `factory`, nothing run), for intent's
`yes, for the factory`. `factory.py` never imports `sdlc.py`, and
`sdlc` only reads the files a run leaves in a change's folder: each reads the other's files with
copies of its parsing (`risk_paths()` and the regexes included), pinned by tests. Agents that
judge have no Write; only the builder edits (its sub-agents only `Agent(Explore, Plan)`), and no
agent commits. `factory.py agent` is the one place the factory runs `claude`, and `factory.py
gate` the one place it runs a host's command, the base branch's `[commands] check`. Landing is
the one place it commits, through `sdlc`'s own `ship`, `base` and `close` of its own version
(`sdlc_path()`); its gate passes itself only when no change carries a risk signal, recorded as
`Sdlc-Landed: by=auto` (never a bare word, which `parse_trailers` drops), never as the person's.
`verdicts` decides from the rounds alone and reads no state file but `runs/mended`. A builder
report and a behaviour check end with `## Evidence` (`read_evidence()`); a reply missing it, or
holding its verdict after a preamble (`preamble()`), is the one stop a run mends, once a round
for each role (`agent --task mend`, recorded in `runs/mended`). No agent but the builder runs
`checks.md` (`test_no_agent_but_the_builder_runs_checks`). The eval and the
review write only under `.sdlc/reports/`, and never the register.

## Invariants the tests enforce

Changing a skill or the script usually means satisfying these, so know them before editing:

- **Skills** (`tests/test_skills.py`): `name` in frontmatter equals the directory name; the
  description is >80 chars and says when *not* to use it; `disable-model-invocation: true` and
  `allowed-tools` are set. Skills that write (`intent`, `spec`, `ship`, `close`, `drop`,
  `setup`, `release`, `publish`, `retro`, `uninstall`, `bug`, `triage`, `idea`, and the factory's `spec`, `build`, `eval`, `review` and `land`) have exactly one heading
  containing `WAIT`, in `SKILL.md`, which asks its literal question in an `AskUserQuestion` dialog
  (2–4 answers, publish's `no` first, only a chosen yes approves) and as text where none can be
  shown (`test_every_wait_asks_in_a_dialog`); metrics read a dialog's answer in a gated span as the
  gate. A skill's side files (any other `*.md` in its folder) are part of it: `SKILL.md` names
  each, none holds frontmatter, a gate, a commit or `sdlc.py ship`, and the rules below cover
  their commands too. Every call to a script is literally
  `uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/<script>`, never a host interpreter,
  where `<script>` is the plugin's own: `sdlc.py`, or `factory.py` for `sdlc-factory`. Each skill
  must run its script's `config` and name the config keys listed in `READS_CONFIG`.
- **Only the named steps push** (`tests/test_skills.py::test_only_the_named_steps_push`): no
  skill has a `push` rule or runs `git push`; `sdlc.py`'s one git push is in `_push()`, never
  forced, called only by `cmd_publish`, and by `cmd_close` and `cmd_release` through
  `_push_plan()`, so each pushes only when `git.push` names it, behind the question it already
  asks. Ship never pushes.
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
- **This repo's process docs hold only its answers** (`tests/test_defaults.py`): `.sdlc/SDLC.md`
  and `.sdlc/REVIEW.md` are this plugin's own answers to `guide/process.md` and `guide/review.md`.
  Every block sits under a heading the guide has, and none restates the guide's word for word. An
  improvement any repo could use goes into the guide; only what is true of this plugin alone
  stays here. Every answer slot in the guide is a block of its own, keyed as the prompt that asks
  for it in `defaults/` (`test_every_prompt_sits_in_a_guide_slot`), and the guide asks nothing
  itself. A change that edits `defaults/` or `guide/` also runs `scripts/sdlc.py record` from its
  own checkout, so `.sdlc/setup.json` matches what it ships: the gate fails while `sdlc.py drift`
  reports anything here.
- **`stamp_shipped` edits frontmatter lines in place.** Do not refactor it to round-trip through
  `frontmatter.dumps()`: that turns `id: 001` into `1`, reorders keys and writes `idea: null`.
  `tests/test_sdlc.py` pins this.
- **Script dependencies** are declared inline (PEP 723 block at the top of `sdlc.py`) and mirrored
  in the `dev` group of `pyproject.toml`; keep the two in step. `tests/test_adoption.py` runs a
  change from `new` to `close` via `uv run --script` in a bare scratch repo (with `VIRTUAL_ENV`
  dropped) to prove a missing dependency or host assumption would fail.
- **The scripts run on Windows** (`tests/test_windows.py`): no module that exists on one platform
  (`fcntl`, `msvcrt`) is imported at the top of a script, only inside the function that needs it;
  every text-mode `subprocess.run` names `encoding="utf-8"` (with `errors="replace"` for a host's
  commands), since the default is the locale's code page; never `shell=True`, but `_sh()`, which
  is `sh -c` everywhere (`trackers/command.py`'s copy is pinned to it, as `factory.py`'s
  `_utf8_streams` is to `sdlc.py`'s); every `write_text`, and every `open()` that writes text,
  passes `newline="\n"`; a repo path shown or compared with git's output is `as_posix()`. A test that
  must pass on Windows is marked `portable`: CI's Windows job (`.github/workflows/check.yml`)
  runs only those, since the rest lean on shebang fakes Windows can't run.
- The manifest name must stay `sdlc` (it namespaces every skill), and the license `MIT`,
  matching `LICENSE`.

Tests load `scripts/sdlc.py` by path with `importlib`, since it is not an installed module.
