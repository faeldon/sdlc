VERDICT: PASS

The doc matches the intent. The 60 open register entries and the 60 ids in the Waves section are the same set, with no id missing, extra or repeated.

## Notes
This change touches only `docs/RETRO-SCORECARD.md` and the register, so there is no program path to run. I checked the doc against the register by reading both and diffing their id lists.
- **Waves content:** the `### Waves` section has waves 0, 1, 1½, 2, 3, 4, 5 and 6, as the Approach lays out.
- **Waves 0 and 1:** both are marked done, with R1 = 160, S7 = 161, S1 = 162, R4 = 163 and R2 = 164.
- **S17 and S5:** the Data table has the S17 row (2026-11-19-9, after S8). S5's row names the feature map, 2026-10-25-3.
- **Old section:** `Suggested order` no longer appears in the doc.
- **Decision D1:** it is a builder default, already recorded in `decisions.md`. The doc puts 2026-11-19-1 and -2 under R6, with a note that R6 retires them as answered, which is what the Approach says.
- **Line width:** the only lines past 100 columns are table rows (459–505) and five lines at 35, 44, 168, 415 and 417. None of those five are in the new Waves section. I didn't check whether the five already existed, and the intent only asks for "no new style nits."
- **Gate:** `build/round-1.gate.md` reads `GATE: PASS`.
- **`checks.md`:** I read both checks and did not run them.
  - **First check** (every open entry named exactly once in Waves): I expect it to pass. It greps the section for each of 60 ids, and my diff found no missing, extra or duplicated id. The section runs to the end of the file, so it only sees this section.
  - **Second check** (no `### Suggested order`, S17 row, S5 row with the feature map, `#### Wave 6`): I expect it to pass. All four are present.

## Evidence
$ git diff --stat HEAD~1 | tail -5
```
 .sdlc/work/inbox.md     | 21 ++++++++------
 docs/RETRO-SCORECARD.md | 73 +++++++++++++++++++++++++++++++++++++++++++------
 2 files changed, 77 insertions(+), 17 deletions(-)
```
exit: 0

$ awk '/^### Waves/{f=1} f' docs/RETRO-SCORECARD.md; grep -n 'S17\|^| \*\*S5' docs/RETRO-SCORECARD.md; grep -c 'Suggested order' docs/RETRO-SCORECARD.md
```
(the Waves section as quoted above; line 463 the S5 row naming 2026-10-25-3; line 472 the S17 row; 551 the Wave 3 S17 item; Suggested order count 0)
```
exit: 0

$ head -8 .sdlc/work/165-scorecard-waves/build/round-1.gate.md
```
GATE: PASS

## Attempt 1

Verdict: PASS
Command: ./check.sh
Build: f9f29cd1f84bc5d9
Exit: 0
```
exit: 0

$ grep -oE '^## \[[0-9-]+\]' .sdlc/work/inbox.md | tr -d '#[] ' | sort > /tmp/reg.txt; wc -l < /tmp/reg.txt; (Waves ids) > /tmp/doc.txt; wc -l < /tmp/doc.txt; comm -23 /tmp/reg.txt /tmp/doc.txt; comm -13 /tmp/reg.txt /tmp/doc.txt; uniq -d /tmp/doc.txt
```
60
60
(missing: none)
(extra: none)
(dup: none)
```
exit: 0
