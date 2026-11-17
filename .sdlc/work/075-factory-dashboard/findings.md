# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

Skill evals: skipped, the diff touches no skill a case covers (`cases`' scope is empty).

## F1. [nit] [correctness] shots waits for the dev server on 127.0.0.1 whatever `[ui] url` names

`shots()` probes readiness with `_answers(port)`, a connect to `127.0.0.1` alone, while the shots
go to `[ui] url`. A dev server that binds `localhost` to `::1` only (Vite on recent Node does)
never answers the probe, so the review is refused with "didn't answer" after `timeout`, though the
page was up at the url the host declared. Loud, never silent, and the default url is 127.0.0.1.

Evidence: plugins/factory/scripts/factory.py:2305 (`_answers`), :2387 (the wait loop)
Class: a readiness check that tests a different address than the one used; nowhere else here
Disposition: fixed
Fix: `_answers(host, port)` connects to `urlparse(_fill(ui["url"], port=port)).hostname or "127.0.0.1"`, which `create_connection` resolves to every address (IPv4 and IPv6), and the wait loop passes that host; the test's `_answers(record["port"])` calls pass `"127.0.0.1"`.

## F2. [nit] [cost] `_sh()`'s docstring wraps mid-sentence after the merge

The rebase's merge of the docstring left "as `sdlc.py` runs a" alone on its line, the sentence
running on below: harmless (the pin compares the code, not the docstring), but it reads as a slip.

Evidence: plugins/factory/scripts/factory.py:182-185
Class: a merge's reflow left undone; only here
Disposition: fixed
Fix: reflow the docstring to "The argv that runs the host's gate, and `[ui]`'s server and screenshots, through `sh -c` on every platform, as `sdlc.py` runs a host's commands: `/bin/sh`, and on Windows the `sh` on PATH, Git for Windows', never `cmd.exe`. Raises OSError when Windows has none. Copied from `sdlc.py`, pinned by a test." at 100 columns.
