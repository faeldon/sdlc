Confirmed one gap in the cutter: paths after a `:` or `=`, and scp-style remotes, are sent as-is. Writing up the review now.

VERDICT: CHANGES

- CHANGE: scripts/sdlc.py:121: `_PATH_RE`'s `abs` lookbehind leaves out any absolute path that follows a `:`, and no pattern catches an scp-style remote, so both reach the public body as-is and `_cut_host()` marks them safe. I checked it with the real `_cut_host()`:
  - `see foo.py:12:/home/<name>/private/notes.txt` comes back unchanged with `safe=True`.
  - `git@github.com:zenith-corp/secret-proj.git failed` also comes back unchanged with `safe=True`.

  These shapes show up in ordinary failure output: `grep`/compiler `file:line:` prefixes, `PATH`-style lists like `/a:/b` (only the first part is cut), and git's `could not read from remote repository git@host:org/repo.git` for any remote other than the host's own. The skill then tells the person "every path, name and value that would identify the host is cut", which makes them less likely to read the preview closely. The result is a public issue naming a client's org or repo, or a home directory. The person can't delete an issue they filed on someone else's repo.

  The fix:
  - Let `abs` match after `:` too (the drive alternative already handles `C:/`, and `_URL_RE` takes `://` first).
  - Add a pass ahead of the path pass that turns `[\w.+-]+@[\w.-]+:[^\s'"`<>]+` into `<remote>`.
  - Add both shapes, with sentinels, to `test_upstream_body_holds_only_the_allowlist` or `test_upstream_cut_leaves_out_what_it_cannot_make_safe`.

- DECISION: [default] Leave `upstream --send` under the skill's one `Bash(... sdlc.py upstream *)` rule, so nothing but the skill's WAIT stops the model from filing a public issue? Assuming yes.
  - OPTION: keep the one rule — same as `close`'s and `release`'s pushes, which also rely on the WAIT; the skill only runs when the person types `/sdlc:bug`; the key only proves a render happened, not that the person saw it
  - OPTION: grant only `upstream` and `upstream --render`, so Claude Code asks again before `--send` — a second check against prompt injection from session output the skill reads; it needs `test_skills.py`'s "every command has a rule" check to allow an unlisted command, and it asks twice
  - WHY: it matches how the plugin already guards its other outward writes, and the WAIT shows the exact body

## Notes

**Medium**
- scripts/sdlc.py:194: names shorter than 3 characters are never cut (a 2-letter owner, user or repo folder), and names in `UPSTREAM_COMMON` are skipped even when they are the host's real name. The preview is the only guard here. Fix: cut short names when they appear as whole words, since the `(?<![\w-])…(?![\w-])` boundary already keeps them from matching inside other words.
- scripts/sdlc.py:299: a relative path is kept as written when `PLUGIN_DIR / posix` exists. The `..` check only looks at the start, so `scripts/../../x/y` still passes and its text is sent. Fix: keep the path only when `(PLUGIN_DIR / posix).resolve()` stays under `PLUGIN_DIR.resolve()`, or refuse `..` anywhere in it.

**Low / Info**
- `from_host` only checks whether the marker appears anywhere in the body (sdlc.py:7883), so anyone can put the marker in an issue and get `Origin: host` written on the entry triage files from it. That only skews O1's counts, and no security control depends on it. Matching only on the body's first line would be tighter.
- Emails other than git's `user.email` are not cut. The scp-remote fix above catches some of them.
- NIT: scripts/sdlc.py:414: `@name` in the person's words or in the output pings that GitHub user when the issue is filed. Wrap `@` mentions in backticks, or put a zero-width joiner after the `@`, when rendering. {robustness S med}
- NIT: scripts/sdlc.py:7883: match `UPSTREAM_MARKER` only on the body's first line, as R12 describes it. {robustness S low}

**What holds up well**
- The repo comes from the manifest alone, through a fixed `https://github.com/owner/name` pattern.
- `gh` gets an argument list, never a shell. The title always starts with `sdlc: `, so it can't be read as a flag, and the body goes in on stdin.
- No `--label`, `--assignee` or `--milestone` is passed.
- `--send` renders again and refuses a key that no longer matches, so a body can't change between the preview and the send.
- The `sending`/`filed` record is written under `_main_lock()`, so a stopped send isn't filed twice.
- Config values never leave the host, and unknown keys are counted, not named (D2).
- Sections outside the allowlist are dropped and listed in `left_out`.
- The upstream number stays out of `recorded_issues()`.
- Nothing is filed without `gh` or a login.

**What I checked and ran**
- I read the intent, spec, decisions (D1–D4 are open defaults, and I raised none of them again), the diff of `sdlc.py`, `github.py` and both skills, and `_gh()`.
- The gate record `build/round-1.gate.md` is green.
- I ran one read-only script that loads `sdlc.py` and calls `_cut_host()` on the four shapes above.
