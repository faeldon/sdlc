# 140-agent-replies-that-file-right — entries

## [2026-11-18-47] [idea] Reword `_no_verdict()` and `NO_DECISION` now that an answer after prose is read

Left undone by 140-agent-replies-that-file-right, carried forward when it landed: `_no_verdict()` and `NO_DECISION` still say "doesn't open with VERDICT…/DECISION…", which the spec kept so the board's and status's problem text doesn't move. Since `opening()` now reads an answer after prose, the words now mean "holds no answer the script reads". A rewording would change the board's and status's text together, and their pins with it.
See .sdlc/work/140-agent-replies-that-file-right/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-48] [nit] `replies[-1]` is a safe fallback only because `_claude()` guarantees a non-empty list when it returns no problem.

Raised by the code review of 140-agent-replies-that-file-right, round 1: plugins/factory/scripts/factory.py:3840: `replies[-1]` is a safe fallback only because `_claude()` guarantees a non-empty list when it returns no problem. A one-line comment saying so would help.

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 140-agent-replies-that-file-right (correctness)
