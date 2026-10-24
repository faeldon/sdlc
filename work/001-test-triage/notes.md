# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `work/ideas.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Acceptance check

Only a revert could fail this one, so it ran once here rather than going into `tests/`, as the new
Stage 4 rule says:

```
$ grep -c "Ask of each test how it could ever fail" defaults/SDLC.md .sdlc/SDLC.md
defaults/SDLC.md:1
.sdlc/SDLC.md:1
$ grep -c "A test only a revert can fail\|A shim with no removal version" defaults/REVIEW.md .sdlc/REVIEW.md
.sdlc/REVIEW.md:2
defaults/REVIEW.md:2
```

The gate (`./check.sh`) passed, 652 tests, with `tests/test_defaults.py` holding the copies to the
defaults' headings and review bullets.
