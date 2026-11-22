I addressed both kept changes. No seed ids or change numbers are left anywhere in `docs/RETRO-SCORECARD.md`. All five acceptance checks pass, and so do the 435 tests that read these docs.

- KEPT code [correctness] RETRO-SCORECARD.md:465: I reworded the *Hosts* opening to "The scorecard reaches hosts by way of the plugin, and each part goes where a host already finds its kind:". It no longer names S14 or S15 or talks about building it later.
- KEPT code [correctness] RETRO-SCORECARD.md:154,156,481: I removed the "(S10, 175)" notes from the Feedback-loop time and Landing time bullets and the "(S1)" from the lead-time paragraph. The rest of each sentence is unchanged.

**New acceptance check** in `checks.md`: "No seed id or wave change number is left anywhere in the scorecard". It searches the whole doc for `S<n>`, `R<n>`, `(1nn)` and `, 1nn)`. Baseline change ranges such as `139–148` are figures rather than plan ids, and the pattern doesn't match them.

**`plan.md`:** unchanged. **`notes.md`:** I deleted the follow-up about the leftover ids, since this round removed them. The note about five lines that were already longer than 100 columns stays.

- DECISION: [default] (supersedes D1) Remove the seed ids that sit outside the Status lines too, keeping the rest of each sentence. This is now built, following the reviewers' kept changes.
  - OPTION: remove them — no ids in the doc point at nothing; four sentences lose a short note, which strays slightly from the word-for-word rule
  - OPTION: keep them — follows the word-for-word rule exactly; four ids would still point at nothing
  - WHY: the Problem names ids that point at nothing as the defect, and removing them is the smaller deviation

- UNTESTABLE: none

## Evidence

$ grep -nE '\bS[0-9]+\b|\bR[0-9]+\b|\(1[0-9]{2}\)|, 1[0-9]{2}\)' docs/RETRO-SCORECARD.md; echo "exit: $?"
exit: 1

$ cat .sdlc/work/226-scorecard-framework-only/notes.md
# Notes

- [ ] Five lines in `docs/RETRO-SCORECARD.md` already ran past 100 columns (35, 44, 176, 452, 454);
  untouched here.
exit: 0

$ uv run --quiet --script scripts/sdlc.py accept 226 (summarised)
True 0 The scorecard ends after Hosts
True 0 Every Status line is captured or not captured, with no seed id or change number
True 0 This repo releases on Release due
True 0 The contributor docs no longer list the scorecard's seeds
True 0 No seed id or wave change number is left anywhere in the scorecard
passed True
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_retro.py tests/test_defaults.py tests/test_feature_map.py tests/test_nothing_local.py
435 passed in 93.53s (0:01:33)
exit: 0
