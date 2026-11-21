---
id: 206
slug: update-skill
kind: spec
created: 2026-11-21
updated: 2026-11-21
---

# 206 — A host learns of a new release and updates in one consistent run · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

What this spec takes as given, each one checked in the code or left for the plan to confirm:

- *Checked.* `plugin_version()` reads the running copy's manifest from `PLUGIN_DIR`
  (`Path(__file__).resolve().parent.parent`), so the running version is a file read. `_older()` and
  `SEMVER_RE` (`^\d+\.\d+\.\d+$`) already compare versions. `setup_nudge()` is status's only nudge
  about the plugin, and it compares `.sdlc/setup.json` with the running copy, nothing newer.
  `factory_enabled()` reads `enabledPlugins` from three settings files and runs nothing. Both
  plugins release as one version (`test_the_factory_depends_on_sdlc_and_shares_its_version`).
  `.claude-plugin/plugin.json` names `repository: https://github.com/faeldon/sdlc`. sdlc's manifest
  has no `hooks` key, and `test_sdlc_loads_nothing_from_plugins` asserts there is no `hooks/`
  folder. That test changes in R1.
- *Checked.* State that no tree may hold already lives in the git common dir (`_ledger_dir()`, the
  gate slots, the main lock). A cache kept there dirties no checkout and is shared by every worktree.
