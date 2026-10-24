# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `work/ideas.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Where the build departs from the plan

- `acceptance()` reports one problem the spec didn't list: a fenced block that is never closed.
  Without it, an unclosed `sh` fence would swallow the rest of the file and read as one check.
- The plan's second dogfood check ("ship's `allowed-tools` holds no `accept` rule") is a
  regression test already (`test_no_skill_lets_accept_run_unasked`), so it isn't repeated as an
  acceptance check. `checks.md` checks the factory reviewer's wording instead, which only a revert
  could break.
- This repo's `.sdlc/setup.json` is recorded again (`sdlc.py record`), since Stage 4 and Pass 1 of
  the defaults changed; `sdlc.py drift` here reports nothing.
