---
id: 018
slug: base-branch
kind: spec
created: 2026-10-25
updated: 2026-10-25
---

# 018 — Let a host name its base branch · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **One resolved base.** `load_config()` resolves the base branch once, and `config` prints it as
   `git.base` with a `git.base_source` of `config`, `detected` or `unset`. When
   `.sdlc/config.toml` sets `[git] base`, that value wins. When it doesn't, the base is `main` if
   `refs/heads/main` exists; otherwise the branch `refs/remotes/origin/HEAD` points at, if that
   branch exists locally; otherwise it is unset. Each case has a test.
2. **No literal `main` left.** Every git call in `scripts/sdlc.py` that means the base branch reads
   the resolved value. A test greps `sdlc.py` for `"main"`, `refs/heads/main` and `..main` used as
   a ref and finds none. Prose, `main_root` and `main_checkout` don't count.
3. **No base, no issue.** When the base is unset, or `refs/heads/<base>` doesn't exist,
   `new --worktree` refuses before it claims a number. No issue is opened and no counter moves.
   The refusal names `git.base` and what it resolved to. A test with a fake tracker asserts
   `claim()` was never called.
4. **The drop is reported.** The tracker's `drop()` returns why it failed, or None when it
   succeeded. `new` prints the outcome of every drop it makes: `closed <url> (not planned:
   <why>)`, or that the issue is still open and to close it by hand. A dropped issue loses its
   `stage:` label, in an edit of its own whose refusal is skipped, never fatal. A test covers each
   case. Today `new` prints only the failure and the `opened` line, so the reporter took a closed
   issue for an open one, still labelled `stage: plan`.
5. **Ship's base step.** `cmd_base` rebases onto, or fast-forwards to, the resolved base. Its
   refusals name that branch. Tested in a repo whose only branch is `master`.
6. **Close.** Close requires the main checkout to be on the resolved base. It fast-forwards that
   branch, and `--is-ancestor` and `rev-parse` read it. The `Drop` merge lands on it.
   `closed_changes()`, `dropped_changes()`, `_close_times()` and `_drop_commit()` walk its
   first-parent line.
7. **Release, publish and retro.** Release and retro-commit require the resolved base to be checked
   out. `unreleased()`, the retro boundary and `tag --merged` read the base. Publish's "moved past
   the tag" check reads it, and publish pushes `refs/heads/<base>` and the tag, nothing else.
8. **The base reaches the tracker.** Core passes the base in the `change` dict. The GitHub
   tracker's `_landing()` compares GitHub's default branch to it instead of to its `MAIN`
   constant, so a host on `master` whose GitHub default is `master` gets `Closes #N` behaviour,
   not close-it-ourselves.
9. **Other readers.** `status`'s "behind" count, `nits --change`, `context --base`, `new --base`
   and `_own_script()`'s merge base all default to the resolved base. An explicit `--base` still
   wins.
10. **The skills say the right branch.** Intent's approval question and Step 5, ship's base step,
    close's question and report (`git log -2 --oneline <base>`), drop's question, release's prose,
    and publish's question and limits all name the base from `config` (`git.base`).
    `READS_CONFIG` lists `git.base` for each of those skills, and the existing test enforces it.
11. **Setup pins it.** When `git.base_source` is `detected` and the base isn't `main`, setup
    proposes writing `[git] base = "<branch>"` behind its existing WAIT. When it's `unset`, setup
    asks for the branch. A host on `main` gets no new line.
12. **The adoption test.** A copy of `test_adoption.py`'s run from new through close, in a scratch
    repo whose only branch is `master` with no config key, passes. Through `config`, a main-only
    repo sees `git.base: "main"`, `detected`.
13. **Reference.** `docs/REFERENCE.md` documents `[git] base`, the detection order and what refuses
    when the base is unset. AGENTS.md says in one line that `main` in it means the resolved base.

## Design

**Resolution.** A new `git` section in `CONFIG_KEYS` holds `base: None`. After the config is
parsed, `load_config()` resolves it:

```
base = cfg["git"]["base"]
       or ("main" if rev-parse --verify -q refs/heads/main)
       or (origin/HEAD's short name, if refs/heads/<it> exists)
       or None
```

`cfg["git"]["source"]` records which rule gave the answer. Resolution needs at most two `git`
calls, against `home`; branches are shared by every worktree, so a worktree's `root` gives the
same answer.

A helper, `base_branch(home, cfg) -> str | None`, reads it back. Every site in the inventory takes
the base from it or from a parameter that caller already resolved, so nothing calls git to find the
branch a second time. Functions that take `main: Path` for the checkout keep that name. The branch
is a separate `base: str` argument, threaded down from each command's one `load_config()`.

**What resolution never does.** It never uses the main checkout's current branch,
`init.defaultBranch` or a branch GitHub reports. The first two are about one machine, not the repo.
The third is a network call, and core never calls `gh`.

**Refusing early.** In `cmd_new`, the base check runs right after the `work_ignored` check and
before `ids_mode`/`claim`:

- unset → `⚠ no base branch: set [git] base in .sdlc/config.toml`
- missing → `⚠ base branch 'X' doesn't exist here (git.base, <source>)`

An explicit `--base` is checked the same way. `claim()`'s local path and `_add_worktree` stay as
they are. They can still fail for other reasons (the path already exists), which is why the drop
has to be loud too.

**The tracker.** `drop(url, why) -> str | None` closes the issue as not planned and returns
stderr when `gh` fails. It then removes the issue's `stage:` label in a separate
`gh issue edit`, whose refusal is skipped, as `sync` skips its edits, so a closed issue doesn't
still read `stage: plan`. `new` prints the outcome either way: `closed <url> (not planned: <why>)`,
or the URL as still open, to close by hand. `claim()`'s own internal drop is reported the same way.
`_landing()` reads `change["base"]`, and `MAIN` goes. `_tracker_change()` adds `base`. The tracker
still never reads `.sdlc/`.

**Commands that need the base and don't have one.** `base`, `close`, `release`, `publish`,
`retro-commit` refuse with the same message as `new`. Read-only `status`, `unreleased` and `retro`
report it as a problem and skip the branch-based parts rather than crash.

**Skills.** Each bash block stays a plain command. The skill reads `git.base` from the `config`
JSON it already prints in Step 0 and says the name in prose and questions. No shell variable, so
`allowed-tools` doesn't change. Close's `git log -2 --oneline main` is a prose instruction under the
existing `Bash(git log *)` rule, so it becomes `<git.base>` in that prose.

**The orphaned issue, for the reporting host.** After this lands, it closes its orphaned issue by
hand (`gh issue close <N> --reason "not planned"`) and reruns `/sdlc:intent`, which takes a new
number. With no config line at all its base resolves to `master` through `origin/HEAD`, and setup
offers to pin it.

## Contracts touched

- **Mechanism vs. policy / config read once.** The base is a host setting, read only through
  `load_config()` and resolved there once. Detection is part of resolving, not a second reader.
- **Only publish pushes.** Publish's refspec changes from `refs/heads/main` to
  `refs/heads/<base>`. It's still two refs and still only in `cmd_publish`. `"push"` stays out of
  every other function, and `test_only_publish_pushes` still holds.
- **Close only fast-forwards; never merge the base into a branch; never stash.** Unchanged. Only
  the branch name moves.
- **`closed_changes()` is the one walk over landed changes.** It walks the base's first-parent
  line. A host that changes `git.base` after changes have closed would walk a different line.
  That's a host's own decision, so REFERENCE says so rather than guarding against it.
- **Numbering never falls back.** This change adds a refusal before numbering, so it doesn't touch
  that. Making the drop loud prevents silent orphans.
- **Trackers never read `.sdlc/`; core never calls `gh`.** The base crosses in the `change` dict,
  and resolution makes no `gh` call.
- **`RETIRED_KEYS` / `TEMPLATE_READS`.** No entry. A key added isn't one retired, and no template
  heading is read. An older plugin seeing `[git] base` warns "unknown key", which is accurate.
- **Nothing local.** Test data uses `master` as a branch name and names no project.
- **Narrow `allowed-tools` and each skill's WAIT.** Not changed. No rule is added or reworded, and
  the questions only swap a word.

## Alternatives rejected

- **Only a config key, no detection.** Every host on `master` would have to know about the key
  before its first intent. That's exactly where the reporter got stuck, after an issue had already
  been opened. Detection plus the early refusal means nobody gets that far.
- **Detect from the current branch or `init.defaultBranch`.** These describe one person's machine,
  and can differ between two people working in the same repo.
- **Ask GitHub for the default branch.** That's a network call from core, it doesn't work with
  `archive.target = none`, and core never calls `gh`.
- **`new --issue N` to adopt an already-opened issue.** It would let a person type a number into the
  numbering scheme. That's the "same number twice" risk the github mode exists to rule out, and
  it's added surface for a one-off. Closing the orphan by hand costs one command.
- **Read `--base` from an environment variable.** It would be invisible in the config and in
  `config`'s output, so skills couldn't name it.

## Verification

```bash
./check.sh
uv run --group dev pytest tests/test_adoption.py -q
uv run --group dev pytest -q -k "base or drop or landing"
```

Healthy output means the gate is green; the master adoption run closes a change and leaves a
`Close NNN-slug` commit on `master`; the grep test finds no literal `main` ref; and `config` in this
repo prints `"git": {"base": "main", "source": "detected"}`.
