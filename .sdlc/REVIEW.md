# Review

> The sdlc plugin's own additions to the review guide, which `/sdlc:ship` reads with this file
> (`docs.review.guide` in `sdlc.py config`). Each block here, a heading or a `- **lead**` bullet,
> stands in for the guide's block of the same heading path, or lead, when it holds text of its
> own, and is read after its parent's block there when the guide has none like it. A heading with
> nothing under it only places what follows.

## Pass 1 — Correctness

### The ways this repo's code fails

- **A skill and its rules drifting apart.** A command in a bash block with no `Bash(...)` rule
  written exactly as it runs, a rule nothing runs, plain `Bash`, or an `if`/loop/brace group a rule
  can't cover. Logic that needs branching belongs in `sdlc.py`. The script called any way but
  `uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py`.
- **A writing skill with zero or two WAIT headings**, or a write that happens before it.
- **A config key a skill reads without running `sdlc.py config`**, or one missing from
  `READS_CONFIG`; a host specific guessed instead of asked.
- **Frontmatter round-tripped.** Anything that rewrites `intent.md` through `frontmatter.dumps()`
  turns `id: 001` into `1`, reorders keys and writes `idea: null`; `stamp_shipped` edits lines in
  place.
- **An id matched by string.** A prefix match or `[:3]` instead of `names_change()`: ids are three
  digits *or more*, and GitHub numbers run past 999.
- **A change folder looked up anywhere but `change_dirs()`**, or a worktree's inherited copy of
  `main`'s folders counted as that change. A change's folder lives on its own branch, in its own
  worktree; `main_root()` is for state, the lock and the worktree list.
- **A fallback from GitHub numbering to local**, or any path that can hand one number out twice.
- **Closing that can lose a change:** a folder removed before the change's commit is on `main`, or
  before a configured mirror reads back; an issue touched without matching number, label and
  marker; a rerun that posts a comment twice; a non-zero exit treated as archived; a dropped branch
  deleted before its `Drop` commit makes its commits reachable from `main`.
- **Bad input raised in a host repo.** `check` and `status` report unparseable frontmatter as a
  problem; a traceback there is a broken pipeline.
- **A dependency added to the PEP 723 block and not to the `dev` group** (or the reverse), or
  anything that only works because this repo has a `.venv`, a `Makefile` or a GitHub remote.
  `tests/test_adoption.py` is the check; a change to `new`, `ship` or `close` should still pass it.
- **A destructive git flag** in close: `--force`, `-D`, any merge but `--ff-only`, and
  `-s ours --no-ff` for a `Drop` commit only.
- **A project cited**: a host by name or as the one the plugin came from, a change by its bare
  folder number. Test data uses neutral examples.

## Pass 2 — Contract

Does the change stay inside the invariants in `AGENTS.md` (`[docs] policy`), under
*Invariants the tests enforce*? Check each one the diff comes near. If the change genuinely
*needs* one to move, that's an edit to the policy with its own reasoning in `spec.md`, not a quiet
exception.

Two apply everywhere:
