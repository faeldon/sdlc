# Review

> What `/sdlc:ship` works through on every change before it commits: three passes over the diff,
> then how findings are reported. This guide is the plugin's, read in place from it
> (`docs.review.guide` in `sdlc.py config`), and names only the mistakes every change can make. A
> repo's review doc (`[docs] review`, `.sdlc/REVIEW.md`) is read with it and adds the ways its own
> code has failed: a block of the repo's with a heading path, or lead, found here stands in for
> this one when it holds text of its own; any other is read after its parent's block here.

**Scope:** the diff, and only the diff. Three passes, in order. Stop at the first pass that produces
a blocking finding — fix it and re-run rather than accumulating a long list.

## Pass 1 — Correctness

Does the change do what `intent.md` (Tier 1) or `spec.md`'s numbered requirements (Tier 2) said?
Walk the requirements one at a time; **a requirement with no corresponding code is a finding.** A
requirement with code but no test that would fail without it is one too, unless only a revert
could fail it and the change's `checks.md` holds the check that proves it (`notes.md` when it
can't run).

Then look for the failures that don't announce themselves:

- **An error swallowed.** A `try` that catches everything, a default returned where a failure was
  meant, a check that passes when the thing it checks is missing.
- **An edge case the requirements name and the code doesn't handle:** empty input, a missing file,
  a second run of something meant to run once.
- **A test that can't fail.** A glob that matches nothing, an assertion on a mock of the thing under
  test, a case skipped by a condition that is always true.
- **A test only a revert can fail.** A test in the suite that checks a file moved, a key renamed or
  a line added: nothing but undoing the change breaks it, so it is an acceptance check, kept in
  the change's `checks.md` (or `notes.md` when it can't run).
- **Behaviour changed where the diff doesn't say so:** a default, an order, a rename that something
  else still reads by its old name.
- **Bad input that crashes.** Input a person or another system can get wrong (a config file, a
  frontmatter line, a request body) raises a traceback where the code promises to report it.
- **Works only here.** A change that passes because of what this machine or checkout has: a local
  file, an environment variable, a tool on `PATH`, a network service the tests happen to reach.
- **A destructive operation where a safe one exists:** a force flag, a recursive delete, a
  migration or overwrite with no way back, run without the check that makes it safe.
- **A symptom fixed in place of its cause.** On a change that fixes a bug (its `fixes:` line), ask
  whether the diff removes what made the bug possible or only the case that was reported: a guard
  around one caller, while every other caller still reaches the broken code.

### The ways this repo's code fails

None recorded yet. A repo lists here the failure classes its own history shows, each a
`- **lead**` bullet pinned by a test the diff should still pass for the right reason.

## Pass 2 — Contract

Does the change stay inside the invariants the host's policy doc (`[docs] policy`, `CLAUDE.md`, or
`AGENTS.md` when that is the only one) declares? Check each one the diff comes near. If the change
genuinely *needs* one to move, that's an edit to the policy with its own reasoning in `spec.md`,
not a quiet exception.

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

- Findings are ranked **Important**, **Nit** or **Pre-existing**. Important = wrong behaviour, a
  broken contract, or a requirement with no code or no test. Pre-existing = a fault in lines the
  diff neither adds nor changes, and doesn't newly reach: it isn't this change's, so it never
  blocks it, and it is filed as a bug of its own. A new call into old broken code is the diff's
  finding, ranked Important or Nit. Everything else is a Nit.
- **Evidence, not a guess.** Every finding cites the `path:line` it rests on, read, never inferred
  from a name. A finding with nothing to cite isn't one.
- **Name the class.** Say what kind of mistake it is and whether the same mistake appears
  elsewhere, so the fix covers every instance, not the one line shown.
- **Cap nits at 5.** If there are more, the change is too big — that's the finding.
- Tag each finding with its pass: `[correctness]`, `[contract]`, `[cost]`.
- **Count first.** The findings open with their count by rank, and say "nothing to fix" plainly
  when there are none.
- **A second reviewer's findings count like any.** On a diff that touches a sensitive path, a
  reviewer that never saw the session that built it reviews the diff too. Each of its findings is
  answered like the review's own, and one that can't be confirmed from its evidence is dismissed
  with why, never dropped unseen.
- **Out of scope, never reported:** generated files, and formatting a formatter already fixes.

### Paths this repo's review skips

None beyond the out-of-scope above. A repo lists here the paths its review never reads (vendored
code, fixtures, snapshots), each with why.
