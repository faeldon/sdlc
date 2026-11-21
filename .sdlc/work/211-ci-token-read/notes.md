# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

- [x] pre-existing: .github/workflows/check.yml:23: `actions/checkout@v4` and `astral-sh/setup-uv@v6` are pinned by moveable tag, not by commit SHA. Pin each to a full SHA with the version in a comment, and let Dependabot or Renovate bump them. → seed: 2026-11-21-22
