# Notes

- [x] `/sdlc:idea --themes` leaves out entries tagged `[building]` but not those an open change's
  `idea:` names, so it may propose a `Theme:` for a seed being built. Harmless (an update, which
  `inbox-commit` allows), but it could read `status`'s `building` list to match. → seed: 2026-11-17-66
- [x] `status` prints `■ Next up` only when there is a candidate, a theme, a done milestone or a
  warning, so with every seed being built the new `N being built` line isn't shown. Left as is:
  each such seed is an open change listed at the top of `status` already. → dropped: each such seed is an open change listed at the top of status already