- *For the plan to confirm, by recording a real one first (REVIEW.md, "A transcript's shape assumed,
  not read"):* the output of `claude plugin list` (`--json` if it exists, its text otherwise) for an
  install at user scope, one at project scope, sdlc-factory, and a local-path marketplace. Also: that
  a SessionStart hook's `{"systemMessage": …}` is shown to the person, and that a cached copy under
  `~/.claude/plugins/cache/` has no `.git` entry. The requirements below assume these hold. If one
  doesn't, the plan says so and the spec comes back.

Nits taken in: none

1. **R1. The plugin ships one SessionStart hook.** `hooks/hooks.json` at the plugin root holds
   exactly one hook. Its event is `SessionStart`, its matcher is `startup`, and its one command is
   `uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py update --hook` with a timeout.
   The manifest gains no `hooks` key. `test_sdlc_loads_nothing_from_plugins` changes from "no
   `hooks/`" to "`hooks/` holds only `hooks.json`, and it holds only that hook". The changed test
   fails if a second hook, another event, or a `hooks` key in `plugin.json` appears.
   `claude plugin validate --strict` passes.
2. **R2. The hook only advises.** `update --hook` exits 0 every time and prints either nothing or
   one JSON object whose `systemMessage` is one line. It never runs `claude plugin update` or
   `marketplace update`, and it writes nothing but its cache (R4). A test runs it with `claude`
   missing from PATH, with `git ls-remote` failing, and outside a git repo. Each time it must exit 0
   and print nothing, and the test fails on any output or non-zero exit.
3. **R3. The line.** When a fresh check finds a release newer than the running copy, the line reads
   exactly `sdlc <latest> is out (this session runs <running>): /sdlc:update`. Suppose instead the
   running sdlc is current but an sdlc or sdlc-factory install that applies to this repo (R6) is
   older. Then the line reads `sdlc <latest> is out (<plugin> <version> at <scope> scope): /sdlc:update`.
   Several stale installs are joined with `, ` inside the one pair of parentheses. The test against
   the faked `claude plugin list` (R13) asserts each form character for character.
4. **R4. At most one network check a day, cached in the git common dir.** The latest release is
   `git ls-remote --tags --refs <repository>`, where `<repository>` is the running manifest's
   `repository`. The newest tag matching `v?X.Y.Z` wins. The command runs with
   `GIT_TERMINAL_PROMPT=0` and a short timeout. Its answer is cached with the installs from R6 and a
   UTC timestamp in `sdlc-update.json` in the git common dir. Within 24 hours of that timestamp, the
   hook and `status` read the cache and run neither `git ls-remote` nor `claude`. A test records
   every argv and fails if a second hook run on the same day runs either. A failed check is cached
   as `latest: null` with its reason, so being offline is retried tomorrow, not at every session.
5. **R5. A plugin read in place is never told to update.** When the running copy has a `.git` entry
   (a clone registered as a marketplace from its path, or a `--plugin-dir` worktree), the hook
   prints nothing, `status` shows no update line, and `update` reports `"in_place": true` with no
   steps. It also runs no `git ls-remote`, since a clone's version is whatever its checkout holds.
   A test with a `.git` in the fake plugin root fails if any line, step or network call appears.
   In this repo, `update` reports `in_place` (Verification).
6. **R6. Installs that apply here.** `plugin_installs()` is the one reader of `claude plugin list`.
   It resolves `claude` with `shutil.which` (so Windows finds `claude.cmd`), runs it with
   `encoding="utf-8"` and a timeout, and returns
   `[{plugin, scope, version, project, local_source}]` for `sdlc@sdlc` and `sdlc-factory@sdlc`. An
   install applies here when its scope is `user`, or `project`/`local` with a project path equal to
   this repo's `main_root()`. Both paths are normalised with `Path.resolve()` and compared
   `as_posix()`, never as raw text. Any failure gives `[]` and a reason, never a traceback.
7. **R7. `status` repeats the line from the cache alone.** `update_nudge()` builds the R3 line from
   the cache and the running version, and `status` prints it beside `setup_nudge()`'s line. It runs
   no `claude` and no `git ls-remote`, and it shows nothing when the cache is missing, stale,
   `latest: null` or `in_place`. A test refuses any subprocess argv starting with `claude` or
   holding `ls-remote` during `cmd_status`, and asserts the line appears with a fresh cache.
8. **R8. `sdlc.py update` reports this host's exact steps.** With no flag, it refreshes the check
   now (ignoring the day's cache, and writing it) and prints JSON with `running`, `latest`,
   `checked`, `in_place`, `installs` (every one found, each marked whether it applies here),
   `restart_first` and `steps`. `steps` is, in order:
   - `claude plugin marketplace update sdlc`;
   - one `claude plugin update <plugin>@sdlc --scope <scope>` per install that applies here and is
     older than `latest`, sdlc before sdlc-factory, user scope before project before local, each
     run from `main_root()`;
   - `restart Claude Code`;
   - `/sdlc:setup`;
   - `commit what setup names`.

   Installs at project or local scope in other repos go in `elsewhere`, never in `steps`. The test
   uses two scopes plus sdlc-factory plus another repo's project install, and fails if a step is
   missing, duplicated, out of order, or names the other repo. With everything current, `steps` is
   empty.
9. **R9. `update --installed` tells setup whether to restart.** It runs `plugin_installs()` fresh,
   with no network and no cache write. It reports `restart_first: true` when an sdlc install that
   applies here, at the most specific scope found (`local`, then `project`, then `user`), is newer
   than the running copy. It reports `null` with a reason when it can't tell. A test fails if a
   newer project install over an older running copy gives anything but `true`, or if a missing
   `claude` gives anything but `null`.
10. **R10. `update` is not read-only, and the docs say so.** It writes the cache and reaches the
    network, so it is not in `READ_ONLY` or `ALLOW_RULES`, and setup proposes no rule for it. The
    existing `READ_ONLY` test keeps passing unchanged. AGENTS.md's map gains a paragraph naming the
    hook, the cache in the git common dir, and the fact that the cache is the one write made with
    no WAIT outside the existing five, because it is state, not an artifact.
11. **R11. `/sdlc:update` runs the steps behind one WAIT.** `skills/update/SKILL.md` exists, is in
    `GATED`, and has `disable-model-invocation: true`. Its description says when not to use it
    (inside the plugin's own clone, or to refresh a repo's docs, which is `/sdlc:setup`). Its Step 0
    runs `config` and `update`. Its READS_CONFIG entry is `factory.enabled`: an enabled factory with
    no install found is said, not hidden. It prints the steps, then asks one `AskUserQuestion` WAIT:
    `Run these claude plugin commands: <commands>? (yes / no)`. After a yes it runs each command as
    its own Bash call (`cd "<main checkout>" && claude plugin …`) and stops on the first failure.
    Then it tells the person to restart and run `/sdlc:setup`. It commits nothing and pushes
    nothing. Its `allowed-tools` holds a rule for each command, written as it runs:
    `Bash(claude plugin marketplace update sdlc)`, `Bash(claude plugin update sdlc@sdlc --scope *)`,
    `Bash(claude plugin update sdlc-factory@sdlc --scope *)`, plus the script's `config *` and
    `update *` rules and `Bash(cd *)`. `tests/test_skills.py` passes with the skill added and fails
    on a missing or unused rule. With `in_place` true or `steps` empty, the skill says so and stops
    before the WAIT.
12. **R12. Setup refuses to refresh on a stale session and names the commit.** Setup's Step 0 also
    runs `sdlc.py update --installed`. When `restart_first` is true, setup says
    `restart first: this session runs <running>, <installed> is installed` and stops before drafting
    anything. `null` doesn't refuse. `readiness` gains `uncommitted`: the paths setup owns (config,
    `.sdlc/setup.json`, `.claude/settings.json`, `.gitignore`, every doc in `setup.json`'s `docs`,
    the files in its `created`) that have uncommitted changes, read through git, `as_posix()`. It
    does not change `complete`. Setup's `complete` stop and its Step 6 report each end with the
    commit, `git add <uncommitted> && git commit -m "Refresh the sdlc setup for <plugin version>"`,
    whenever `uncommitted` isn't empty. Tests: `readiness` on a repo with a modified `setup.json`
    and `settings.json` lists both, and a clean one lists none. The setup skill's text names
    `update --installed`, `restart first` and `uncommitted` (a test fails if a refactor drops one).
13. **R13. One test runs the detection end to end, offline.** It uses a fake `claude` on PATH that
    prints the recorded `plugin list` output (user plus project scope, sdlc-factory, a local-path
    marketplace) and a bare repo in `tmp_path` tagged `v1.10.0` and `v1.11.0` as the `repository`.
    It runs `update --hook` and asserts the exact R3 line. It then asserts a second run the same day
    calls neither and prints the same line. It is not `portable` (shebang fake). The pure parts
    (`plugin_installs()` parsing, `update_nudge()`, the line) have `portable` tests built from the
    recorded output.
14. **R14. The recorded shape is the fixture.** The fake `claude`'s output in R13 is a real
    `claude plugin list` output recorded once, in neutral paths, with no machine or home path
    (`test_nothing_local`). A comment says which Claude Code version printed it.
15. **R15. The docs describe the same sequence the command prints.** README *Updating* and
    REFERENCE.md *After an update* both list R8's five steps in that order. They name `/sdlc:update`,
    the `--scope` per install, the restart, and the commit, and say what the hook and `status`
    print. `docs/FEATURES.md` and `docs/PROCESS.md` gain the `update` command, skill and hook, and
    `tests/test_feature_map.py` fails until they do.
16. **R16. Windows.** No new top-level platform import, every `subprocess.run` names
    `encoding="utf-8"`, the cache is written with `newline="\n"`, and `tests/test_windows.py` passes
    unchanged.

## Design

**One module of logic, in `sdlc.py`.** Everything mechanical sits beside `setup_nudge()` and
`plugin_version()`:

- `release_source()`: the running manifest's `repository`, or None.
- `in_place()`: whether `PLUGIN_DIR / ".git"` exists.
- `latest_release(source)`: `git ls-remote --tags --refs`, the highest `SEMVER_RE` match after an
  optional `v`, or None with a reason.
- `plugin_installs(home)`: R6.
- `update_cache(home)`: reads and writes `sdlc-update.json` under `_ledger_dir()`, with the
  24-hour check.
- `update_report(home, fresh)`: the JSON of R8.
- `update_line(report)`: R3.
- `update_nudge(home)`: R7.

`cmd_update` maps `--hook`, `--installed` and no flag onto these. Nothing here imports anything of
the factory's. sdlc-factory's version comes only from the `claude plugin list` row, so `factory.py`
is untouched and ships no hook of its own.

**The hook.** `hooks/hooks.json` at sdlc's root is the default location Claude Code loads, so the
manifest needs no `hooks` key. The factory's copy is rooted at `plugins/factory/` and never carries
it. On `startup` it runs `update --hook`. With a fresh cache that is one `git rev-parse` and a file
read. Once a day it is one `git ls-remote` and one `claude plugin list`, each under its own timeout,
inside the hook's own timeout. Any exception is caught at `cmd_update`'s top for `--hook` alone.
There it prints nothing and exits 0, so a broken check never shows a traceback at session start.

**The cache.** The file is `sdlc-update.json` in the git common dir:
`{"checked": "<UTC ISO>", "source": "<url>", "latest": "1.11.0" | null, "reason": …,
"installs": [...]}`. It is one per repo, shared by every worktree, and never in a tree. Outside a
git repo there is nowhere to keep it, so the hook checks nothing there. That keeps the promise of
one check a day without writing outside the repo.

**Setup.** Step 0 gains one call (`update --installed`) and one stop rule. Step 6 and the
`complete` stop gain the commit from `readiness`'s `uncommitted`. Setup still writes only behind its
Step 4 WAIT and commits nothing.

**The skill.** `/sdlc:update` is a thin reader of `update`'s JSON, with one WAIT before the
`claude plugin` commands. It runs each step as its own Bash call, so no loop is needed. Each command
runs from `main_root()`, because `--scope project` acts on the folder it runs in, and a session in a
change's worktree is in another folder. The running session keeps the old copy after the commands,
so the skill ends by telling the person to restart and run setup. Setup's R12 refusal catches anyone
who skips the restart.

**Edge cases.** A downgrade (running newer than latest) shows no line. An empty tag list or an
unreadable `repository` gives `latest: null`. A factory that is enabled but has no install row is
reported by the skill, not the hook. Repos whose project-scope install isn't this one go in
`elsewhere`, and the skill names them for the person to update from there.

## Contracts touched

- **Nothing runs unasked.** The rule as written is the board's: no model starts a server. A hook is
  run by Claude Code because the person enabled the plugin, and it only reads, cached a day at a
  time. It still runs code and reaches the network at every new session in every repo with the
  plugin enabled, and the plugin has never done that before. That is a widening for a person to
  approve, not a side effect. The design stays inside it only by advising, by the daily cap, and by
  silence when unsure. If the answer is no, detection lives in `update` and `status` alone (see
  Alternatives).
- **Writes before a WAIT.** AGENTS.md names five. The cache in the git common dir is a sixth write
  made with no question. It is state like the main lock or the records ledger: no artifact, nothing
  committed, no checkout dirtied. R10 names it in AGENTS.md rather than leaving it implied.
- **`test_sdlc_loads_nothing_from_plugins`.** It pins "no `hooks/`" so that sdlc's copy never widens
  what it loads. R1 changes that pin to "exactly this one hook", which keeps its point (nothing of
  `plugins/factory/` loads). This is an edit to a test that enforces an invariant, so it is said
  here.
- **Narrow `allowed-tools`.** There is one rule per `claude plugin …` command, written as it runs,
  and no plain `Bash`, loop or brace group (R11).
- **Only the named steps push.** Neither the skill nor `update` pushes or commits.
- **Mechanism in `sdlc.py`.** Choosing installs, scopes, steps and the restart check is the
  script's. The skill only shows the steps and runs them.
- **Every script call is literally `uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py`.**
  That covers the hook's command too.
- **The scripts run on Windows** (R16). `claude` is resolved with `shutil.which`, never `shell=True`.
- **`readiness`'s `complete` errs towards false.** `uncommitted` is reported beside it and never
  changes it, and `test_the_set_up_fixture_is_complete` stays green.
- **Nothing about a project.** Fixtures use neutral paths, and no host is named. `intent.md` as
  written names a host and one of its changes by number, which this invariant forbids in the repo.
  See the questions below.
- **`claude plugin validate --strict`** must accept `hooks/hooks.json` (Verification).

## Alternatives rejected

- **The GitHub releases API, or `gh release list`.** It needs `gh` or a token, it is rate-limited,
  and it ties the check to GitHub. `git ls-remote` needs only git, which every host has.
- **The marketplace folder's `plugin.json` as the latest version.** It is only as new as the last
  `claude plugin marketplace update`, the step hosts skip, so a host that never runs it would never
  hear of a release.
- **Detection only in `status` and setup.** A host that never runs `status` never hears. This is the
  fallback if the hook is refused: `update` refreshes the cache, and `status` reads it.
- **A hook in sdlc-factory too.** `factory.py` can't import `sdlc.py`, so the logic would need a
  second pinned copy. sdlc's hook already sees the factory's install row.
- **Printing `!` commands for the person to run.** The problem's transcript shows the same commands
  run fine from inside a session. The skill runs them behind its WAIT and prints them first, so a
  refused WAIT still leaves the person the steps.
- **Updating every repo on the machine.** A project-scope install is that repo's, and its settings
  change is that repo's commit. Other repos are listed, not touched.
- **The restart check in `readiness`.** It would make `readiness` run `claude`, and readiness is the
  file-only reader setup's fast path trusts.
- **Inferring the installed version from `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`
  folders.** Old versions can linger there, and it can't say which scope applies here.
- **A per-machine cache under `~/.claude/`.** That writes outside the repo with no WAIT.
- **Updating from the hook.** The constraints forbid it.

## Verification

- `./check.sh` is green: ruff, the format check, `pytest -n auto`, and
  `claude plugin validate --strict` accepting `hooks/hooks.json`.
- `uv run --group dev pytest -q tests/test_update.py tests/test_skills.py tests/test_feature_map.py
  tests/test_windows.py` passes. The R13 end-to-end test prints nothing to the network: the bare
  repo is in `tmp_path`, and the fake `claude` is on PATH.
- `uv run --group dev pytest -q -m portable` passes, the parsing and line tests included.
- In this repo, `uv run --quiet --script scripts/sdlc.py update` prints `"in_place": true`,
  `"steps": []`, and runs no `ls-remote`. `update --hook` prints nothing and exits 0.
- In a scratch repo with the plugin installed from GitHub at an older version, a new session shows
  the one R3 line. `/sdlc:status` repeats it. `/sdlc:update` lists five steps and asks its WAIT.
  After running the commands without a restart, `/sdlc:setup` says `restart first`. After the
  restart, setup's report ends with the `git add … && git commit -m "Refresh the sdlc setup for …"`
  line naming `.sdlc/setup.json` and `.claude/settings.json`.
- `uv run --quiet --script scripts/sdlc.py vet --strict` passes.
```

---

**Questions resolved, from the code or the problem's evidence:**
- *Where "latest release" comes from:* `git ls-remote --tags --refs` on the running manifest's `repository`, cached once a day in the git common dir. A host with no network or no `gh` sees nothing: the failure is cached as `latest: null` and retried the next day. The marketplace folder and the releases API were rejected (see Alternatives).
- *Whether a skill can run `claude plugin update` mid-session:* yes. The problem's transcript shows the same commands run from inside a session. The skill runs them behind its WAIT and prints them first. The restart is still needed, and setup's refusal enforces it.
- *How setup tells the running copy is older:* it compares `plugin_version()` (the running `PLUGIN_DIR`) with the sdlc install that applies here in `claude plugin list`, at the most specific scope. That is `update --installed`.
- *Every repo or only this one:* only this repo, plus user scope. Project and local installs in other repos are listed in `elsewhere`, never updated from here.

**Questions left for you:**
- *Is a plugin-shipped SessionStart hook acceptable under "nothing runs unasked"?* The design assumes yes, because it only advises, checks at most once a day, and stays silent when unsure. It widens what the plugin does at every session in every repo, and the pinned test changes with it. A no keeps detection in `/sdlc:update` and `status` only, and drops R1–R4's hook parts.
- *An off switch for the hook.* None is designed, to stay inside the intent. A `[updates]` config key, or relying on Claude Code's own hook settings, would let an offline or privacy-minded host stop the daily check. Adding a key is a REFERENCE.md and `CONFIG_KEYS` change.
- *`intent.md` names a host repo and cites one of its changes by folder number.* The "nothing about a project or a workspace" invariant forbids both anywhere in the repo, and this folder is committed and archived to an issue. It should be reworded to neutral terms before ship. The spec doesn't repeat either name.
- *Claude Code behaviour this spec assumes (R14, the plan's first step):* the real shape of `claude plugin list` output (and whether `--json` exists), that a SessionStart `systemMessage` reaches the person, that a cached copy has no `.git`, and that `--scope project` is keyed to the folder it runs in. If one turns out false, the spec comes back.
