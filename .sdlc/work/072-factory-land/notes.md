# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Where the build departs from the spec

- **Three kinds of change are left out of a batch, not asked about** (R3, R5): undone `notes.md`
  items (`carry` writes them; only a person gives each a disposition), a `checks.md` (`accept`
  runs only under a prompt), and, in this repo, skills' cases in scope (ship refuses without the
  `Skill evals:` line, and `run-cases` is paid and asked). `land-check` lists them as `excluded`,
  for `/sdlc:ship` one at a time.
- **In a batch that passed itself, a change whose rebase conflicted stops once its resolution is
  reviewed**: a resolved conflict is a signal (R3), so it lands at the next `/sdlc-factory:land`,
  behind the person's yes, from `stage: shipped` (`ready` now lists a shipped change whose
  worktree is still open).
- **The commit is `factory.py`'s** (`land`), not a `git commit` in the skill's bash: only ship's
  skill may hold that rule. `land --close` amends the landing's own record (`reviews/land-<n>/`,
  `runs/land-resolved`, `build/land-<n>.md`) into the change's commit before `sdlc.py close`, so the
  change lands as one commit and close finds its worktree clean.
- **`.sdlc/last-id` conflicts settle themselves** in `resolve` (the higher number), as `sdlc.py base`
  does on a fast-forward: every batch of locally numbered changes conflicts there, found by the
  end-to-end test.
- **A change mid-rebase is found by its rebase's `head-name`** (`current_branch()`): HEAD is
  detached then, and `git branch --show-current` is empty.
- **The approver proposes the impact** with a `- IMPACT:` line; a missing one is a signal, and
  `land` refuses to ship without one.
- **The trailer is `Sdlc-Landed: by=auto|person`**: `parse_trailers` drops a bare word.

## Not verified yet

- [x] A real landing (paid): two ready factory changes from a real supervised run (seed
  2026-11-17-7), `/sdlc-factory:land` from a fresh session in the main checkout. It is the only
  check of the cache lookup (`<cache>/<marketplace>/sdlc/<version>/`, inferred from the clone-read
  layout the docs describe), of the builder resolving a real conflict and the reviewers checking
  it in headless sessions, and of `close`'s push from a subprocess. → seed: 2026-11-17-10
