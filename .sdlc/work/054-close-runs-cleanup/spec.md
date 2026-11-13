---
id: 054
slug: close-runs-cleanup
kind: spec
created: 2026-11-13
updated: 2026-11-13
---

# 054 — Close runs the repo's cleanup when its gate approves it · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1.** `[commands] close_cleanup_runs` is a new boolean key, `false` by default, validated like
   `BOOL_KEYS`. A non-bool value is a `config` warning and reads as `false`. With it `true` and no
   `close_cleanup`, `config` warns, and nothing runs.
2. **R2.** `sdlc.py close` reports `cleanup: {command, runs}` when `close_cleanup` is set.
   `command` is the one that would run: `{id}` filled in, and a leading `!` with its whitespace
   stripped. `runs` is `true` only when `close_cleanup_runs` is on. `--check` reports the same, so
   the skill's question can name it word for word. A test pins `--check` and the real run
   reporting the same `command`.
3. **R3.** With `runs` true, close runs `command` as its last step, `cleanup`, after
   `delete branch` and after `push`, for a shipped change and for a dropped one. It runs as
   `_sh(command)` from the main checkout, with the session's environment, `stdin` closed,
   `encoding="utf-8"`, `errors="replace"` and a `CLEANUP_TIMEOUT` of 600s. It runs whether or not
   `close_list` found anything. A test asserts it runs after the worktree and branch are gone.
4. **R4.** A leading `!` is stripped, never passed to `sh`. A test pins it: `"! false"` reports a
   failure, not success.
5. **R5.** A cleanup that exits non-zero, times out or can't start is `cleanup_failed` in the
   report, with its reason (exit code and the tail of its stderr), and close still exits 0. `done`
   lists `cleanup` only when it exited 0. Tests cover each case.
6. **R6.** The cleanup runs only within a close that reaches its last step. `--check` never runs
   it, a refusal or a failed step before it never runs it, and exit 3 (the worktree kept) doesn't
   reach it. Because the change's worktree is gone once it runs, a rerun of close can't find the
   change and so never runs it twice. Tests pin `--check` and a failed step.
7. **R7.** The command and the switch are read from the base branch's config as it stood before
   the merge: `.sdlc/config.toml` at `refs/sdlc/base/<branch>` for a shipped change, and at the
   base branch's tip for a dropped one, whose `Drop` commit keeps the base branch's tree. A change
   that edits `close_cleanup` or `close_cleanup_runs` therefore takes effect from the next close,
   and a rerun after the merge still runs what the question named. When that config can't be
   read, nothing runs: the report says why and hands the command over as today. A test lands a
   change that turns the switch on and asserts its own close doesn't run the cleanup.
8. **R8.** With the switch off, or no `close_cleanup`, close's report and the skill's question are
   unchanged from today. The existing close tests pass untouched.
9. **R9.** `skills/close/SKILL.md` behaves as follows:
   - Step 1 shows the command when `cleanup.runs` is true.
   - Step 2's question gains `…, then run <command>` (before `then push` when both apply), so the
     yes covers it.
   - Step 4 reports `cleanup` done, or `cleanup_failed` with the command handed to the human to
     rerun.
   - With `runs` false it hands the command over as today, only when `close_list` found something.

   "Never run it from this session" stays: the script runs it, never the skill's bash.
   `allowed-tools` gains nothing.
10. **R10.** `docs/REFERENCE.md` documents the key and the `!` rule, and lists `close_cleanup`
    among the commands `sdlc.py` runs itself when the switch is on. AGENTS.md's **Closing**
    paragraph names the `cleanup` step. `.sdlc/setup.json` matches (`sdlc.py drift` reports
    nothing). `./check.sh` passes.

## Design

**Config.**

- `CONFIG_KEYS["commands"]` gains `close_cleanup_runs: False`, and `BOOL_KEYS` gains
  `close_cleanup_runs`.
- `close_cleanup`'s comment changes to "{id}; handed to the human, or run by close when
  close_cleanup_runs".
