VERDICT: PASS

I checked the whole branch diff against main at f02c571 (the build the land-2 gate passed on). The end-to-end paths behave as the intent's Outcome says: the port-0 board, the live reload, and the rebasing card. I found no CHANGE.

- **`board --port 0`** printed the port it bound (63915 in the run), and the page and `/state.json` answered on that port.
- **Live reload:** a scratch copy of `scripts/` served an edited `board.py` on the next request, with the new key present. A broken copy kept the last good code and set `reload_error`, which says the file won't load and the board serves the code it had.
- **Rebasing card:** a scratch change stopped on a conflict keeps its card with `rebasing: true`, and its next step is `sdlc.py resolve 101 --continue` or `--abort`. Git's worktree, HEAD and rebase record are identical before and after the read.

## Notes

- **Checks:** there is no `checks.md` in this change's folder, so there are no acceptance checks to read or expect.
- **Gate:** `build/land-2.gate.md` is green on build f02c571, which matches HEAD. I did not run the gate.
- **Read only, not run:** the precedence table in `next_action()` (rebasing, then missing stage, then problems, then closed) matches `plan.md`'s table as I read it. `_progress()` reads `decision.md` only at `test`, `shipped` or `dropped`, as `column()` does. I did not run `tests/test_board.py` again, because the gate already ran the full suite on this build.
- **Not a CHANGE, for the person:** the branch's diff against main edits `.sdlc/work/inbox.md`. It removes entries 22, 23, 30 and 47 and adds seeds 52–58 on this branch, which AGENTS.md says should never ride a change's branch: `inbox-commit` writes the register on the base branch. This is a process question for ship and the landing, not a board behaviour, so I have left it out of the verdict.
- **Not run:** the `checks.md` path (none exists), and the full pytest suite (the gate covers it).

## Evidence

$ git merge-base HEAD main; git rev-parse main
6ae08346b8de32329cf5ee85ea278afe2a9fc653
6ae08346b8de32329cf5ee85ea278afe2a9fc653
exit: 0

$ git diff --stat main...HEAD  (tail)
 scripts/sdlc.py                                    |  11 +-
 tests/test_board.py                                | 199 ++++++++++++++++++++-
 42 files changed, 1243 insertions(+), 64 deletions(-)
exit: 0

$ git diff main -- scripts/sdlc.py scripts/board.py scripts/board.html docs/REFERENCE.md  (read in full; key hunks: `_Live`, `route()`, `next_action()` rebasing branch, `_progress()` stage gate, `cmd_board()` port read-back, `change_dirs()` via `_change_trees()`)
exit: 0

$ uv run --quiet --script "$PWD"/scripts/sdlc.py board --port 0   (worktree code, background; port read from output)
{
  "url": "http://127.0.0.1:63915/",
  "serving": true
}
exit: 0

$ curl -s -H "Host: 127.0.0.1:63915" http://127.0.0.1:63915/state.json | python3 -c '...'
board: sdlc keys: ['at', 'board', 'changes', 'repo', 'trunk']
[('098', 'shipped', False, None), ('099', 'test', False, None), ... ('107', 'design', False, None)]
page 200
exit: 0

$ cp -R scripts "$SCR/scripts"; uv run --quiet --script "$SCR/scripts/sdlc.py" board --port 0   (scratch copy; port 63925)
{
  "url": "http://127.0.0.1:63925/",
  "serving": true
}
before edit keys: ['at', 'board', 'changes', 'repo', 'trunk']
exit: 0

$ python3 (edit scratch copy's board.py: add "reviewer_probe" key to state()); curl state.json
after edit: edited-on-disk reload_error: None
exit: 0

$ printf 'def broken(:\n' >> "$SCR/scripts/board.py"; curl state.json
after break: probe: edited-on-disk | reload_error: board.py changed but won't load (SyntaxError: invalid syntax (board.py, line 822)): the board serves the code it had until the file loads
changes served: 9
exit: 0

$ bash: git init; printf base; commit; branch 101-demo with conflicting commit; main commit; git worktree add "$SCR/wt-101" 101-demo; git rebase main
rebase exit: 1
CONFLICT (content): Merge conflict in shared.txt
error: could not apply 18725a3... branch work
(worktree wt-101: detached; head-name: refs/heads/101-demo)
exit: 1 (rebase, expected: stopped mid-rebase)

$ before=$(git status / head-name / HEAD | shasum) ; uv run --quiet --script "$WT/scripts/sdlc.py" board --port 0  (scratch repo, port 64014)
before: c120b501e8a9dcaa56566d4ee4d3f957718a427f  -
{ "url": "http://127.0.0.1:64014/", "serving": true }
exit: 0

$ curl -s -H "Host: 127.0.0.1:64014" http://127.0.0.1:64014/state.json | (card 101)
{'id': '101', 'slug': 'demo', 'stage': 'test', 'rebasing': True, 'column': 'needs-you', 'next': 'a rebase is stopped in its worktree: resolve its conflicts, then sdlc.py resolve 101 --continue, or sdlc.py resolve 101 --abort', 'problems': ['missing created:', 'missing updated:']}
exit: 0

$ after=$(git status / head-name / HEAD | shasum)  (same commands as before)
after: c120b501e8a9dcaa56566d4ee4d3f957718a427f  -
exit: 0

$ git diff main -- .sdlc/work/inbox.md | grep -E "^[+-]## "  (read only)
exit: 0

$ pgrep -fl "sdlc.py board --port 0" || echo "no board servers running"
no board servers running
exit: 0
