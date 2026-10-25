# Inbox

> Where change requests arrive, before anyone decides to act on them. Each one is a
> `## [YYYY-MM-DD] [seed] <title>` heading, then a few lines on why and where it came from;
> `[bug]` in place of `[seed]` marks something already broken. A seed that must wait for others
> carries an `After: "<title>", "<title>"` line. `/sdlc:status` reads the tags and that line to
> put forward what's next. `/sdlc:intent` promotes an entry into a change and tags it `[building]`;
> that change's commit deletes the entry, and history keeps it.
