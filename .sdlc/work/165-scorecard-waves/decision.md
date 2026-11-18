DECISION: READY

**Why.** The intent asks for four things, and all four are in the doc. *Waves* replaces *Suggested order*. Waves 0 and 1 are marked done with their change numbers (160–164). S17 has a row in the *Data* table, and S5's row names the feature map 2026-10-25-3. Both reviewers checked the doc against `inbox.md` by script: its 60 ids match the 60 open register entries, with none missing, extra or named twice. Both round-1 reviewers returned `VERDICT: PASS`, the gate ran `./check.sh` green (3052 passed), and the diff touches only `docs/RETRO-SCORECARD.md`, a design doc that no code or host reads.

**Open items**
- None. The code reviewer's one NIT (F1: the S17 table row runs past 100 columns, as its neighbouring rows do) is already marked `minor` in `findings.md`.

**Decisions to confirm**
- No blocking decisions are open.
- SETTLED: D1: the intent settles it. Its Outcome requires "every register entry open when this lands is named in exactly one wave", and its Approach says "R6 takes 2026-11-19-1 to -4 and -100". The doc only lists the two nits under R6. Whether they are actually retired is up to R6's own intent and landing, so this change neither builds nor retires anything. Both reviewers (code.md, behaviour.md) confirmed the doc follows this default.

**For the person at ship**
- **Re-check the ids first.** The intent asks for a hand check of the *Waves* ids against `sdlc.py status --all` on `main` just before ship. The builder and both reviewers matched the 60 ids against the register as it stood at build time. Any nit filed since then needs adding to the wave of the change that touches its files.
- **Then read these:**
  - Wave 1½ and Wave 2 in `docs/RETRO-SCORECARD.md` (lines 527–543), where most of the ids are.
  - The S17 row in the *Data* table.

- IMPACT: none — only this repo's design doc changed; nothing a host receives behaves differently.

**Undone items:** there are none. This change has no `notes.md`, and the builder reported nothing left over.

**How to recover:** no lines are needed, because the prompt names no irreversible paths.
