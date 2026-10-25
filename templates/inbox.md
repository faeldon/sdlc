# Inbox

> Where change requests arrive, before anyone decides to act on them. Each one is a
> `## [YYYY-MM-DD-n] [seed] <title>` heading, its id the day it came in and a count from
> `sdlc.py next-entry`, then a few lines on why and where it came from; `[bug]` in place of
> `[seed]` marks something already broken. A seed that must wait for others carries an
> `After: <id>, <id>` line. An entry is named by its id, written bare, or by its title, quoted.
> `/sdlc:status` reads the tags and that line to put forward what's next. `/sdlc:intent` promotes
> an entry into a change and tags it `[building]`; that change's commit deletes the entry, and
> history keeps it.
