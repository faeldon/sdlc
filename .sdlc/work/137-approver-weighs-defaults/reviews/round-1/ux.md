VERDICT: CHANGES

- CHANGE: scripts/board.py:636: the new `/sdlc-factory:decide NNN` is the only way to answer an escalated change's open decisions and defaults, and the board never names it. At `test` with `decide D1` pending, the card says "decide D1, then /sdlc:ship, or /sdlc-factory:land…". With only defaults to confirm (`confirm N defaults`, no `decide` ids), line 640 sends it to "/sdlc:ship, or /sdlc-factory:land with the others ready", which skips the confirmation the card says it needs. Make the next step at `test` with open items read `/sdlc-factory:decide NNN`, then ship or land. Keep the "in the factory's supervisor" wording for `build`.
- CHANGE: scripts/sdlc.py:4383: status's "What needs me" still says "confirm N default(s)" and never says where to do it. Add `/sdlc-factory:decide NNN` to the hint or to status's next-step line, so the person doesn't have to find the skill.
- CHANGE: plugins/factory/skills/decide/SKILL.md:35: `ask` refuses a change not at `stage: test`, and the skill says "say so and stop". It should also say what the person can do instead, for example wait for the run's decision, or answer the supervisor's own blocking questions. The same applies to the refusal for a bad or unknown NNN.

## Notes

- **Read:** the 1280px board screenshot, `intent.md`, `decisions.md`, `decide/SKILL.md`, `needs_of()` in sdlc.py and `next_step` in board.py.
- **Not read:** the 390px screenshot, `spec.md`, the other changed files, and the code for what `ask` prints or the board renders for settled defaults. I did not trace the approver's reply format or the ledger parsing.
- **Screenshot:** the board page is unchanged here, and its "needs you" card for 007 reads sensibly. The gaps are in the text that points to the new skill.
- **Not judged:** the dialog flow is Claude Code UI that no screenshot shows, so I judged it from the skill text.
- **Smaller finding:** Step 1 says options beyond three alternatives are "listed in the question's text, for the person to type". Say that the dialog's Other field is where they type it.
- **Smaller finding:** Step 3 says to record a typed answer "as they gave them", but doesn't say what to do with a multi-line answer in a one-line ledger entry.
- **Done well:**
  - The default comes first in every dialog, and `keep the default` / `change it` still works for ledgers written before this change.
  - Settled defaults are shown as a single block and never asked, so the person's word and the approver's call stay distinct.
  - A "yes" is required before anything is written.
  - Dismissed or empty answers are left open and said so, not filled in.
  - The skill ends with the next step in plain words and starts none of them itself.
