Resolved `AGENTS.md`: I kept 173's rewrapped paragraph and added 172's one wording change, with no conflict markers left. I only read the conflict hunk and did not read either spec or diff. I ran no tests, since this is a docs-only edit.

- **From 173:** the "Modules loaded by path" paragraph as rewrapped to the narrower line width.
- **From 172 (HEAD):** the changed wording "the board, close and retro reach `factory_records.py` through their binding". 173's side still said "the board and close", so I applied 172's wording inside 173's wrapping.

I left one over-long line in place: "`factory_records.py` through their binding, as `sdlc.factory_records`. `closing.py` and `landing.py` are apart so". 173's rewrap goal presumably covers it, so it may be worth a look.

## Evidence

$ grep -c '<<<<<<<\|>>>>>>>' AGENTS.md
0
exit: 1
