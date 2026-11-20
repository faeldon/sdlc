DECISION: READY

**Why.** All four round-1 reviewers (code, test, security, behaviour) returned `VERDICT: PASS`, and the gate passed (`./check.sh` exit 0, 3540 passed, 29 skipped). Every requirement R1–R11 has code and a test, by the reviewers' account: the new tests cover R1–R4, R8 and R9, the unchanged tests cover R5–R7, and the R10 bullet sits under Pass 1 of `.sdlc/REVIEW.md`. Nothing is High or Critical. The two Medium findings both fail closed, which means they stop the train for you rather than let a wrong change through. There is no `notes.md` and no `decisions.md`, so no item is carried over and no decision is waiting.

**Open items**
- None. The only CHANGE-level items are two nits, kept as `recorded` in `findings.md`:
  - F1 (code): `landing.py:2923` reads `_status_entries()` twice.
  - F2 (test): the `[edit]` and `[mv]` cases both stray on `.gitignore`.

**Decisions to confirm**
- None. No decision is unticked and the prompt names no open defaults.

**For the person at ship**
- **Look first at `plugins/factory/scripts/landing.py`, `cmd_resolve()`, the `--continue` branch (around lines 2852–2932).** The order is: the no-rebase refusal, then reading `_replayed()` and `_staged()` once, then `staged_gone` built from `replayed.get(p, "D")`, then `allowed = {*replayed, *files, *moved, *records}`.
- **Security reviewer's Medium [correctness] finding, which no other reviewer took up.** Here is the case:
  - `HEAD` renamed `a`→`b`, and `REBASE_HEAD` edited `a`.
  - merge-ort carries the edit into `b` cleanly, but `b` is not in `allowed`.
  - So if the same commit also has a real conflict, the new fence refuses a correct resolution.
  - This is safe: the train stops and nothing wrong lands. But it is narrower than before.
  - Suggested fix: allow rename targets from `git diff --cached -M HEAD` whose source `REBASE_HEAD` owns.
  - Decide whether to accept it as a known limit or file a seed.
- **The other Medium, already known.** The fence works by path, so a resolver can stage different text for a path `REBASE_HEAD` owns that didn't conflict, and it passes. The spec names this under *Known limit*, and `runs/spec-questions.md` left it for you. The security reviewer notes that no open question records it, and suggests a seed for a `git merge-tree` text check.
- **Two Lows from the security reviewer:**
  - `_z_listing` decodes with `encoding="utf-8"` but no `errors=`. A path that isn't valid UTF-8 crashes with a traceback instead of refusing cleanly. It still stops before anything is staged.
  - A resolver could forge unmerged index entries. This existed before this change.
- **No published interface touched.** The change only narrows the existing contract in AGENTS.md (*The factory*: "the resolver only the files the conflict names, which `resolve --continue` checks"), which the approved spec names under *Contracts touched*. That sentence becomes more accurate.
- Nothing is destructive and no secret is involved. The plan's Rollback is `git revert`.

- IMPACT: patch — `resolve --continue` now refuses staged paths outside the replayed commit, and refuses when no rebase is under way. That fixes bug 2026-11-20-27 in the landing. Nobody holding the previous release has to do anything differently.
