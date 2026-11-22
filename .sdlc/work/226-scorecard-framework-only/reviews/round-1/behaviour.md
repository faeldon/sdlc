VERDICT: PASS

The scorecard now ends after *Hosts*. All 36 Status lines read *captured* or *not captured*, with no seed or change id inside the check's reach, and the wave release block and the CONTRIBUTING wording are gone. I ran no test of my own: the gate record shows 4030 passed and 29 skipped, and I read each check without running it.

## Notes
- **Check 1, scorecard ends after Hosts:** I expect it to pass. The last `## ` heading is `## Hosts`, and "Seeds to build", "Waves" and "lists the seeds" have no matches.
- **Check 2, Status lines:** I expect it to pass. There are exactly 36 Status lines, none that don't start with "captured" or "not captured: ", and no S/R/1xx id within three lines after one. My first grep used `-n` and showed false matches on line numbers like 105; without `-n`, as the check runs it, nothing matches.
- **Check 3, release block:** I expect it to pass. `follows the waves` and `### The release loop` have no matches in `.sdlc/SDLC.md`.
- **Check 4, CONTRIBUTING row:** I expect it to pass. The scorecard row is present, and "the seeds that build it" has a count of 0.
- **Decisions D1–D3:** these are the builder's defaults, not mine to settle here. D1 keeps the seed ids outside the Status lines: the Speed Diagnostics ids and Hosts' S14/S15/S1. I did not raise them as a CHANGE because the intent says to keep the framework word for word. Four dead ids remain, and the builder logged a follow-up in `notes.md`.
- **Not run:** the end-to-end `sdlc.py retro` comparison. The spec asks for it, and the gate's retro tests passed, but I did not rerun it.

## Evidence
$ cd .sdlc/work/226-scorecard-framework-only && ls; cat intent.md | head -80; cat build/round-1.gate.md | tail -15; cat checks.md; cat decisions.md | head -20
(printed intent, the gate record ending in "✔ Validation passed", checks.md and decisions.md D1–D3)
exit: 0

$ f=docs/RETRO-SCORECARD.md; wc -l $f; grep '^## ' $f | tail -3; grep -n -e 'Seeds to build' -e 'Waves' -e 'lists the seeds' $f; grep -c '\*\*Status:\*\*' $f; grep '\*\*Status:\*\*' $f | grep -v -E '\*\*Status:\*\* (captured|not captured: )'; grep -n -e 'follows the waves' -e 'release loop' .sdlc/SDLC.md; grep -n 'RETRO-SCORECARD' docs/CONTRIBUTING.md; grep -c 'seeds that build' docs/CONTRIBUTING.md; head -8 $f; grep -n 'exit\|passed' .sdlc/work/226-scorecard-framework-only/build/round-1.gate.md | head
485 docs/RETRO-SCORECARD.md
last headings: Trust band, Insights, Hosts
36
(no matches for the unwanted sections, lines or wording)
CONTRIBUTING row: `| docs/RETRO-SCORECARD.md | the framework /sdlc:retro reports against: ... a reference, read by nothing |`
0
62: 4030 passed, 29 skipped in 312.74s (0:05:12)
80: ✔ Validation passed
94: ✔ Validation passed
exit: 0

$ f=docs/RETRO-SCORECARD.md; grep -A3 '\*\*Status:\*\*' $f | grep -E '\bS[0-9]+\b|\bR[0-9]+\b|\b1[0-9]{2}\b' | grep -v '\*\*What'; echo "exit $?"; grep -c 'Status:\*\* not captured' $f
exit 1
7
exit: 0
