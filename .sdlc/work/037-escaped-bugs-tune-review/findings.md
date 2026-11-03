# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:` and `Reason:` lines, and `By: fresh` on a
> finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings` trailer, and
> `ship` refuses while one is still `open`.
>
> Fresh review: not run: this diff touches no `[review] sensitive` path.

## F1. [nit] [correctness] R8's test greps retro-commit's source for "review"

`test_retro_proposes_review_changes_as_seeds_and_never_writes_them` asserts the words `review` and
`config.toml` are absent from `cmd_retro_commit`'s source, so only a rename fails it, and a
harmless comment naming the review would. Commit a retro whose tree also changes `.sdlc/REVIEW.md`
and assert the refusal instead.

Evidence: tests/test_skills.py:355
Class: a test that greps source instead of running the behaviour; the same as 2026-10-25-22
Disposition: recorded

## F2. [nit] [correctness] A findings.md that no longer parses reads as fewer findings

`_review_at` keeps `_findings_from_text`'s entries and drops its problems, so a section a later
format change makes unparseable vanishes from `review.findings` and `important` while `state`
still says `file`. Carry the problems as `review.problems` for the skill to say.

Evidence: scripts/sdlc.py:5495
Class: an error swallowed where a reader would take the gap for a clean answer; none other in the diff
Disposition: recorded
