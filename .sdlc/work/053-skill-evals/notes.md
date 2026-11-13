# 053 — Behavioural evals for the core skills · notes

> What building it turned up that the spec didn't say: deviations, and what's left undone.

## Deviations from the spec

- **No command name holds `eval`.** The harness refuses any command line containing the word from a
  worktree session, so the suite runs through `sdlc.py run-cases`, and the read-only command is
  `cases` (spec R6–R10 renamed while planning).
- **`cases` isn't in `READ_ONLY`, and ship has no rule for it:** `READ_ONLY` is what setup proposes
  to every host, which has no suite; ship reads the scope from `preflight` and the scores from
  `run-cases`' own output, so a `cases` rule would be one nothing runs.
- **A change's scope is passed as `--tag`, never `--case`:** the CLI's `--case` takes one glob, and a
  second replaces the first (the first debug run ran only the last case named).
- **Each run grants `Bash`, `Write` and `Edit` and runs one arm** (`--allow-tools`, `--ablation
  none`): a case's `allowed_tools` grants nothing, and the default second, no-plugin arm doubles
  the cost.
- **The scaffold readies uv in the run's temporary home** (`--sandbox`, cases only): the sandbox has
  no network, and macOS's `/usr/bin/python3` shim can't run in it, so a uv config there makes uv
  use a Python it installed and an offline cache in the workspace, warmed by the scaffold. macOS's
  `/usr/bin/git` shim fails the same way; the skills recovered by finding Homebrew's git, which
  costs a few turns.

## Undone

- [x] The approve-path cases (spec R3, R5, R6): a case that continues a stop case's transcript with
  `yes`. The native transcript is in a kept run's `config/projects/*/<session>.jsonl` (the
  `trace.jsonl` beside it is stream-JSON), and it ends at the WAIT as needed, but it carries the
  machine's absolute paths (the plugin root in every command), so it can't be committed
  (`test_nothing_local.py`) or replayed elsewhere. The likely design: histories kept out of git,
  captured per machine before a run, and approve cases skipped while theirs is missing.
  → seed: 2026-11-13-1
