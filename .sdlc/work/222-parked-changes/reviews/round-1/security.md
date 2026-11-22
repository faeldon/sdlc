I'm asking for one change. When a host's check answers "busy", the gate skips its check that the run left the worktree unchanged, so the check's own code can edit files without anyone seeing.

VERDICT: CHANGES

- CHANGE: plugins/factory/scripts/factory.py:3934: `cmd_gate` returns through `_gate_busy()` (`if busy: return _gate_busy(...)`) before it works out `changed` from `before`/`after`. So a busy run that changes the worktree is never seen. A gate's "Tree: changed → FAIL" rule exists to catch a check, running code the builder wrote, that rewrites the change it is judging. On a host that sets `[park] exit`, that code can now edit files, exit with the park code (for example `os._exit(75)` from a test), and leave the edit behind. The next attempt's `before` already holds the edit, so it reads `Tree: unchanged` and goes green, with `Build:` still the hash of the snapshot taken before the edit. Later rounds' reviewers read only `reworked`, worked out from those snapshots, so an edit on a path the rework didn't touch never reaches a reviewer. On `--land`, the gate goes green on a worktree that differs from the commit that lands. Fix: compute `changed` before the busy branch, and treat a busy answer as busy only when nothing changed (`busy = None if changed else busy`). A busy run that changed the tree then becomes a normal `FAIL` attempt with `Tree: changed: …`. Add a test where a check edits a tracked file and exits with `[park] exit`, asserting a FAIL attempt is written and no `runs/parked.md`.

## Notes

**Trust boundaries reviewed.**
- **What the host's check prints.** This is code the builder wrote, read as `SDLC-BUSY-*` lines.
  - It reaches `runs/parked.md`, `runs/stopped.md`, `verdicts` JSON (which the supervisor and autopilot read), `status` in the terminal, and the board.
  - Each value is joined onto one line, marked by `_placeholders()`/`_defused()` and cut to 200 characters. That stops a value from breaking onto a new line in the record, so it can't fake a `DEADLINE:` or `PROBLEM:` line (the key regexes are anchored per line).
  - Resource and holder are passed to `str.format` as arguments, never as the format string, so there is no format injection.
  - The board builds the text with `textContent`.
- **`runs/parked.md` in the change folder,** which an agent could write.
  - It is vouched before it is written.
  - An unvouched or garbled record is a `rerun` stop, never a wait.
  - The deadline is capped from the base branch's `[park] deadline` in `capped_park()`, whatever the file says.
  - `park --wait` is also bounded by `now + deadline`, so a forged record can't make a run wait (R8).
- **`[park]` config.** It is read only from `_base_factory()`, with a warning when the checkout's copy differs, so a change can't turn parking on for itself or stretch its own deadline.
- **Every waiting state is bounded.**
  - `retry` is capped at the deadline, and the deadline at 1440 minutes.
  - A gate-slot wait is bounded by `SLOT_WAIT`.
  - Autopilot sleeps in 30 s slices and rereads the cancel file and budgets each time, so the loop can't wait forever.
- **A busy landing gate** gives only a `problem`, which stops the train without ejecting it. `landing.py` is untouched.

**Medium and Low findings.**
- Low: `busy_of()` doesn't remove control characters. `" ".join(value.split())` keeps ESC (`\x1b`), so a check can put terminal escape sequences into `status`'s `⏸` line and the `NEXT:` line of `runs/stopped.md`. On most terminals that can only fake or hide the text around it. The fix is to drop C0/C1 control characters in `clean()`.
- Low: `[park] exit` accepts any code from 1 to 255, including `1`. A host that sets it to its check's normal failure code turns every red gate into a park, ended only by the deadline. A warning for `exit = 1`, or a note in the README pointing to 75, would help.
- Info: `park --clear` removes an expired record without checking it is vouched. That is harmless, because it only removes a cause of a stop. `start` and the skill gate it behind the rerun's yes.
- Info: `status` and the board read the park through `factory_records.park()` and don't check it is vouched. They only display it, plus one need past the deadline, and neither decides anything from it, so this is acceptable.

- NIT: plugins/factory/scripts/factory.py:331: `busy_of()`'s `clean()` keeps control characters (ESC and the like), which reach `status` in the terminal; strip C0/C1 before marking {robustness S med}
- NIT: plugins/factory/scripts/factory.py:119: `[park] exit = 1` is accepted, which makes every ordinary red check a park; warn on 1, or document 75 as the only sensible code {docs S low}

**Done well.**
- Vouching comes before the write.
- The deadline is capped on every read, not only when it's written.
- The clock is passed in to `verdicts`, so a reading is the same for the same files and time.
- The landing gate stops the train instead of parking it.
- A slot that times out holds nothing.

**What I checked.** I read the intent, spec, decisions and the gate record (round 1, PASS). I read the diffs of `factory.py`, `run_state.py`, `autopilot.py`, `build/SKILL.md`, `board.py`/`board.html` and `sdlc.py`, and the existing `_tree_hashes()`, `build_hash()`, `_gate_state()`, `_placeholders()` and `_defused()`. I ran no tests. The CHANGE comes from reading `cmd_gate`'s order of steps against `build_hash()`, which hashes the report and the snapshot, not the tree.
