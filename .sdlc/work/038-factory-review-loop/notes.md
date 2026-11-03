# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Where the build differs from the spec and plan

- **`[light]` is documented in `plugins/factory/README.md`, not `docs/REFERENCE.md`** (R14):
  REFERENCE has never described `factory.toml`; the factory's README is its home. REFERENCE got
  `Sdlc-Review`'s `dropped`.
- **`read_rounds()` reads every reviewer's file present**, not only the depth's, and
  `_rounds_at_depth()` marks each round `complete` against the depth's reviewers, so the depth
  can see that a round ran beyond `[light]` (a run never lightens) without reading twice.
- **A run is also `full` once any round number passes `[light]`'s `rounds`**, beside a reviewer
  outside `[light]`'s list: a host whose two depths share reviewers still never lightens.
- **`_factory_files()` writes `dropped` for every reviewer, 0 included, only when the run has a
  `verified.md`**, so a trailer from before the verifier reads as unknown, never as nothing
  dropped.
- **The verifier's `DROPPED` reason follows the last ` — `**, split by `rpartition`, so a change
  whose own text holds an em dash still matches; `sdlc.py`'s regex copy only counts lines.
- **`untouched` is empty when there's no base branch:** nothing is known to be touched, so nothing
  is called pre-existing.
- **A low-risk run's question can't be exact:** the build approval comes before any diff, so it
  states both depths and `max_runs` at the full depth, as agreed in the spec.
