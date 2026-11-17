# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

Skill evals: ran, 2 of 2

## F1. [nit] [cost] `GATE_RE` is defined and never read

The constant for a gate file's first line, `GATE: PASS|FAIL`, is added with the others, but
`read_gate_file()` reads only each attempt's `Verdict:` line, and nothing else matches the first
line. Dead code the diff itself adds, which a reader takes for a parse that happens.

Evidence: plugins/factory/scripts/factory.py:126
Class: a constant left over from a plan the build changed (the first line is written, never read); no other unused one in the diff
Disposition: fixed
Fix: in plugins/factory/scripts/factory.py, delete the line `GATE_RE = re.compile(r"^GATE: (PASS|FAIL)\s*$")`.

## F2. [nit] [context] REFERENCE says `gate_fail` counts only the gate on each build

`_factory_files()` counts every `Verdict: FAIL` in any `build/*.gate.md`, so a red gate on a change
a landing rebased (`build/land-<n>.gate.md`) is counted too, while `docs/REFERENCE.md` says the
gate runs "on each build before its review". The count is right; the doc says less than it counts.

Evidence: scripts/sdlc.py:3434, docs/REFERENCE.md:800
Class: a doc written before the landing's gate was added in the same change
Disposition: fixed
Fix: in docs/REFERENCE.md, replace "on each build before its review, absent" with "on each build before its review and on a change a landing rebased, absent".

## F3. [nit] [contract] A clear landing runs the host's gate with no question naming it

With `land-check` clear, `/sdlc-factory:land` passes its gate itself and now runs `factory.py
gate --land`, a host command, under the skill's rule with no question at all; the build's WAIT
names its gate command, the landing's has none to name it in.

Evidence: plugins/factory/skills/land/SKILL.md:14, plugins/factory/skills/land/SKILL.md:103
Class: a command run unasked through an `allowed-tools` rule
Disposition: minor
Reason: nothing new runs unasked: before this change the landing's behaviour check ran the same base-branch check after a rebase, unasked, in `factory.mode`; the script now runs it instead, and the skill's Step 3 names it.
