# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

- [x] code: plugins/factory/scripts/factory.py:4246: when the server answers and then `proc.poll()` shows it has exited, `_up()` returns `True` (lost) without probing the port. That breaks the rule this round asked for: only a port that won't bind is lost. A server that answers and then dies on its own, while the port is free, gets three starts and a false "lost" record, the same bug the kept finding named. The fix: in that branch, return `(why, not _binds(host, port))`, so a port that binds reads as the server failing on its own. Add a test that drives `_up()` directly with a stub process whose `poll()` returns 1 after a listener on the port is closed, and asserts `lost` is False.
  Done in round 3 (decision-1.md): `_up()` now has one exit for a server that ended, and it asks
  `_lost()`, the one place lost is decided; `test_a_port_is_lost_only_when_it_wont_bind_whichever_way_the_server_ended`
  pins the answered-then-exited path both ways.
- The retry can't close the race entirely: a process can take the port between the "already
  answers" check and the serve's own bind, and the bind is probed only after the server exits.
  That is inherent to retrying (D1); "report" (`{port}` = 0) would remove it, at the cost of a
  placeholder each host's serve must honour.
- Round 4: `_binds()` read a port in TIME_WAIT (a connection the server closed first) as held,
  so a server that answered and exited on its own still read as lost. It now sets `SO_REUSEADDR`
  on POSIX; on Windows that option would let a bind take a port another socket holds, and
  TIME_WAIT doesn't block a bind there, so it is left off. No test of this runs on Windows: the
  port tests use real sockets and aren't `portable`.
