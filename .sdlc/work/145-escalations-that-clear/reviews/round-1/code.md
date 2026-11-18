VERDICT: PASS

I reviewed the factory side (`ledger`, `ask`, `decisions`) in the diff. I did not read the `sdlc.py` or `board.py` changes line by line, and I did not walk every requirement through to its test.

## Notes
- The gate record `build/round-1.gate.md` is green (attempt 1, `./check.sh` exit 0, tree unchanged). I did not run the gate or any test myself.
- **Checked against the spec, and consistent:**
  - **R2:** `escalation_reasons()` reads only the current `decision.md`. A word that is not `gate`, `look` or `D<n>` reads as a `look`, with the word kept in its text.
  - **R3:** `cmd_decisions()` files each `look` reason once per `(source round, text)`. A rerun writes nothing, and a restart files a new line because `newest_round()` changes.
  - **R4:** a `look` line is excluded from `by_text`, so a blocking or default line can't match it.
  - **R5:** `_settle_refusal()` refuses a `look` line with "is the person's to acknowledge". `upgrade_answer()` still reads only `blocking` lines.
  - **R6:** `read_ledger()` marks a `look` line open only while `look_current()` holds (newest round plus exact text).
  - **R11:** `cmd_ask()` gives a `look` item `reply: decision.md`.
  - **R27:** `NO_DECISION` and `_no_verdict()` are reworded.
- **Done well:** a `look` line is open only while it is current, which keeps an acknowledgement from carrying over to a new build. The builder's two default decisions (D1, D2) are reasoned and stay within the spec.
- **Nit (not rated, no cost or value weights):** D1 makes two gate reasons print as two identical `Escalated` lines. That is the spec's exact wording, so it is only recorded here.
