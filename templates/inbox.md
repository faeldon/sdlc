# Inbox

> Where change requests arrive, before anyone decides to act on them. Each one is a
> `## [YYYY-MM-DD-n] [seed] <title>` heading, its id the day it came in and a count from
> `sdlc.py next-entry`, then a few lines on why and where it came from. `[bug]` in place of
> `[seed]` marks something already broken, with `Severity:` (a word from the process doc),
> `Paths:` and, once confirmed, `Introduced by: NNN-slug` lines; `[nit]` a finding `/sdlc:ship`
> approved unfixed, with `Theme:`, `Paths:`, `Cost:`, `Value:` and `Raised by: NNN-slug (pass)`
> lines. A seed that must wait for others carries an `After: <id>, <id>` line. An entry is named
> by its id, written bare, or by its title, quoted. `/sdlc:status` reads the tags and those lines
> to put forward what's next. `/sdlc:intent` promotes an entry into a change and tags a seed
> `[building]`; that change's commit deletes the entry, and history keeps it.
