VERDICT: PASS

The end-to-end path does what the spec says. In a scratch host, `upstream` reported the manifest's repo, and `--render` cut host specifics and listed the extra input section in `left_out`. `--send` refused a key that didn't match the render.

## Notes
- **`checks.md`, "The docs say what filing upstream does":** I expect it to pass. I grepped for each of its strings in the docs and found each one (counts 1, 2, 1, 1, 1, 1), so its `grep -q` chain would exit 0.
- **`decisions.md`:** D1–D4 are the builder's defaults and are still unanswered. None of them is a failure, so I raised nothing against them.
- **Not run:**
  - A real `--send` to `faeldon/sdlc`. It files a public issue.
  - The no-`gh` path. `gh` was present and logged in here, and the targeted tests cover that path.
- **Gate:** `round-1.gate.md` shows `GATE: PASS`, and I did not run the whole suite again. The 17 upstream-related tests I ran passed.

## Evidence
$ cat .sdlc/work/209-upstream-bugs/build/round-1.gate.md | head -5
GATE: PASS

## Attempt 1

Verdict: PASS
exit: 0

$ (scratch host with a private remote, a git user and email, and an input file holding sentinels) uv run --quiet --script scripts/sdlc.py upstream
{"available": true, "own_repo": false, "repo": "faeldon/sdlc", "login": "altcoder", "new_issue_url": "https://github.com/faeldon/sdlc/issues/new", ...}
exit: 0

$ uv run --quiet --script scripts/sdlc.py upstream --render
title "sdlc: close fails in /<owner>"; body starts `<!-- sdlc:host-bug:12a8a1b286f0 -->`; the paths and the email are cut to `<path>` and `<email>`; the Diagnostics block shows versions and `Config keys set: commands.check, git.base`, with no values; `left_out: ["Secrets"]`; the password text is absent.
exit: 0

$ uv run --quiet --script scripts/sdlc.py upstream --send --key deadbeef
{"refusals": ["the bug renders as 12a8a1b286f0, not deadbeef: render it again and show it first"]}
exit: 1

$ uv run --group dev pytest -q -k "upstream or intake_flags or bug_asks or bug_shows or github_file_issue"
17 passed, 3705 deselected in 42.33s
exit: 0

$ grep -c 'sdlc.py upstream' docs/REFERENCE.md; grep -c 'sdlc:host-bug:' docs/REFERENCE.md; grep -c 'a bug in the plugin itself goes to the plugin' README.md; grep -c 'by `upstream` (`upstream_tracker()`)' AGENTS.md; grep -c UPSTREAM_INPUT AGENTS.md; grep -c '^- \*\*`upstream bug`\*\*' docs/FEATURES.md
1
2
1
1
1
1
exit: 0
