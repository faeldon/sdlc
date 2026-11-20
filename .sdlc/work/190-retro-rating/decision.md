DECISION: READY

**Why.** All three round-1 reviewers returned `VERDICT: PASS`. The test reviewer matched each of R1–R15 to a test that fails without the code. The gate (`./check.sh`) passed: 3534 passed, 29 skipped, exit 0, tree unchanged. The only findings are three low nits (F1–F3). The one undone item in `notes.md` is a by-hand check the spec itself left for ship. No review suggests the spec was wrong, and the build follows `plan.md`.

**Open items**
- None. No CHANGE is unresolved. The nits F1 (code), F2 (code) and F3 (test) are recorded in `findings.md` and don't block.

**Decisions to confirm**
- None. There is no `decisions.md` ledger for this change, and the prompt names no open default.

**For the person at ship**
- **Look first: the two-question dialog's answer order.** The spec's *Contracts touched* asks someone to check one real `/sdlc:retro` transcript before ship. The check is that `toolUseResult.answers` lists the approval first, so `metrics._answers()[0]` is still the approval. R11's test (`tests/test_metrics.py`) only uses a synthetic transcript built in the shape the reader expects; no reviewer could check the real harness. If the order isn't kept, the fix is a change to metrics, which the spec's Boundaries put under "ask first".
- `skills/retro/SKILL.md` Step 5: there is still one `WAIT` heading, the approval is asked first, the rating "never approves", and a dismissed rating is no rating.
- `scripts/retro.py`: `experience_answer()`, `_last_experience()` (it does `int(rating)` on a hand-edited cell, F2), and the draft handling in `cmd_retro_commit()`. The draft is dropped from the stray check, refused when malformed, and removed only after the commit succeeds.
- **Published interfaces you already approved in `spec.md` *Contracts touched*:**
  - the WAIT/dialog contract (`tests/test_skills.py`)
  - metrics reading the dialog's answer as the approval
  - `retro-commit`'s four files
  - `{{experience}}` added to `templates/retro.md` without a `TEMPLATE_READS` entry
  - the `sdlc.py record` rehash of `.sdlc/setup.json`
- **Minor:** in the behaviour review, `drift` exited 1 while reporting `breaking: []` and `refresh: []`. The gate, which fails on drift, is green.

- IMPACT: minor — someone on the previous release can now record a rating and a line at the retrospective's approval and see it read back as a trend; nothing they already do changes.

- UNDONE: Before ship (spec, *Contracts touched*): read one real `/sdlc:retro` transcript with the two-question dialog and confirm `toolUseResult.answers` lists the approval first, so `metrics._answers()[0]` is the approval. R11 pins the shape `_answers()` reads, not the harness. → seed: Confirm a real two-question retro transcript lists the approval first

- RECOVER: templates/retro.md: `git revert <the change's commit>`, then run `uv run --quiet --script scripts/sdlc.py record` so `.sdlc/setup.json` matches the old template again. A host's own override in `.sdlc/templates/` and the reports it already committed with `## Experience` stay; they're harmless, because a reverted reader ignores the table. A host with an uncommitted `.sdlc/retros/<date>.experience.md` deletes it with `rm` before its next `retro-commit`.
