DECISION: ESCALATE

**Why.** The build is done and tested. All four reviewers passed round 1 with only nits, the gate is green (`./check.sh`, 3447 passed), and nothing open is Critical or High. The one thing holding it is the open default D1. It widens the intent's Approach ("Dedupe identical decisions") so that a reworded question with the same options and why also counts as already filed. The security review notes what follows: a reworded `[blocking]` question can then count as already answered by the person's earlier reply. That rule decides which questions reach the person, so it's yours to confirm, not mine to settle.

**Open items**
- None. The reviewers recorded only nits (F1 code, F3 security, F4 test), and none was asked to be changed.

**Decisions to confirm**
- No blocking decision is unticked.
- ESCALATED: D1: it decides when a person's answer to one question also covers a differently worded one (a blocking question included), and it goes beyond the intent's "identical" dedupe. Which questions the person gets asked is a policy call, and only they can make it.

**Every other reason you escalate for**
- None.

**For the person at ship**
- Look first at `plugins/factory/scripts/factory.py: cmd_decisions()`, the `by_alts` match near line 2018. This is D1's rule, which counts a raise as already filed by its source, kind, options and why. Then look at `question_lines()`, which folds a question's continuation lines into one ledger line.
- `plugins/factory/scripts/landing.py: read_only_command()` (a sensitive path). It now refuses any prefix of `--dereference-recursive` of three or more characters; the check is written `len(name) >= 5` because it counts the leading `--` (F3). It only gets stricter.
- The `decisions.md` ledger format is read by `/sdlc-factory:decide`, `/sdlc:ship` and the board. You approved this in the intent's *Affected* section and its Approach. Old ledgers still read: they're matched by their first line alone, and a rerun writes nothing.

- IMPACT: patch — `/sdlc-factory:decide` now gets a decision's whole question and its options, a decision raised twice is filed once, and the unattended landing's read-only list is stricter. Nothing anyone uses has to change.

**Each undone item's disposition**
- UNDONE: pre-existing: plugins/factory/scripts/landing.py:795: the grep refusals cover GNU grep and BSD grep only. If a host's `grep` on `PATH` is ugrep, `grep -r --dereference-files keep .` is allowed and follows links to files outside the checkout. This change didn't add or touch that gap, but it is in the same function. Fix: refuse `--dereference-files` and its prefixes too, or check every word against a list of such long options. → seed: Read-only list refuses ugrep's symlink-following long options (`--dereference-files` and its prefixes)

  I've carried this as a seed, not a bug. It's a gap in the allow-list's security, and none of the process guide's severity words (`high`, `med`, `low`) clearly fits it.
