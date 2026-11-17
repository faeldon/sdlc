# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

- [x] Docstrings still name the change folder by its pre-1.4.0 name, `work/`: `sdlc.py`'s module
  docstring, `change_dirs()`, `next_id()`, `claim()` and `cmd_uninstall()` (`_seed_title()` and
  `stamp_shipped()` may mean history's). AGENTS.md now points at these docstrings, so they should
  say `.sdlc/work/`. Left alone here: the docstrings aren't this change's. → seed: 2026-11-17-27
- [x] `sdlc.py`'s module docstring lists about half the subcommands (no `base`, `resolve`,
  `preflight`, `findings`, `checks`, `accept`, `board`, `record`, `drift`, …). AGENTS.md doesn't
  point at it for the list (`sdlc.py --help` has them all); either complete it or cut it to the
  module's purpose. → seed: 2026-11-17-27
- [x] CONTRIBUTING.md's *Writing a tracker* lists the interface without the intake methods core
  calls when a tracker has them (`mark()`, `unmark()`, `needs_info()`, `open_marks()`,
  `open_numbers()`, `closed_by()`); AGENTS.md points there for the interface. → seed: 2026-11-17-28
