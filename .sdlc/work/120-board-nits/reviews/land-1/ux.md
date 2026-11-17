VERDICT: PASS

I reviewed the change from its current text and the two landing-round screenshots. I could not run `git diff` (this session has no shell), so I did not check the full diff line by line. I read the UI paths directly and the strings they produce, and I'm relying on the test gate for the rest.

No CHANGE and no DECISION. Every decision in `decisions.md` is settled, and I have not re-raised any of them.

## Notes

**Read:** both 1280×800 and 390×844 screenshots of `index`; `intent.md` (the change is Tier 1, so there is no `spec.md`; I used the intent's Approach and Outcome); `decisions.md` (D1–D5, R1); `build/land-1.md`; `scripts/board.html` (`.next code` rule and the card's `needs you:` and `next:` lines); `scripts/board.py` (`_progress()`'s stop test); `scripts/sdlc.py` (`FACTORY_STOP_NEEDS` and `needs_of()`); `plugins/factory/scripts/factory.py` (`WAYS`, `WAYS_WHY`, `stop_text()`); the `006` fixture's `stopped.md`; `status`'s `SKILL.md`; and the stop paragraphs in `docs/REFERENCE.md` and `plugins/factory/README.md`.

**Done in the screenshots and the code:**
- Card text wraps inside the card at both widths. The long `next:` commands on 006 and 003 break at the card edge, and nothing runs past it at 390px.
- The needs-you line for a stop now reads `stopped: rerun to ask an agent again`. The word `mend` appears on no card, and the `next:` line gives the command to type.
- The needs-you line is text, not colour alone, so it reads the same without the red.
- `status` and the board use the same `needs_of()` texts, so the card and the `→` line say the same thing.

**States I could not see:**
- *A stop record that won't read.* The needs-you and next lines fall back to `read runs/stopped.md`. That gives the person a file to open, not a command, which is acceptable for a file the plugin cannot parse.
- *Loading and empty states.* Neither is touched by this change. The board's empty-column behaviour is outside its scope.
- *A stop recorded before this change.* D4 covers its old wording.

**Smaller findings:**
1. `WAYS["ship"]` says `read the commit, then /sdlc:ship {id}`, which does not say which commit or where to look. The drawer's longer sentence explains that an agent committed, but the card line alone leaves the person to find it. Consider `read the agent's commit, then /sdlc:ship {id}`, if it still fits two lines at 390px.
2. The `stopped:` label for a `rerun` way is `fix its cause and rerun`, and its `next:` line adds the command. The two are consistent, so no change is needed.
3. The 390px screenshot's `next:` on card 006 wraps to three lines. D5 settled this; I mention it only so the builder knows I saw it.

**What the change does well:** it fixed the wrap at the source (`overflow-wrap: anywhere` on `.next code`) and kept the stop test's result while parenthesising it. It also made the stop's short `NEXT:` line the same text on the card, in `status` and in the record, so the three can't drift apart.
