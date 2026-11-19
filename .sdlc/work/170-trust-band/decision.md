DECISION: READY

**Why.** All four round-1 reviewers (code, test, security, behaviour) returned `VERDICT: PASS`. The test reviewer confirms every requirement R1–R14 has a test that fails without it. The round-1 gate is green: `./check.sh` gave 3081 passed and 28 skipped, and `claude plugin validate --strict` passed. The plan names and explains each departure from the spec (the `_model_word()` cleaning, ship's `cases.md` branch left out of a host's `prose`, and the `landing_catches` test fixture now carrying `Sdlc-Mode: factory`). None of them suggests the spec itself was wrong.

**Open items**
- None. No reviewer raised a CHANGE. Four nits are already recorded in `findings.md`: F1 and F2 from code, marked minor, and F3 and F4 from security, marked recorded.

**Decisions to confirm**
- No blocking decisions are unticked.
- SETTLED: D1: R11 says a host's retro JSON must hold no `cases` key outside `tests.times`. `test_a_hosts_retrospective_never_mentions_the_cases` fails while `prose` lists ship's `cases.md`, so the default is what the spec already demands. The other option, narrowing R11, would rewrite the spec. Plan.md explains the change and the code reviewer agreed with it in round 1.
- SETTLED: D2: R5 writes the `none:` reasons out bare (`no transcripts for this repo`) and makes spend's reason "its existing `why`". `_none_reason()` keeps the two the same, and the test reviewer confirms the R4 test checks spend's `missing_because` equals its `why`. The code reviewer agreed with this default in round 1.
- SETTLED: D3: R2's own test needs a version to come back as text with no `/`, `~` or space. `_model_word()` is `_word()` with `,` and `:` also replaced, so it is stricter and the line's format is still the one R2 specifies. Plan.md explains the departure. The security review shows it stops a value forging a second trailer, splitting in two, or reading back as a key:value pair.

**For the person at ship**
- **`scripts/closing.py`:** `finish()`'s new `try` around the runtime line, and `_lead_marks()` skipping `runtime` events. Together they keep lead time as it was and keep the close landing.
- **`scripts/retro.py`:** `_none_reason()`'s regex. Security found it backtracks badly on a hand-written `Sdlc-Coverage` trailer (F3), and the one-line fix is `(\s+[^\s=]+=\S*)+$`.
- **`scripts/retro.py`:** `_previous_window()` falls back to index 0 when `since` isn't among the retrospective bounds (F2).
- **Host `prose`:** the `OWN_REPO_BRANCHES` filter (D1).

- IMPACT: minor — closes now write a new `Sdlc-Runtime` trailer, and a host's retrospective newly shows each headline's coverage, why the rest is missing, what changed underneath, and a no-factory sentence. No existing trailer or key changes meaning.

**Undone items**
- None. The change folder has no `notes.md`, so there are no unticked `- [ ]` items.

**How to recover**
- The prompt names no irreversible paths. Plan.md's rollback is `git revert`; the `Sdlc-Runtime` lines that closes write in the meantime stay in history but are harmless, since no reader counts an unknown key.
