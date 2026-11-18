VERDICT: PASS

The change adds a doc and a layout row, and the spec describes no command to run end to end, so I compared the doc with the approved draft and with the code.

## Notes
- **Closest path:** `docs/RETRO-SCORECARD.md` differs from `draft.md` only in the status lines `notes.md` says were corrected. I spot-checked two of those against `scripts/retro.py`: `out_per_line` and `throughput` are both there.
- **Check "The scorecard doc holds the framework" (expected to pass):** the doc has every heading it greps for (title, Value band, Pillars 1–5, Trust band, Insights, Seeds to build it). I counted three lines with `S16**` or `R6**`, so those markers are present. I did not run the check itself.
- **Check "CONTRIBUTING's layout lists the doc" (expected to pass):** the diff adds a row starting `| \`docs/RETRO-SCORECARD.md\` |`.
- **Open `- [ ]` in `notes.md`:** the "Hosts" item is unticked. It is for ship to give a disposition, not a failure here.
- **Not run:** I did not run `./check.sh` or any test. The gate record shows `GATE: PASS` with exit 0.

## Evidence
$ cd .sdlc/work/159-retro-scorecard-doc && ls . build; cat intent.md; cat checks.md; cat build/round-1.gate.md | tail -15; git status --short | head; git diff --stat $(git merge-base HEAD main) | tail -10
(reads; the gate record ended in `✔ Validation passed`; the diff touched only `docs/CONTRIBUTING.md`, plus the untracked new doc and change folder)
exit: 0

$ grep -n '^#' docs/RETRO-SCORECARD.md | head -40; grep -c 'S16\*\*\|R6\*\*' docs/RETRO-SCORECARD.md; git diff docs/CONTRIBUTING.md; diff .sdlc/work/159-retro-scorecard-doc/draft.md docs/RETRO-SCORECARD.md | head -40; cat notes.md | head -40; head -12 build/round-1.gate.md
(reads; the headings are present, the S16/R6 count was 3, the diff against the draft showed only the status edits, and the gate record's first line was `GATE: PASS`)
exit: 0

$ grep -c 'out_per_line' scripts/retro.py; grep -c 'throughput' scripts/retro.py; grep -n '^## ' docs/RETRO-SCORECARD.md | tail -8
(output: 1, 4, then the headings from Pillar 1 through Seeds to build it)
exit: 0
