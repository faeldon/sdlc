# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Where the build differs from the spec

- **R9's paragraph is `How to recover:`,** agreed after the spec: for each irreversible path, the
  command that reverses it or "fix forward: …", since a revert can't reach what a host already
  copied. The question's clause reads `with how to recover it shown`.
- **`[review]` is read from the base branch's checkout,** like `git.base`, never the change's own.
  So a change can't lighten its own review by editing the lists, and this change, which adds them,
  ships without a deep review: `main` has no `[review]` yet. The next change touching a listed path
  is the first deep one.
- **`test_sdlc_loads_nothing_from_plugins` is narrowed.** It asserted the repo root has no
  `agents/`; its point is that `sdlc`'s default scans never reach `plugins/factory/`, which a root
  `agents/` holding only `reviewer.md` keeps true, and the test now says that.
- **The reviewer agent has no `model:`,** unlike the factory's: it inherits the session's, so a
  deep review is never weaker than the session that would otherwise do it.
- **Retro counts `fresh_counted`,** the changes whose trailers carry the fresh reviewer's numbers,
  beside `answered`, for the same reason: an old trailer is unknown, never a reviewer that found
  nothing.
