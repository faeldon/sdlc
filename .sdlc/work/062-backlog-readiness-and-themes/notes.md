# 062 — Readiness groups for the backlog, and taking a theme as one change · notes

## This repo's Next up, after

```
■ Next up: 27
    Ready to build: 2
      nits  [style] 1 open, cost S  (23d)  → /sdlc:intent pay down the [style] nits
      nits  [cost] 1 open, cost S  (12d)  → /sdlc:intent pay down the [cost] nits
    Needs a decision: 25 (16 low)
      idea  [retro] A retro report and process views from each change's numbers  (23d)  → …
      … (eight lines in all)
    (+17 more: status --all)
```

`status --all` prints the take-the-theme command under seven themes, e.g. retro's
`→ /sdlc:intent 2026-10-24-4 2026-11-08-3 2026-11-12-2  (its ideas as one change)`.

## Departures from the spec

- **`ideas_of(rec)`** reads a record's `ideas`, falling back to its one `idea` for a record built
  without the list (an existing test hands `next_up` such a dict). Every R6 reader goes through
  it, so nothing that builds a record by hand loses its seed.
- **Ship deletes each distinct entry once**, however many of the `idea:` values name it (an id and
  its title both listed), last line first.
- **The theme command line** reads `→ /sdlc:intent <ids>  (its ideas as one change)`, so the line
  says what it's for.
