VERDICT: PASS

No CHANGE and no DECISION. D1 to D5 and R1 are settled in `decisions.md`, so I have not raised them again.

## Notes

**Read:** the 1280×800 and 390×844 screenshots of `index`; the change's `intent.md` (Tier 1, so no `spec.md` exists and the intent's Approach is the spec); `decisions.md`; `reviews/land-1/ux.md`; `build/land-2.md`; `scripts/board.html` (`.next code`, the card's `needs you:` and `next:` lines, the drawer); `scripts/board.py` (`_progress()`'s stop test, `needs` and `next_action()`); `scripts/sdlc.py` (`FACTORY_STOP_NEEDS`, `needs_of()`, `factory_stop()`); `plugins/factory/scripts/factory.py` (`WAYS`, `WAYS_WHY`, `stop_text()`); the `006` fixture's `stopped.md`; `skills/status/SKILL.md`; and the stop paragraphs in `docs/REFERENCE.md` and `plugins/factory/README.md`.

I have no shell here, so I could not run `git diff a2f79963…HEAD`. I read the changed files as they stand at HEAD and checked each path the spec names against them. I did not check the diff hunk by hand, so for unchanged lines I rely on the test gate that `land-2.md` reports as passing (2309 passed, 13 skipped). I did not treat anything from main's movement as a finding.

**Done, in the screenshots and the code:**
- Card text wraps inside the card at both widths. The `next:` command on 006 breaks at the card edge at 390px, and nothing runs past it.
- The stop's needs-you line now reads `stopped: rerun to ask an agent again`, `stopped: fix its cause and rerun` or `stopped: review an agent's commit`. The word `mend` appears on no card or page, and the `next:` line gives the command to type.
- `status`, the board and the fixture all carry the same `NEXT:` and needs texts, so the card and the `→` line say the same thing.
- `_progress()`'s stop test is parenthesised with the same result.

**States I could not see:**
- *A stop record that won't read:* the needs line and `next:` fall back to `read runs/stopped.md`. That gives the person a file to open, which is acceptable for a file the plugin cannot parse.
- *Loading and empty states:* not touched by this change. The board's empty-column text is outside its scope.
- *A stop recorded before this change:* D4 covers its old wording.

**Smaller findings:**
1. The ship stop says two different things for one act. The needs line says `review an agent's commit` (`FACTORY_STOP_NEEDS`) and the `next:` line says `read the commit, then /sdlc:ship {id}` (`WAYS["ship"]`). Use one verb, `read`, in both. This is the same point `land-1/ux.md` made about `WAYS["ship"]` not saying which commit, which still stands. If the wording fits two lines at 390px, `read the agent's commit` would answer it.

**What the change does well:** it fixed the wrap at its source with `overflow-wrap: anywhere` on `.next code`, and it kept the card, `status` and the record on one set of texts. Those three can't drift apart, and the stop test reads the same as before.
