# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.
>
> Fresh review: ran
> Skill evals: ran, 2 of 2 (cases-2026-11-17-9; the first run, cases-2026-11-17-8, failed
> `intent`'s judgment grader on a reply split before its text question, and passed on the rerun)

## F1. [important] [correctness] `groups` reads a shipped or dropped change's slug as `created`

`open_by_slug` is built from `_used()`, every change folder on disk whatever its stage, so a group
whose slug a shipped (awaiting close) or dropped folder holds is skipped as made by an earlier run,
and a group `after` it gets that dead change's number as `depends_on`. `new` refuses that slug, so
`groups` must refuse it too.

Evidence: scripts/sdlc.py:2485 (`open_by_slug` from `_used(home)`), :2501; `_open_claims()` at
:6826-6829 skips `shipped` and `dropped`, the lookup beside it doesn't
Class: "open change" read as "any change folder"; the lookup beside it filters, this one didn't
Disposition: fixed
Fix: build the slug map from `change_dirs()` with `load_change()`: an open stage is `created`, a shipped or dropped one a refusal (`<slug>: taken by <NNN-slug> (<stage>)`); a test with a shipped folder of the group's own slug
By: fresh

## F2. [nit] [correctness] A malformed `Issue:` line reads as no issues

`entry_issues()` returns None for a value that isn't `#N`, and `cmd_groups` turns it into `[]`, so
the batch drafts that change with no `closes:` line and never says why; `check` reports the same
None as a problem.

Evidence: scripts/sdlc.py:2519 (`"issues": entry_issues(entry) or []`)
Class: an error swallowed into a default; the same `or []` at :7050 predates this diff
Disposition: fixed
Fix: refuse it, `<slug>: <id>'s Issue: line isn't #N, …`, with a test
By: fresh

## F3. [nit] [correctness] A rerun skips a change whose intent was never written

A run stopped between `new` and writing the intent (the session ends, say) leaves a scaffold; the
rerun reads the slug as `created` and skips it, so that change is never drafted and its seeds are
never tagged, though `batch.md` says what was made is complete.

Evidence: scripts/sdlc.py:2501; skills/intent/batch.md:57-69
Class: a second run of something meant to run once; only here
Disposition: fixed
Fix: `groups` reports `drafted`, false while the created change's `intent.md` is unfilled (`is_unfilled()`); batch.md's Steps 3 and 5 draft and write such a change, skipping only its `new`; a test
By: fresh

## F4. [nit] [correctness] The spec's Verification names the wrong test file

It names `pytest tests/test_sdlc.py -q -k groups`; the tests are `tests/test_groups.py`.

Evidence: .sdlc/work/096-factory-intents/spec.md, Verification
Class: an artifact naming a path the plan changed
Disposition: fixed
Fix: `uv run --group dev pytest tests/test_groups.py -q`
By: fresh
