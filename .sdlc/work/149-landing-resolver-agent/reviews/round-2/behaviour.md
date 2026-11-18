VERDICT: PASS

The card's `next:` line now says "its agent is resolving a conflict". The test strings (`tests/test_board.py:1216` and `:1424`) match it. The board paragraph at `docs/REFERENCE.md:579` says "whose agent is resolving the conflict". I did not run a landing end to end, so the board path was checked only through its tests and the code.

## Notes
- **Kept change from round 1:** fixed in all four places. `board.py:843`, both test lines and the REFERENCE.md paragraph use "agent". No "its builder" wording remains in those three files.
- **End-to-end path:** the spec's board behaviour is a card for a factory landing with a stopped rebase and `resolve` as its step. It should show the wait-or-re-land `next:` line. `tests/test_board.py` passes (265 passed, 28 skipped), and that suite pins this card's wording and precedence.
- **checks.md, "The docs say the builder and the resolver edit, and the builder no longer resolves":** I read it and did not run it. I expect it to pass. The rework touched none of the files it greps (AGENTS.md, the factory README, `builder.md`). `AGENTS.md` and the README are modified in the working tree, and `AGENTS.md` carries the "only the builder and the resolver edit" line the check looks for.
- **Gate record:** `build/round-2.gate.md` ends in "Validation passed". The plugin-directory icon warning in it is not a failure.

## Evidence
$ grep -rn "its builder\|its resolver\|its agent" scripts/board.py tests/test_board.py docs/REFERENCE.md; ls .sdlc/work/149-landing-resolver-agent/build | tail; git status --short | head
```
scripts/board.py:843:            "its agent is resolving a conflict: wait for it, or "
tests/test_board.py:1216:     "its agent is resolving a conflict: wait for it, or /sdlc-factory:land 016 if its session "
tests/test_board.py:1424:        "its agent is resolving a conflict: wait for it, or /sdlc-factory:land 030 if its "
(other matches are unrelated "its agent" uses; no "its builder")
round-2.gate.md
 M docs/REFERENCE.md
 M scripts/board.py
 M tests/test_board.py (and others)
```
exit: 0

$ sed -n 825,850p scripts/board.py; cat .sdlc/work/149-landing-resolver-agent/build/round-2.gate.md | tail -8
```
... ✔ Validation passed
```
exit: 0

$ grep -n "is resolving a conflict\|resolving a conflict" docs/REFERENCE.md; uv run --group dev pytest tests/test_board.py -q -n auto 2>&1 | tail -3; ls .sdlc/work/149-landing-resolver-agent/
```
265 passed, 28 skipped in 19.68s
build checks.md decisions.md intent.md plan.md reviews runs spec.md
```
exit: 0

$ sed -n 575,582p docs/REFERENCE.md; grep -n "^## " .sdlc/work/149-landing-resolver-agent/checks.md
```
...a factory landing whose agent is resolving the conflict says so, its next step to wait for it, or `/sdlc-factory:land NNN` if its session ended.
8:## The docs say the builder and the resolver edit, and the builder no longer resolves
```
exit: 0

$ sed -n 1,40p .sdlc/work/149-landing-resolver-agent/checks.md
```
(check read; not run)
```
exit: 0
