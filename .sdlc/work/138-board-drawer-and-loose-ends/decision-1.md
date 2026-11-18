DECISION: ESCALATE

**Why.** The build is finished and has converged. All three round-2 reviewers returned `VERDICT: PASS`, the round-2 gate passed (`./check.sh`: 2410 passed, 13 skipped, `drift` empty), and each round-1 finding the verifier kept (C1, C2, C3) is fixed and tested. It still needs you, because all four decisions in `decisions.md` are unticked defaults the build rests on. D3 also takes the build past the intent's Approach (a new `waits_on_push` / `dangling_unread` field in `intake`'s output, written up in `docs/REFERENCE.md`), and D4 was never acted on.

**Open items**
- No CHANGE is open. Round 2 left only nits, recorded in `findings.md`: F3 (`# fmt: skip` not needed, code), F7 (Step 6 line in triage is 168 characters, code) and F8 (test docstrings cite "138 C1"/"C2", code).
- ux round 2 also asked for small things: Step 6 could say the waiting issues "won't be offered again", and `dangling_unread` says "the base branch", which a person may not follow.
- ui round 2: when the tracker has no `closed_by`, `dangling_unread` still says "couldn't read the commits". The behaviour is safe, but the reason given is wrong. It can't happen today, because GitHub is the only tracker with `dangling`.

**Decisions to confirm**
- D1: the spec gate's question moves into the script (`spec_question()` in `factory.py`), and seed 2026-11-18-10 is not retired.
- D2: a late drawer response is dropped using a request counter, not `AbortController`, and not by matching on the path.
- D3: `intake` gains a per-issue `waits_on_push` flag (`null` plus `dangling_unread` when the unpushed commits can't be read). The Approach only asked for wording.
- D4: nothing was done. `plugins/factory/skills/spec/SKILL.md:91` (and `skills/spec/SKILL.md:120`) still offer "rethink the design" without saying what it does. The suggested default is to call it a no that writes nothing and logs your words like "revise" does, or else to remove the option. Either way the same answer goes into both skills, and it is not built in this change.

**For the person at ship**
1. `scripts/sdlc.py`'s `cmd_intake()` (about lines 7600–7625) and the `docs/REFERENCE.md` lines on it. This is the one new field in a documented output, and it is where the build leaves the plan.
2. `factory.py`'s `spec_question()` against the sample in the factory spec skill's Step 2.
3. `show()` and `paint()` in `scripts/board.html`. No screenshot shows the drawer open, so the empty-file note was checked only by reading the code and by the tests.

- IMPACT: patch — the drawer stops showing a stale or blank file, and triage stops offering issues that only wait on a push. `intake` gains a field, which is additive, and nothing a host does has to change.

- UNDONE: pre-existing: scripts/board.py:626: a card reads "decide D1 in the factory's supervisor". A person doesn't know what the supervisor is or where to go. This change doesn't touch that text. → bug: low: scripts/board.py: A needs-you card says "decide D1 in the factory's supervisor" without saying what D1 is or where to go

- RECOVER: templates/findings.md: fix forward: revert the note's wording in `templates/findings.md` and `FINDINGS_HEAD` (`plugins/factory/scripts/factory.py`) together, then rerun `uv run --quiet --script scripts/sdlc.py record` so `drift` stays clean. Any host `findings.md` already written with the new note keeps it. That is harmless, because it is a `>` note no parser reads, and `sdlc.py` reads only the `## ` sections and their field lines.
