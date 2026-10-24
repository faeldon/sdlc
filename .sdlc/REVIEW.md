# Review

> What `/sdlc:ship` works through on every change to the sdlc plugin before it commits. It starts
> from the plugin's `defaults/REVIEW.md`, which is what the plugin ships to hosts, and adds under
> Correctness the ways this repo's own code fails: what its tests guard against. A failure class
> that any repo can hit belongs in the default too.

**Scope:** the diff, and only the diff. Three passes, in order. Stop at the first pass that produces
a blocking finding — fix it and re-run rather than accumulating a long list.

## Pass 1 — Correctness

Does the change do what `intent.md` (Tier 1) or `spec.md`'s numbered requirements (Tier 2) said?
Walk the requirements one at a time; **a requirement with no corresponding code is a finding.** A
requirement with code but no test that would fail without it is one too, unless only a revert
could fail it and `notes.md` records the check that proved it.

Then look for the failures that don't announce themselves:

- **An error swallowed.** A `try` that catches everything, a default returned where a failure was
  meant, a check that passes when the thing it checks is missing.
- **An edge case the requirements name and the code doesn't handle:** empty input, a missing file,
  a second run of something meant to run once.
- **A test that can't fail.** A glob that matches nothing, an assertion on a mock of the thing under
  test, a case skipped by a condition that is always true.
- **A test only a revert can fail.** A test in the suite that checks a file moved, a key renamed or
  a line added: nothing but undoing the change breaks it, so it is an acceptance check, run once
  and recorded in the change's `notes.md`.
- **Behaviour changed where the diff doesn't say so:** a default, an order, a rename that something
  else still reads by its old name.
- **Bad input that crashes.** Input a person or another system can get wrong (a config file, a
  frontmatter line, a request body) raises a traceback where the code promises to report it.
- **Works only here.** A change that passes because of what this machine or checkout has: a local
  file, an environment variable, a tool on `PATH`, a network service the tests happen to reach.
- **A destructive operation where a safe one exists:** a force flag, a recursive delete, a
  migration or overwrite with no way back, run without the check that makes it safe.

The ways this repo's code fails, each pinned by a test the diff should still pass for the right
reason:

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

- **Confirm before writing.** Any new path that writes something real drafts it, shows it, and
  waits for a yes. Approval is per-invocation, never standing. A write path that doesn't gate is
  blocking.
- **No secrets in the repo.** A key, token or password committed in any form is blocking.

## Pass 3 — Cost and simplification

- **Reuse over reimplementation.** An existing function or tool before a new one.
- **Nothing speculative.** Configuration nobody sets, a layer with one caller, a flag for a case
  that doesn't exist yet.
- **A shim with no removal version.** Code kept for compatibility (an old key still read, an old
  name still accepted) that doesn't name the version that removes it, or a compatibility test that
  outlives its shim.
- **Altitude:** does the new code sit at the same level of abstraction as its neighbours?

## Reporting rules

- Findings are ranked **Important** or **Nit**. Important = wrong behaviour, a broken contract, or a
  requirement with no code or no test. Everything else is a Nit.
- **Cap nits at 5.** If there are more, the change is too big — that's the finding.
- Tag each finding with its pass: `[correctness]`, `[contract]`, `[cost]`.
- **Out of scope, never reported:** generated files, and formatting a formatter already fixes.