- The parsing in `load_config()` is split into a function over TOML text, so
  `_config_at(home, ref)` reuses the same validation on `git show <ref>:.sdlc/config.toml`. It
  returns `None` when the file or the ref is missing, or the TOML won't parse.

**The plan.** `_cleanup_plan(home, cfg_at, number)` returns `{command, runs}`, or `None` when
`close_cleanup` is unset. It fills `{id}` and strips `^!\s*`. `cmd_close()` builds it before
`--check` returns:

- for a shipped change, from `_config_at(main, start)` when the ref exists;
- under `--check`, or when that ref is missing before the merge, from `cfg`, which is the same
  config before the merge;
- for a dropped change, from `_config_at(main, trunk)`;
- when nothing can be read after the merge, from no config at all: `runs: false` with a
  `because`.

**The step.** `cleanup()` runs after the loop and after `push()`, like `push()`, never as a
`steps` entry. A failure sets `report["cleanup_failed"]`, never a refusal or exit 1. It is reached
only on the path that returns 0. The `merged` handoff reruns close with the merged code, which
reaches the cleanup in the innermost run, reading its config from the ref per R7.

**The skill.** It reads `cleanup` from `close --check`'s JSON, which it already shows in Step 1,
and from the final report in Step 4. `close_list` stays the skill's own, run as today.

## Contracts touched

- **Close's WAIT step (always Tier 2).** The question gains a clause naming the exact command.
  The yes approves it for this change only, and the setting alone never runs anything (R2, R6,
  R9).
- **Nothing runs unasked; logic a permission rule must cover lives in the script.** The script
  runs the cleanup inside `sdlc.py close`, which the person already approves. No skill bash or
  `allowed-tools` rule gains a command that writes.
- **What a host already has means (always Tier 2).** `close_cleanup` keeps its meaning, and its
  new behaviour is behind a new key that is off by default (R8). The `!` strip applies only when
  close runs the command, so a host handing it over sees no change. `RETIRED_KEYS` and
  `TEMPLATE_READS` need nothing.
- **Close deletes only the change's folder, worktree and branch.** This change widens that: close
  now runs the host's command, which may delete whatever the host's command deletes. The policy
  text in AGENTS.md and the skill's Out of scope change with it, and the widening applies only
  behind the host's opt-in and the person's yes.
- **A failed step stops close; a push failure doesn't.** The cleanup follows `push_failed`: the
  change has landed.
- **Windows.** It runs through `_sh()` with `encoding="utf-8"` and `errors="replace"`, and is
  never `shell=True`.
- **`main` is never written into a git call.** `_config_at()` takes the ref or `trunk`.

## Alternatives rejected

- **Run it from the skill's bash.** That needs an `allowed-tools` rule for a host's command that
  writes, which is always Tier 2, and the harness and a host's guard would see an arbitrary
  command rather than `sdlc.py close`.
- **Make `close_cleanup` itself switch on running.** That would change what an existing host's
  key means. A host set it to be handed over.
- **A `git.push`-style list of points.** There is one point. A list would only spell a boolean.
- **Run it before `remove worktree`.** A cleanup could then delete what the worktree holds before
  git's own refusing removal gets to look, and a failure would land between steps that rerun.
  Last means nothing of the change is at stake.
- **Refuse a leading `!`.** It is the documented example, so every host that copied it would be
  refused at its first close with the switch on.
- **Run it only when `close_list` found something.** The person chose to run it on every approved
  close: the listing is advisory, and the cleanup is the host's own idempotent command.
- **Read the switch from the post-merge config.** A change could then turn on its own cleanup,
  and a rerun could run a command the question never named.

## Verification

- `uv run --group dev pytest -q tests/test_sdlc.py -k "close"`: the new tests for R1–R8 pass, and
  the existing close tests pass unchanged.
- `uv run --group dev pytest -q tests/test_skills.py`: R9's skill text is pinned,
  `READS_CONFIG["sdlc:close"]` names `commands.close_cleanup_runs`, and no new `allowed-tools`
  rule appears.
- `uv run --quiet --script scripts/sdlc.py drift` reports nothing.
- `./check.sh` exits 0.
