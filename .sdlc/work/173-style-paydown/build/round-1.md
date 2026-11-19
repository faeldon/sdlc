All the style nits in this change are now cleared, and the full gate passes: 3065 passed, 28 skipped. Nothing is committed. The only lines changed apart from rewrapping are two comments, and in the four markdown files every word is the same and in the same order as in `HEAD`.

**What changed**
- **`.github/workflows/check.yml`** (-75, -77, -78): the 166-column header line is rewrapped. No CI step changed.
- **`AGENTS.md`** (-83, 2026-11-19-5): the *Modules loaded by path*, *The board* and *The factory* paragraphs are rewrapped, and the short lines earlier edits left in them are filled. I also wrapped one 101-column bullet line so the file has no line past 100.
- **`plugins/factory/README.md`** (-82, -96, 2026-11-19-10): every prose line past 100 is rewrapped, and the paragraph on what `factory.py` does, which was full of short lines, is filled. Table rows and fenced blocks stay as they are, because a markdown table row can't wrap.
- **`reviewer-code.md` and `reviewer-ux.md`** (-81): the "Under a decision's line" paragraph, the round-file sentence and the nit-weights paragraph are rewrapped.
- **`check.sh`** (-76): the comment over the pytest step now says the `skipped` count is expected and that `pytest -rs` names each reason. Running `tests/test_board.py -rs` showed the 28 skips come from that file's pairs of board states that can't overlap, not from the browser tests. The browser tests only add to the count on a machine without Chromium.
- **`.sdlc/function-heat.py`** (-108): a two-line comment over `heat()`'s blame call says a file added after the boundary has no boundary lines, so the commit that added it counts as one.

**Change files**
- **`plan.md`**: written, though this is a Tier 1 change, because the Approach touches seven files. The build follows it.
- **`checks.md`**: three checks — no prose line past 100 in the named files, `check.sh`'s skip note, and `heat()`'s comment. All three exit 0.
- **`notes.md`**: three items left open. The other nine factory agent files still have lines past 100, but no entry named them. The README's table and fenced lines can only be shortened by rewording. A few short lines remain in `AGENTS.md` paragraphs that no nit named.

No new tests: nothing behaves differently, and `checks.md` proves the outcome. The full gate shows the rewrap broke none of the tests that look for exact text in these files.

- UNTESTABLE: none

- DECISION: [default] Keep the agents' frontmatter `description:` lines on one line, though idea -81 names them. Going ahead unless told otherwise.
  - OPTION: one line — matches every core and factory agent and skill, and keeps the YAML simple; those lines stay past 100
  - OPTION: wrap as a multi-line YAML value — meets -81 literally; no other agent in the repo does this, and it risks how Claude Code reads the description
  - WHY: no behaviour may change, and a frontmatter value the harness reads differs from a prose rewrap

## Evidence

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 173
All checks passed!
3065 passed, 28 skipped in 160.89s (0:02:40)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --quiet --group dev pytest -q tests/test_function_heat.py
7 passed in 12.69s
exit: 0

$ uv run --quiet --group dev pytest -q -rs tests/test_board.py
SKIPPED [1] tests/test_board.py:1410: gate owed and factory building set different stages
SKIPPED [1] tests/test_board.py:1410: approver decided and factory building set different stages
283 passed, 28 skipped in 58.36s
exit: 0

$ uv run --quiet --group dev pytest -q -rs tests/test_board_browser.py
2 passed in 7.69s
exit: 0

$ for f in AGENTS.md plugins/factory/README.md plugins/factory/agents/reviewer-code.md plugins/factory/agents/reviewer-ux.md; do a=$(git show HEAD:$f | tr -s ' \n' '  ' ); b=$(tr -s ' \n' '  ' < $f); [ "$a" = "$b" ] && echo "same words: $f" || echo "DIFFERS: $f"; done
same words: AGENTS.md
same words: plugins/factory/README.md
same words: plugins/factory/agents/reviewer-code.md
same words: plugins/factory/agents/reviewer-ux.md
exit: 0

$ sh -c "<checks.md's first block>" && echo check1-ok; grep -q 'pytest -rs` names each reason' check.sh && grep -q 'skipped` count is expected' check.sh && echo c2; grep -q 'A file added after `since` has no boundary lines' .sdlc/function-heat.py && echo c3
check1-ok
c2
c3
exit: 0

$ uv run --quiet --script scripts/sdlc.py check
■ Problems: 0
    none ✅
exit: 0
