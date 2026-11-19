Those awk hits are byte counts of multibyte lines (≤100 characters), so they're fine.

VERDICT: PASS

## Notes
- Gate record `build/round-1.gate.md`: `GATE: PASS`.
- End-to-end path: the spec names none. The change is rewrap-and-comment only. I ran the first check's scan by hand against the changed files and it found no prose line over 100 columns. The diff shows `check.yml`'s header comment rewrapped with no other change. I saw no behaviour change in the diff of `check.yml`, `function-heat.py` or `check.sh`.
- I did not run `checks.md`; I read each section.
  - "The named files have no prose line past 100 columns": I expect it to pass. It lists the files the diff touches, and the same scan printed nothing.
  - "check.sh says why its summary counts skipped tests": I expect it to pass. Both `grep` strings are in the comment at `check.sh` lines 11–12.
  - "heat() says how a file added after the boundary counts": I expect it to pass. The comment is at `.sdlc/function-heat.py:124`.
- `plugins/factory/agents/*.md` besides `reviewer-code.md` and `reviewer-ux.md` show hits in a byte-length `awk` scan. Those are multibyte characters, not lines past 100 characters. The Python scan, which counts characters, shows none in the two agent files it covers. The nits named only `reviewer-code.md` and `reviewer-ux.md`.
- The diff also lists `.sdlc/work/inbox.md` (39 added lines). That is not part of the intent's files, so I'm only mentioning it, not raising it.

## Evidence
$ cd .sdlc/work/173-style-paydown && ls . build; head -5 build/round-1.gate.md
GATE: PASS
exit: 0

$ git diff --stat <merge-base>
8 files changed, 170 insertions(+), 124 deletions(-)
exit: 0

$ grep -n 'pytest -rs` names each reason\|skipped` count is expected' check.sh
11:# `skipped` count is expected: ...
12:# ... `pytest -rs` names each reason.
exit: 0

$ grep -n 'A file added after `since` has no boundary lines' .sdlc/function-heat.py
124:        # A file added after `since` has no boundary lines, ...
exit: 0

$ python3 -I -c '<check 1 scan over the seven files>'
(no output)
exit: 0

$ awk 'length>100 ...' plugins/factory/agents/*.md plugins/factory/README.md
(hits on multibyte lines; the lines I viewed were ≤100 characters)
exit: 0

$ git diff -U0 .sdlc/function-heat.py check.sh .github/workflows/check.yml
(comment-only changes)
exit: 0
