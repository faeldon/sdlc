# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

## F1. [important] [correctness] `_binds()` reads a port a wildcard listener holds as free

`_binds()` probes only `(host, port)` with `SO_REUSEADDR`. On macOS a port another server holds
on `0.0.0.0` (as `python -m http.server` and `vite --host` bind) still lets that probe bind, so
`_lost()` judges a server that lost its port to a parallel run as having failed on its own, and
the UI review isn't retried: the very race this change's retry exists for. The landing's code
review raised it and its verifier kept it (`reviews/land-1/verified.md`).

Evidence: plugins/factory/scripts/factory.py:4225 (`_binds()`), read with `_lost()` at :4240
Class: a probe that answers for one address while the server may hold another; only `_binds()` probes
Disposition: fixed
Fix: in `_binds()`, probe `(host, port)` and, when `host` isn't already the wildcard, `("0.0.0.0", port)` too, both with `SO_REUSEADDR` off Windows, and return True only when both bind; add a POSIX test (skipped on Windows) that holds the port with a listener on `("0.0.0.0", 0)` and asserts `_binds("127.0.0.1", port)` is False and `_lost("127.0.0.1", port)` is True.
