DECISION: ESCALATE

**Why.** The build looks done and safe to land. All six round-1 reviewers returned `VERDICT: PASS`, and the gate is green (`./check.sh`, 3437 passed, exit 0). The reviewers found a named, failable test for every requirement R1–R22, and an acceptance check covers R23. What holds the change back is one assumption only you can confirm: D3, the builder's decision to reword more places than R7 and R9 list. It is a question of scope, which an approver must never settle.

**Open items**
- None. Both findings in `findings.md` are recorded nits: F1, the ledger listing D1/D4 and D2/D5 twice (raised by code), and F2, a dense fixture list in `tests/test_feature_map.py:273` (raised by test). Security also left an Info nit that isn't in `findings.md`: the docstring at `scripts/sdlc.py:3361` says the gate tail is "already masked", but paths are only replaced with placeholders. No secrets are removed.

**Decisions to confirm**
- No blocking decision is unticked. R1, your call, is ticked.
- SETTLED: D1: R23 (your call in R1 and the spec) requires REFERENCE.md's *After an update* to name `sdlc.py check`. The term test exempts only that paragraph and fails if the paragraph goes (`RENAME_NOTE`, plan.md *As built*). The test reviewer judged the scope "sound", and the security reviewer cites the note as how hosts learn of the break.
- SETTLED: D2: R18 makes `, passed`/`, failed` depend on `build/land-accept.md` holding an attempt, and only a factory landing writes that file. The spec's *Alternatives rejected* rules out adding a record to `sdlc.py accept`. `factory_records.accept_verdict()` and `test_a_card_counts_acceptance_and_its_last_run` cover it.
- ESCALATED: D3: the builder reworded more than R7 and R9 list. That includes the person-facing landing question ("build check" → "the slow gate"), the land, retro, intent and health skills, REFERENCE.md's metrics lines, and the factory README's *The gates* heading, now *The approvals*. The spec's Design does say "everywhere else, a retired phrasing is reworded where it stands". But how far a change reaches is scope, and only you can confirm it.
  - OPTION: reword everywhere found. Pro: one meaning per word, as the intent's outcome asks, and R10's term test stays clean. Con: a larger diff for ship to read, and the landing question's text changes.
  - OPTION: revert to only the listed spots. Pro: a smaller diff. Con: "gate" still means a person's yes in several docs and the landing question, against the intent, and a later change would need to finish the job.
  - OPTION: keep the doc rewording but restore the landing question's wording except for R8's "approved as shown". Pro: script output changes only where the spec named it. Con: "build check" stays in a question people read, against R9's "the slow gate".
  - WHY: the intent's outcome, "a newcomer reading the docs, the board or a report meets one meaning per word".
- SETTLED: D4: a duplicate of D1 (same R11/R23 conflict, same options), so it is settled on the same grounds: R23's required note and the scoped `RENAME_NOTE` exemption that the test reviewer judged sound.
- SETTLED: D5: a duplicate of D2 (same card text, same options), so it is settled on the same grounds: R18 and the spec's *Alternatives rejected*.

**For the person at ship**
- **Words beyond the spec's list.** Read `plugins/factory/scripts/landing.py`'s question ("approved as shown", "the slow gate") and the reworded skill and README text that D3 covers.
- **The board.** Check the gate badge's command/summary line in `scripts/board.py` / `board.html` and `gate_summary()`. The UX reviewer couldn't see it on a 390px card, or see the `acceptance: N, passed/failed` state, in any screenshot.
- **Reading old records.** Check `RENAMED` in `factory.py` and `factory_records.py`, which lets old `verifier`/`verify` records still read. Also check the `runs/verifier.sessions` fallback when the arbiter is resumed.
- **Published interfaces you already approved.** Each is built as you approved it:
  - `sdlc.py check` → `sdlc.py vet` with no alias: intent *Contracts*, spec R1–R3 and *Contracts touched*, decisions.md R1.
  - `[models] verifier` dropped with no shim: spec *Contracts touched*, decisions.md R1.
  - Agent `sdlc-factory:verifier` → `sdlc-factory:arbiter`, and tasks `verify`/`land-verify` → `arbitrate`/`land-arbitrate`, with the files moved by `git mv`: spec R12 and *Contracts touched*, decisions.md R1.
  - The guide heading `#### The gate and the slow gate`: spec R9, decisions.md R1.

- IMPACT: minor — A host's skills now call `sdlc.py vet`, and CI that runs `sdlc.py check` must switch. You decided `minor` for this removal (intent, spec R23, decisions.md R1), even though the guide's table would say `major`.

**How to recover**
- RECOVER: defaults/SDLC.md: fix forward: a follow-up change restores `#### The gate and the slower check` in `guide/process.md`, `defaults/SDLC.md` and `.sdlc/SDLC.md`, and reruns `sdlc.py record`. Hosts that took setup's refresh then get it proposed back. A host that didn't still has its answer read under the parent block (`doc_units()`), so nothing is lost.
- RECOVER: templates/findings.md: fix forward: a follow-up restores the note's wording. Each host's `findings.md` already committed with the "arbiter" note keeps it. Nothing reads that wording; `sdlc.py` reads only the finding lines, which are unchanged.
