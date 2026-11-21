# Build report: 216-autopilot, round 4 (after the decision-1 escalation)

Round 4 builds the three confirmed defaults that existed only as reviewer lines in round 3: D8, D9 and D10. The full gate is green: 3947 passed, 29 skipped. Nothing is committed; `HEAD` is `ef75cb3`, the base branch's tip after `fresh`.

## The escalation's items

- **D1–D7:** these were confirmed as built (D6 was settled by the approver), so I changed nothing for them.
- **D8 (sensitive paths are guarded by default):** done.
  - When `guards` is unset, `_default_guards()` now covers the policy and review docs, `[review] irreversible` and `[review] sensitive`.
  - Like the others, it is read from the base branch through `factory._sensitive()`.
- **D9 (a seed with an `Issue:` line only when named):** done.
  - `sdlc.py`'s `next_up` items, and so `status --json`, now carry `issues` from `entry_issues()`. The value is `None` when the line isn't `#N`.
  - `candidates()` takes a seed that names an issue, or has an unreadable line, only when `--seeds` names it.
  - `open_wave()` passes the numbers to `open_seed()`. It writes them through `opened_intent()` as `closes: [12, 15]`, the same line `/sdlc:intent` writes. So the landing's `issue` signal fires, the risk weight counts, and the issue gets closed.
  - A seed whose line can't be read is held before any agent runs.
- **D10 (what `--by autopilot` protects against):** documented in AGENTS.md, the factory README and the autopilot skill.
  - The marker stops a process from inheriting it by accident. It is not a boundary against a process running as the same user that sets it on purpose.
  - The README says the real limit on a misled builder is its own permissions and sandbox (`mode`).
- **D11 (look):** seen by the person. Nothing to build.

## Tests

All four were run red first, each failing for the expected reason, then green after the change:

- **`test_default_guards_hold_the_sensitive_paths` (D8):** the default guards include the base branch's sensitive paths. The change's own `[review]` adds nothing.
- **`test_a_seed_with_an_issue_is_a_candidate_only_when_named` (D9):** a seed with an issue, or an unreadable `Issue:` line, is a candidate only when named.
- **`test_a_seed_with_an_issue_is_opened_with_closes` (D9):** the loop writes `closes: [12, 15]` and `intent_closes()` reads it back. The unreadable seed is held and its intent is never drafted.
- **`test_candidates_come_from_the_real_status_json` (extended):** the real `status --json` gives `issues` ([] or [7]), and a bug with an issue is a candidate only when named.

## Runs

| Run | Result |
|---|---|
| `tests/test_autopilot.py` | 54 passed |
| The 8 test files that read `next_up` | 656 passed |
| Full gate (`factory.py check 216`) | 3947 passed, 29 skipped, exit 0 |

## Docs, plan.md and notes.md

- **plan.md:** work-order step 6 (round 4) added, and the D8/D9 tests added to the Tests list.
- **notes.md:** a *Round 4* section added. The four unticked `- [ ]` lines from earlier rounds are unchanged, and each already has the seed the approver proposed.
- **One gap in `spec.md`:** its R19 text still gives the default guards as the docs plus `irreversible`. I didn't edit the spec; the person's D8 answer is what changes it, and the reviewers will read the code against that ledger line.

No new decisions this round.

- UNTESTABLE: none

## Evidence

$ cat .sdlc/work/216-autopilot/decision-1.md .sdlc/work/216-autopilot/decisions.md
(D1–D10 ticked `→ decided: the assumed default, confirmed`; D6 settled by the approver; D11 `→ decided: seen`)
exit: 0

$ uv run --group dev pytest -q tests/test_autopilot.py -k "sensitive_paths or issue or real_status"   (before the fix)
E       AssertionError: assert ['2026-11-21-...2026-11-21-3'] == ['2026-11-21-3']
E       AssertionError: assert ['.sdlc/SDLC....', 'db/*.sql'] == ['.sdlc/SDLC....s/closing.py']
E       ValueError: too many values to unpack (expected 1)
E       KeyError: 'issues'
4 failed, 50 deselected in 1.13s
exit: 1

$ uv run --group dev pytest -q tests/test_autopilot.py
54 passed in 18.75s
exit: 0

$ uv run --group dev pytest -q -n auto $(grep -ln "next_up" tests/*.py)
656 passed in 13.87s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 216
All checks passed!
367 files already formatted
3947 passed, 29 skipped in 244.01s (0:04:04)
✔ Validation passed
exit: 0

$ git log --oneline -1
ef75cb3 Add seed 2026-11-21-45: park a change on a host resource, with a deadline
exit: 0
