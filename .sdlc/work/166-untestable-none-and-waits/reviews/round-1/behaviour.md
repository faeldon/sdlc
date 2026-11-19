VERDICT: PASS

The spec's end-to-end path is the reader of `- UNTESTABLE:` lines. I ran it directly on the new regex and it does what the intent says.

## Notes
- **Empty answers:** `none`, `none.`, `None`, `n/a` and `N/A.` no longer match, so `verdicts` and `early_stop()` won't stop on them.
- **Real gaps:** `R3 needs a live GitHub` still matches, and so does `none of R3 can be tested`, which is a real gap.
- **Both copies:** `factory.py` and `factory_records.py` carry the same regex, so the name-wide pin test holds and the board and `status` read the same lines.
- **Gate:** `build/round-1.gate.md` shows `GATE: PASS` and exit 0.
- **Waiting guidance:** `builder.md` and `reviewer-behaviour.md` both gain a "never `sleep`, use a timeout or a bounded loop in one command" paragraph.
- **Whitespace-only answer:** `- UNTESTABLE:` followed by only spaces still matches, because the regex backtracks. That is the old behaviour and outside the intent, so I'm not raising it.
- **Prompt recordings:** the change touched agent files, not `prompts/*.md`, so there are no `tests/prompts` copies to re-record.
- **`checks.md`:** none exists for this Tier 1 change, so there are no checks to read.

## Evidence
$ cat .sdlc/work/166-untestable-none-and-waits/build/round-1.gate.md
GATE: PASS
Verdict: PASS
Command: ./check.sh
Exit: 0
exit: 0

$ git diff HEAD~1 -- plugins scripts
(diff showed the regex change in both files and the two agent-file paragraphs)
exit: 0

$ python3 -I - (new regex run against 8 sample lines)
- UNTESTABLE: none False
- UNTESTABLE: none. False
- UNTESTABLE: None False
- UNTESTABLE: N/A. False
- UNTESTABLE: n/a False
- UNTESTABLE: R3 needs a live GitHub True
- UNTESTABLE: none of R3 can be tested True
- UNTESTABLE:    True
exit: 0

$ uv run --group dev pytest tests/test_factory.py tests/test_board.py tests/test_modules.py -q -k "untestable or none"
7 passed, 672 deselected in 4.56s
exit: 0
