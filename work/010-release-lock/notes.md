# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `work/ideas.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

- The plan missed `tests/test_config_resolution.py`: `test_the_release_section_resolves_with_its_defaults`
  pins every default in `[release]`, so it gained `"after_bump": None`. The first `./check.sh`
  failed on it, and nothing else.
- `AFTER_BUMP_TIMEOUT` sits beside `SEMVER_RE`, with release's other constants, rather than beside
  `EVIDENCE_TIMEOUT` as the plan said: `cmd_release` is defined well above retro's constants.
- 008's drift gate caught the new config key (`release.after_bump (new): record`) before `record`
  ran, as 009's message now says. The process-doc edit matched the copy, so only the key showed.
- [x] Not run by hand: a release with `after_bump = "uv lock"` on a real uv project, and the spec's
  `release --check` from a scratch clone. This session can only run git in its own worktree. The
  R1–R4 and R6 tests run a real shell command (`echo`, `touch`) through the same step.
  → dropped: this repo's next `/sdlc:release` runs it for real, behind its own approval.
