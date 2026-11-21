VERDICT: PASS

Every requirement has code and a test. The gate record `build/round-1.gate.md` is green (`GATE: PASS`, exit 0). I ran no test myself.

- **Prompts.** `builder.md`, `resolver.md` and `reviewer-behaviour.md` now ask for `exit: <n>` after every command, reads included. The behaviour prompt's gate-record citation shows `exit: 0`. `prompts/mend.md` and its three golden files say the same.
- **Script.** `is_read()` and `read_evidence()` are unchanged, as the constraint requires. Only the `READS` comment changed.
- **Tests.** The wording test fails on any prompt that still lets a read leave its exit off. The three commands from today's stops read clean with an exit and are still flagged without one, so the rule did not loosen.
- **Accept nit.** `cmd_accept()` now re-checks that its record is vouched after the checks ran, as `cmd_gate()` does. `test_a_record_forged_while_accept_ran_is_never_appended_to` covers it.
- **Nit 2026-11-20-47.** Left out, with D1 recording why and a default of "leave it out". That is sound: the change folder is untracked at the fork point, so a read there would loosen the bar.
- **Wording search.** A grep for the old wording across the repo found no leftover outside the tests.

## Notes
- NIT: AGENTS.md says "every command with its `exit:` but a read that shows its output". That is still true of the script's rule, so I left it alone. If you want the prompts' stricter ask recorded, a half-sentence would do it. {docs S low}
- Done well: the wording test pins the exact set of prompts that end with `## Evidence`, so a new one can't slip through. The accept re-check reuses `_unvouched_refusal()` with the same rewording `cmd_gate()` uses.
- Ran: nothing beyond reading the diff, the plan and the gate record.
