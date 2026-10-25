# Inbox

> Where change requests arrive, before anyone decides to act on them. Every entry is a **seed**,
> something a change may grow from, and its tag is its kind: `[idea]` a change someone proposes,
> `[bug]` something already shipped that is broken, `[nit]` a finding `/sdlc:ship` approved
> unfixed. Each is a `## [YYYY-MM-DD-n] [idea] <title>` heading, its id the day it came in and a
> count from `sdlc.py next-entry`, then a few lines on why and where it came from. A `[bug]` has
> `Severity:` (a word from the process doc), `Paths:` and, once confirmed, `Introduced by:
> NNN-slug` lines; a `[nit]` has `Theme:`, `Paths:`, `Cost:`, `Value:` and `Raised by: NNN-slug
> (pass)` lines. A seed that must wait for others carries an `After: <id>, <id>` line. An entry is
> named by its id, written bare, or by its title, quoted. `/sdlc:status` reads the tags and those
> lines to put forward what's next. `/sdlc:intent` promotes a seed into a change, whose type
> (`feature`, `fix`, `refactor`, `docs`, `chore`…, listed in the process doc) its kind suggests,
> and tags an idea `[building]`; that change's commit deletes the entry, and history keeps it. A
> `[seed]` tag, from before ideas had their own, reads as `[idea]`.
