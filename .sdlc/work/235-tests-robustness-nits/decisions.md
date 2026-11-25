# Decisions

- [x] D1 (builder round 1, default): Should a host that `hosts.local` both lists and `!`-excludes go unread? Going ahead with yes: `_read_hosts()` skips it, it gets no row, and `listed` doesn't count it. → decided: the assumed default, confirmed
  - OPTION: skip it — matches 208 R3 ("never read"), and R15's test can pass; `listed` drops by one for such a line
  - OPTION: leave the code and drop R15's read assertion — no code change; an excluded host is still read, against 208 R3
  - WHY: R15 asks for exactly this, and 208 R3 already says an excluded repo is never read
- [x] D2 (approver round 1, look): `scripts/closing.py: fix_trailers(), origin_trailer()` — both now catch `(OSError, ValueError)` instead of `Exception`. The path is in `[review] sensitive`, and a coding error there now stops a close. The spec names this and says a git or read failure still gives `[]`. → decided: seen
