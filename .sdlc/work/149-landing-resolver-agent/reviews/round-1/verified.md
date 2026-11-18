- KEPT: ux: C1: scripts/board.py:843: the card's `next:` line still says "its builder is resolving a conflict", but the resolver now does that work. The same stale wording is in `tests/test_board.py:1216` and `:1424` and in `docs/REFERENCE.md:579`.

## Notes
I read the code and grepped. I ran no tests. `git diff --stat` shows `board.py` changed in this round, but not at line 843. The string and both test copies still say "builder". `docs/REFERENCE.md:579` says "a factory landing whose builder is resolving the conflict", so it is stale too.
