VERDICT: PASS

The landing path does what the intent asks. Both landing prompts now name `git diff <merge-base>...HEAD`, not the base branch's tip, and the two new tests that pin this pass on HEAD a383e45. I found no CHANGE.

## Notes

- **End-to-end path:** the change has no `spec.md` (Tier 1), so the intent's Approach is the spec. The path is `factory.py`'s `_land_task()` building the `land-review` and `land-verify` prompts during a landing. I ran the two tests that exercise it, which is the closest path the change's own tests cover. The first checks that the prompts name the round's base and never the moved tip, that the diff holds the change's file and not the later commit's, and that `land-close` still reports `moved`. The second checks that with no merge base both tasks refuse with `_NO_FORK`.
- **Settled points not re-raised:** `decisions.md` marks D1 and D2 as confirmed. D1 is deriving the round's base with `git merge-base` at prompt time, not recording it, and D2 is the same choice seen from the code side. `decision.md` still reads ESCALATE, but it was written before those were ticked, so I took the ticks as the answer.
- **Round 2 rework:** the one kept finding, the silent `or base` fallback, is gone. `_land_diff()` returns None on no merge base and both callers return `_NO_FORK`. The two new tests cover that path.
- **`_amend_record()` keeps `HEAD`'s parent:** it runs `git commit --amend --no-edit` with no rebase. So the merge base stays the rebase point after a later move of the base, which is what `_land_diff()`'s docstring relies on.
- **The four agent paragraphs** are byte-identical; their hashes match.
- **Stale comment (nit, not a behaviour failure):** `plugins/factory/scripts/factory.py:2137` still says the landing review is "the review of the change as it now stands on the base branch". It is now false. The earlier review noted it at line 2000, but it has moved. Filed for later, not reworked here.
- **Register entry (for the person to look at):** the diff removes bug `2026-11-17-86` from `.sdlc/work/inbox.md` on this branch. `AGENTS.md` says the register is committed only by `inbox-commit`, on the base branch, so an entry never rides on a change's branch. The change's `fixes:` line suggests this is the usual close-time removal for a fixed bug. I didn't confirm that from the code, so please check it before ship.
- **Checks:** there is no `checks.md` in the change folder, so there are no acceptance checks to read.
- **Gate:** `build/land-1.gate.md` is green on this build (`Build: a383e45db29fc9fc`, exit 0, 2303 passed). I did not rerun it.

## Evidence

$ git log --oneline -5; git merge-base HEAD main; git rev-parse main; git status --short
  a383e45 A landing review reads its change from the round's own base / ffca1a2 Close 122-retro-one-diff / ... / ffca1a2667cf5e2df9918f25309819fe246d1a69 / ffca1a2667cf5e2df9918f25309819fe246d1a69 / ?? build/land-1.gate.md ?? runs/reviewer-behaviour.sessions
  exit: 0

$ git diff main...HEAD --stat
  26 files changed, 521 insertions(+), 20 deletions(-)  (code: plugins/factory/agents/*.md, plugins/factory/scripts/factory.py, tests/test_land.py; rest is the change folder)
  exit: 0

$ git diff main...HEAD -- plugins/ tests/
  factory.py: `_land_task()` uses `_land_diff()` in both prompts; new `_NO_FORK`, `_land_diff()` = `git merge-base <base> HEAD`, None on no fork; four agent files get the same paragraph; tests/test_land.py gains two tests
  exit: 0

$ cat .sdlc/work/121-landing-review-base/plan.md .sdlc/work/121-landing-review-base/decisions.md .sdlc/work/121-landing-review-base/decision.md
  "- [x] D1 ... decided: confirmed" / "- [x] D2 ... decided: confirmed" / "DECISION: ESCALATE ... Round 2 is VERDICT: PASS and the gate passes (2250 passed)."
  exit: 0

$ cat .sdlc/work/121-landing-review-base/build/land-1.gate.md
  GATE: PASS / Build: a383e45db29fc9fc / Exit: 0 / 2303 passed, 13 skipped
  exit: 0

$ cat .sdlc/work/121-landing-review-base/build/round-2.gate.md
  GATE: PASS / Build: 9c5f7657e33b2b3f / Exit: 0 / 2250 passed, 13 skipped
  exit: 0

$ git diff main...HEAD -- .sdlc/work/inbox.md
  -## [2026-11-17-86] [bug] A landing review reads the base branch's newer commits as the change's deletions  (entry removed on this branch)
  exit: 0

$ cat .sdlc/work/121-landing-review-base/reviews/round-2/code.md .sdlc/work/121-landing-review-base/reviews/round-1/verified.md
  VERDICT: PASS (round 2) / KEPT: code: C1 ... `_land_diff()` falls back to `base` (the moved tip) when `merge-base` fails
  exit: 0

$ Read .sdlc/work/121-landing-review-base/intent.md
  1 --- id: 121 ... stage: shipped ... ## Approach: "pass `git diff <that base>...HEAD` ... in place of the diff against the base branch's tip"
  exit: 0

$ Read .sdlc/work/121-landing-review-base/spec.md
  File does not exist (Tier 1 change: no spec)
  exit: 1

$ ls -d .venv; grep -n "def _amend_record" -A25 plugins/factory/scripts/factory.py; grep -n "_land_diff\|_NO_FORK" plugins/factory/scripts/factory.py; git log --oneline -4 main -- .sdlc/work/inbox.md
  .venv / 3843:def _amend_record(...) "keeps HEAD's parent" / 2648, 2649, 2665, 2666, 2674, 2677, 2682 / e1f5ab9, 6483632, 7847b6a, a9fd56d
  exit: 0

$ PYTHONDONTWRITEBYTECODE=1 uv run --group dev pytest tests/test_land.py -q -p no:cacheprovider -k "landing_review_reads_the_change_from_its_rounds_own_base or landing_review_with_no_fork_point_is_refused"
  (first attempt) zsh: command not found: timeout
  exit: 127

$ set -o pipefail; PYTHONDONTWRITEBYTECODE=1 uv run --group dev pytest tests/test_land.py -q -p no:cacheprovider -k "landing_review_reads_the_change_from_its_rounds_own_base or landing_review_with_no_fork_point_is_refused"
  2 passed, 49 deselected in 2.37s
  exit: 0

$ grep -n "now stands" plugins/factory/scripts/factory.py plugins/factory/agents/*.md
  plugins/factory/scripts/factory.py:2137:# for, the review of the change as it now stands on the base branch, and the mend of a landing
  exit: 0

$ for f in reviewer-code reviewer-security reviewer-test verifier; do sed -n '/^A landing round/,/^that landed/p' plugins/factory/agents/$f.md | md5sum; done
  45544e72ac9453534d6aa1a70d8cb632 (x4, identical)
  exit: 0
