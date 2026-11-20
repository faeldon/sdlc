# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## The key scan

`_code_reads()` follows any mention of a function's name, not only a call on a path taken, so it
over-counts: about 30 of the 46 keys are read by most commands, through `load_config()` and
widely shared helpers (`status`'s release-due check reaches every `release.*` key it reads). That
errs towards `used`, the safe side for a retire list, and it is what the intent asks ("every key
`load_config()` or a command reads"). A key is now `unused` only when its readers a record could
show didn't run, so the retire list shrinks to keys nothing reads or that only an unrun skill or
command reads.

The factory's scripts aren't scanned: `factory.py` reads its own settings (`gate_jobs`) and no
key of `CONFIG_KEYS` by name, and scanning it would widen what core reads of the factory beyond
`COMMAND_RE`'s command names.

- [x] The scan's reach could follow only calls, not every mention of a name, if the surface's key → seed: 2026-11-20-56
  share should separate keys a command reads on every run from keys it reads on one branch.
