DECISION: ESCALATE

**Why.** The build itself is done. All three round-3 reviewers returned `VERDICT: PASS`, the round-3 gate passed (`./check.sh`, 2410 passed, 13 skipped, `drift` clean), `sdlc.py accept 138` passes, and R1 (your answer to D4) is built in all three places. The build still rests on three defaults you haven't confirmed (D1–D3). D3 goes beyond the intent's Approach: it adds `waits_on_push` and `dangling_unread` to `intake`'s output and documents them in `docs/REFERENCE.md`, which is a published interface. That needs your eyes before `main`.

**Open items**
- No CHANGE is open in any round. Only nits remain in `findings.md`: F3 (`# fmt: skip` not needed, code), F7 (168-character line in triage Step 6, code), F8 (test docstrings cite "138 C1"/"C2", code) and F9 (`test_no_build_question_for_a_refusal_or_a_spec` is misnamed now, code).
- ux round 3 left optional suggestions only: the loading text could name the file, the error could drop the HTTP status, "advance to stage: design" is jargon in both spec skills, and `dangling_unread` should be worded the same in triage's Step 0 and Step 6. ux and ui both say no screenshot shows the drawer, at either width.

**Decisions to confirm**
- D1: the spec gate's question moves into `factory.py` (`spec_question()`), and seed 2026-11-18-10 is kept and built, not retired.
- D2: a late drawer response is dropped with a request counter in `show()`, not cancelled with `AbortController` and not matched on the path.
- D3: `intake` gives each dangling issue a `waits_on_push` flag. The flag is `null`, with `dangling_unread` saying why, when the unpushed commits can't be read. The Approach asked only for a wording change in triage.
- D4: your restart answer R1 settled it ("rethink the design" removed from both spec gates), but the D4 line itself is still unticked. Tick it as decided by R1 at ship.

**For the person at ship**
1. `scripts/sdlc.py`'s `cmd_intake()` (the `waits_on_push` / `dangling_unread` fields) and the matching lines in `docs/REFERENCE.md`. This is the new public output, and the one place the build leaves the intent.
2. `factory.py`'s `spec_question()` next to the sample in `plugins/factory/skills/spec/SKILL.md` Step 2, and `skills/spec/SKILL.md` Step 4. All three should now read `(yes / revise a requirement)`.
3. `show()`, `paint()` and `openDrawer()` in `scripts/board.html`. No screenshot shows the drawer, so open an empty `.md` in a running board, at 390px as well, before you approve.

- IMPACT: patch — the drawer no longer shows a stale or blank file, the spec gate's question is worded once, and triage no longer offers issues that only wait on a push; `intake`'s new fields are additive, and nothing a host does has to change.

- UNDONE: pre-existing: scripts/board.py:626: a card reads "decide D1 in the factory's supervisor". A person doesn't know what the supervisor is or where to go. This change doesn't touch that text. → bug: low: scripts/board.py: A needs-you card says "decide D1 in the factory's supervisor" without saying what D1 is or where to go

- RECOVER: templates/findings.md: fix forward: a follow-up change puts the old note back in `templates/findings.md` and `FINDINGS_HEAD` (`plugins/factory/scripts/factory.py`) together, then reruns `uv run --quiet --script scripts/sdlc.py record` so `drift` stays clean. A host `findings.md` already written with the new note keeps it, which is harmless: it is a `>` note no parser reads, since `sdlc.py` reads only the `## ` sections and their field lines.
