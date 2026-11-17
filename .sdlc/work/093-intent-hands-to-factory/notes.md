# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Built

- `AGENTS.md` gained one sentence in its factory paragraph, beyond the spec's R12 docs: the core
  knows whether the factory is enabled only through `config`'s `factory`. `sdlc.py context`
  names `AGENTS.md` for this diff, so ship would have asked for it.
- The `product` fixture is a copy of `set-up`'s `change/` plus a product doc, rather than an
  `extends`: `scaffold.sh` reads `extends` only for branch fixtures, not `main` ones.
- Nothing left undone.
