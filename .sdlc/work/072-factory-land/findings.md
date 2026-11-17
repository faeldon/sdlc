# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

## F1. [important] [context] The READMEs still say ship and close are always the person's

071 landed under this change and its factory README says the factory "runs on" manual mode with
"ship and close stay the person's", that it sits "between a person's intent and a person's ship",
and, under "The gates", that `/sdlc:ship` reviews every factory change behind its WAIT and
`/sdlc:close` lands it. The root README's factory bullet says "you ship them, in your order". With
`/sdlc-factory:land`, a clear batch is shipped and closed by sdlc's own code behind a gate that
passed itself, and the factory's rounds stand in for ship's review: every one of those lines is
now false for a landed change, in the first doc a host reads about the factory.

Evidence: plugins/factory/README.md:7, plugins/factory/README.md:17, plugins/factory/README.md:29, README.md:168
Class: a context doc's claim made false by a change landing under this one; the deterministic-spine section 071 added is where the rest of the factory's guarantees are stated
Disposition: fixed
Fix: in plugins/factory/README.md, line 7's "and ship and close stay the person's" becomes "and ship and close stay `sdlc`'s own code, run by the person or, for a batch, by `/sdlc-factory:land`"; line 17's "between a person's intent and a person's ship" becomes "between a person's intent and the change's landing"; "The gates" bullet gains "Or `/sdlc-factory:land` runs ship's and close's own code for a batch of ready changes, behind one gate that passes itself only when no change in it carries a risk signal, the factory's rounds standing in for ship's review."; and README.md:168's "you ship them, in your order" becomes "you land them, one at a time with `/sdlc:ship` or as a batch with `/sdlc-factory:land`".

## F2. [important] [contract] The auto-pass and the exclusions are enforced only by the skill's prose

`factory.py land <NNN> --by auto` ships, commits and lands a change without checking that it has
no risk signal: only the land skill's Step 1 reads `land-check`'s `clear` and skips the WAIT. And
`land --by person` ships a change with a `checks.md` (or skills' cases in scope) without anyone
running `accept`, which `land-check` excludes but `land` doesn't refuse. A skill that skipped its
WAIT, or a session that typed `--by auto`, would land a sensitive or escalated change unasked and
record it as `Sdlc-Landed: by=auto`. The repo's rule is that whether a branch applies is the
script's call, never the skill's.

Evidence: plugins/factory/scripts/factory.py:1505
Class: a gate's rule carried by a skill's prose where the script it calls could check it; `land-check` and `land` read the same signals and must agree
Disposition: fixed
Fix: in `cmd_land`, before shipping, run `land_signals()` for the change: refuse when `excluded` is non-empty ("ship it by hand: …"), and refuse `--by auto` when `signals` is non-empty ("the gate is the person's: …"); with a test that `--by auto` on a change with an ESCALATE decision, and `--by person` on one with a `checks.md`, are refused before anything is written.
