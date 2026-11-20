VERDICT: PASS

## Notes

**Trust boundary.** The resolver is a model with `Bash`. It runs mid-rebase and leaves behind the worktree and the index. Untrusted input from the conflicted files (other changes' text) can steer it. What it leaves reaches `git rebase --continue` and then the base branch. This change narrows that path from "anything staged passes" to "only staged paths that `REBASE_HEAD` owns, plus conflicted, moved and record files". STRIDE threats on that path:
- **Tampering:** a stray staged edit or deletion now fails closed.
- **Spoofing:** a stale `REBASE_HEAD` after the rebase has finished can't be used, because `_rebasing()` is checked before any read.
- **Elevation:** the prompt is no longer the only control.

**Findings (none Critical or High):**

- **Medium, the known limit, carried over from before.** A resolver can stage different text for a path `REBASE_HEAD` owns that did not conflict, and it passes. The spec names this under "Known limit". It is not a regression: before this change any staged path passed. The fix the spec rejected, comparing each owned path against `git merge-tree`'s replay, is the real close. The intent says "see the open questions", but no open question records it, so it should be filed as a seed so it isn't lost.
- **Medium [correctness], fails closed, not a security issue.** Suppose `HEAD` renamed `a`→`b` and `REBASE_HEAD` modified `a`. merge-ort replays the edit cleanly into `b`, and `b` is staged by the replay itself. `b` is not in `REBASE_HEAD`'s `diff-tree` listing, not unmerged and not in `moved`, so the fence refuses a legitimate resolution. A rename-following conflict at `b` is refused the same way once the resolver's work leaves it staged. This stops the train for the person and lets nothing through, so it is safe, but the correctness pass should weigh it. One fix is to add the rename targets from `git diff --cached -M HEAD` whose source `REBASE_HEAD` owns.
- **Low.** `_z_listing` decodes with `encoding="utf-8"` but without `errors=`. A path that isn't valid UTF-8 raises `UnicodeDecodeError`, which nothing catches, so the run dies with a traceback before anything is staged. That fails closed, but it is untidy; catching `UnicodeDecodeError` and returning `None` gives the normal refusal.
- **Low, existed before this change.** `files` (`factory._conflicted`) and `deleted_sides()` read the index's unmerged stages as the resolver left them. A resolver could forge unmerged entries with `git update-index --index-info` so that an arbitrary path counts as conflicted or moved, and the fence would let it through. This is exotic, and the supervisor's HEAD check doesn't cover it. Snapshotting `_conflicted()` and `deleted_sides()` before the resolver runs, in `train-resolve`, and comparing at `--continue` would close it.
- **Info.** A resolver `git commit` that moves `HEAD` would hide changes from the `HEAD`-relative `_staged()`. `agents/resolver.md` says the supervisor checks `HEAD` after the run and stops on a commit, so this is covered outside this function.

**What I checked:**
- The `landing.py` diff:
  - `_replayed`/`_staged` read through `subprocess.run` with an argument list, `-z`, `encoding="utf-8"`, and no shell. A `None` result refuses rather than passing.
  - The no-rebase guard comes before every read.
  - Both reads happen before any `git add`.
  - `allowed` is built from git's own `-z` output and from `as_posix()` records.
  - A deletion of an unowned path now falls to the fence, and a deletion of a path `REBASE_HEAD` keeps still falls to `deletable`.
- `_rebasing()` reads `rebase-merge/` and `rebase-apply/`, never `REBASE_HEAD`.
- `_conflicted()` and `deleted_sides()` in `factory.py`.
- `agents/resolver.md`: tools, and its "never commits" rule.
- The `REVIEW.md` bullet is under Pass 1 and contains no secrets.
- No new dependencies, no destructive operations added, and the refusal leaves the rebase under way, so it can be undone.
- The gate record `build/round-1.gate.md` shows PASS (exit 0). I ran no tests; the gate covered them.

**Done well:** the change fails closed on every path where git can't be read. The stale-`REBASE_HEAD` guard closes the exact class of bug this change names. The refusal's undo text now covers a staged change as well as a worktree edit.
