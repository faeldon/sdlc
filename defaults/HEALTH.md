# Health

> What each finding this repo's scans (`commands.scan`) can report means, and the response tier
> it usually gets: 1 report it, 2 fix it inline, 3 write an intent. `/sdlc:health` reads
> this once per run, routing every finding by the table ahead of its own rules, and the blind
> spots say what a clean scan can't vouch for.

## Findings

<One row per finding a scan can report, named as the scan prints it, in a table: | finding |
what it means here | default response tier (1, 2 or 3) | why |. A finding left out is routed by
the health check's own defaults and its own text.>

## Blind spots

<What the scans can't see, or what they need to reach before a clean result means anything: a
service they call, data they read, a folder they skip. A scan reporting clean having looked at
nothing is the worst finding there is.>
