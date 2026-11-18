VERDICT: PASS

This change moves code that reads the factory's cost and land-time records. It adds no UI and alters none. The board looks the same as before in both screenshots.

## Notes
- **Screenshots read:** `land-2/ux/index-1280x800.png` and `index-390x844.png`.
  - At 1280 wide, the six columns show their counts and a "next:" line on every card.
  - At 390 wide, the board collapses to a single column, which is readable. The "needs you" cards show their reason and their next step.
  - The cost line renders as "cost —" when there is no data. The header shows "$1.50 API-equivalent" and "12 min" where there is data. Neither is blank or raw.
- **Not read:** I did not open the diff or the changed files. The rest of my judgement comes from the screenshots and the change description alone. The screenshots show no sign of a regression from the move.
- **States I couldn't see:** loading and failure states are not in the screenshots. The change is a move of reading code, so I did not expect them to change.
- **Smaller observations (none needs action):**
  - Card tags such as "was ESCALATE" and "was READY" are small and grey. They are readable but low in contrast.
  - The same "cost —" wording is used wherever cost data is absent, which is consistent.
- **Done well:** the cards give a concrete next step in the person's terms, such as the exact command to run or the decision to make.
