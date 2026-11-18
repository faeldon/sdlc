# Findings

> What a change's review found, one `## ` section a finding, committed with the change.
> `/sdlc:ship` writes it after every review, and the factory's `carry`, and its landing's rounds,
> write their agents' findings into it; `By:` names who raised one: `fresh` for ship's
> fresh-context reviewer, a factory role (`code`, `test`, …) for an agent, and no line on ship's
> own. A rerun keeps each id, marks one the diff no longer shows `fixed`, and never raises again
> one the person answered `wrong`, `intentional` or `minor`; an agent's `wrong` is its verifier's,
> never the person's, and the same fault worded differently is one more. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:`, `By:` and `Fix:` lines, counts
> ship's own alone into the `Sdlc-Findings` trailer (its `agents=` says how many it left out),
> words ship's question from the ones proposed `fix`, and `ship` refuses while one is still `open`
> or `fix`. On a diff that touches a sensitive path, this note also says `Fresh review: ran`, or
> `Fresh review: skipped, <why>`.

## F1. [nit] [correctness] The temp directory is replaced as a substring, so `/tmp` also rewrites `/var/tmp/…` and `/tmpfoo`

On Linux with no `TMPDIR`, `tempfile.gettempdir()` is `/tmp`, and `str.replace` writes
`/var/tmp/x` as `/var<tmp>/x` and `/tmpfoo` as `<tmp>foo` in a record. Nothing leaks, but a
quoted path is garbled. The home mark does the same in principle (`/home/ana` inside
`/home/anabel`), but a home path that short is rare.

Evidence: plugins/factory/scripts/factory.py:2717 and scripts/sdlc.py:2898, `text.replace(form, mark)` with no boundary on either side
Class: a path matched as a substring rather than as a whole path; the same in both pinned copies
Disposition: fixed
