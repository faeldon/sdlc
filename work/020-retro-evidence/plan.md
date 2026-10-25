---
id: 020
slug: retro-evidence
kind: plan
created: 2026-10-25
updated: 2026-10-25
---

# 020 — Give this repo's retrospective evidence to score its outcomes · plan

## Context

`retro.evidence` is empty in `.sdlc/config.toml`. The 2026-10-24 retrospective therefore scored
none of O1–O4 in `.sdlc/PRODUCT.md`, and milestone M1 ("The retrospective has evidence") is open.
O1 and O2 are measured by GitHub issues: issues against setup, `new` or close per release (O1), and
issues reporting lost work or a duplicated number (O2). Today every issue is a change's own
tracking issue (`sdlc` label), and nothing marks a reported bug. The person chose:
- labels: the stock `bug` plus `area: setup`, `area: new`, `area: close` (O1), and `lost-work` (O2);
- a Python script with a test, not inline `gh | jq`.

Settled in planning (struck in the intent):
- **O3 needs no command.** `retro`'s `metrics.groups` already reports `target` and `over` per tier.
- **O1's adoption test needs no command.** `./check.sh` runs it on every change.
- **The window is per release.** Each `v*` tag's time closes a window, plus an `unreleased` one,
  as O1's measure says.

## Changes (all in the 020 worktree)

1. **`.sdlc/evidence.py`** (new), with a PEP 723 header and no dependencies, run with
   `uv run --quiet --script`. Under `.sdlc/`, not `scripts/`, so no host's cached copy carries it.
   - `tag_times(root)`: `git for-each-ref refs/tags/v* --sort=creatordate
     --format=%(refname:short) %(creatordate:iso-strict)`.
   - `bug_issues()`: `gh issue list --state all --label bug --limit 1000 --json
     labels,createdAt,state`. It asks for no title, body or author, so none can be printed.
   - `count(issues, tags) -> list[dict]`, pure. It drops issues that carry `sdlc`. Each issue goes
     to the first tag at or after its `createdAt`, else to `unreleased`. Each window counts
     `reported`, `open`, `area: setup`, `area: new`, `area: close` and `lost-work`.
   - `render(rows) -> str`: one line per window, such as
     `v1.1.0  reported=0 open=0 setup=0 new=0 close=0 lost-work=0`, plus a header line naming
     what it counts (non-sdlc `bug` issues by release window).
   - `main()`: if `gh` or `git` fails, it writes the error to stderr and exits 1, so retro shows a
     row with an exit code and never fails.
2. **`.sdlc/config.toml`**: under `[retro]`, add
   `evidence = ["uv run --quiet --script .sdlc/evidence.py"]`, with a one-line comment naming the
   labels it counts.
3. **`tests/test_evidence.py`** (new): loads `.sdlc/evidence.py` by path with `importlib`, as
   `test_metrics.py` loads `metrics.py`. It covers `count` and `render` with neutral fixture
   dicts:
   - `sdlc` issues are excluded;
   - an issue created exactly at a tag's time falls in that tag's window;
   - an issue after the last tag goes to `unreleased`;
   - area and `lost-work` counts, and the `open` count;
   - no tags at all gives one `unreleased` window;
   - `render` prints counts only.
4. **`docs/CONTRIBUTING.md`**: a short "Bugs and the retrospective" note next to the GitHub-issues
   paragraph (~line 88). It says that triage labels a reported bug `bug` plus its area or
   `lost-work` (a reporter can't set labels), and that `.sdlc/evidence.py` counts them for
   `/sdlc:retro`.
5. **GitHub labels**, an outward write approved by approving this plan. Run once:
   `gh label create "area: setup"`, `"area: new"`, `"area: close"`, `"lost-work"`, each with a
   description. Before creating them, run `gh label list` to check they don't already exist.
6. **The change's own files**:
   - save this plan as `work/020-retro-evidence/plan.md`;
   - in `intent.md`, strike the four open questions with how each was resolved, and set
     `stage: build`.

## Not in scope

- The bugs register and the intake seeds, which later replace this script's source.
- An issue template.
- Any `scripts/sdlc.py` change.

## Verification

- `uv run --quiet --script .sdlc/evidence.py` from the worktree: it exits 0 and prints the windows
  `v1.0.0`, `v1.1.0` and `unreleased`, all zeros.
- With the config in place, from the worktree:
  `uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py retro | jq .product.evidence`
  shows one row with `exit: 0` and no `error`. `retro` reads `main_root`'s config, so if this row
  is still empty, verify by running the command directly and confirm again after close.
- `uv run --group dev pytest tests/test_evidence.py -q`, then `./check.sh`, which covers ruff,
  format, the full suite including `test_nothing_local` and `validate --strict`.
- Then `/sdlc:ship 020`.
