# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:` and `Reason:` lines, and `By: fresh` on a
> finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings` trailer, and
> `ship` refuses while one is still `open`.

## F1. [nit] [correctness] An interrupt typed after a gate is counted as after_gate

`close_span()` gives every stop after the pick `after_gate`, so an interrupted turn once the WAIT
is answered loses its `interrupt` kind.

Evidence: scripts/metrics.py:636
Class: precedence between two shape rules; nowhere else
Disposition: minor
Reason: after the WAIT the person is moving on either way, and retro reads `after_gate` as that.

## F2. [nit] [cost] A stray blank line before read_events' entry loop

The `asked` initialiser is followed by an empty line the loop's other state lines don't have.

Evidence: scripts/metrics.py:451
Class: layout; formatter-clean, so nothing catches it
Disposition: minor
Reason: cosmetic, and not worth an inbox entry.

## F3. [pre-existing] [correctness] Membership reads skill names quoted in harness entries

`_membership()` looks for `<command-name>/sdlc:…` in every user entry: a compaction summary that
quotes `/sdlc:intent` can move where a change's main-branch run starts, and one that quotes a
skill inside close's run, or a task notice typed after its approval, ends the run early. This
change keeps those entries out of `read_events`, but membership runs before it and still reads
them as typed.

Evidence: scripts/metrics.py:258, scripts/metrics.py:286
Class: harness entries read as the person's, the class this change fixes in `read_events`
Disposition: recorded
