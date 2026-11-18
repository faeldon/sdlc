---
id: 135
slug: factory-records-no-machine-paths
tier: 1
impact: patch
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea: 2026-11-18-22
depends_on:
fixes: [2026-11-18-22]
serves: [O6]
---

# 135 — The factory keeps this machine's paths out of every record it files

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

An agent's reply goes into the change's folder exactly as it came back: `cmd_agent` writes it to
its review, report or verdict file (`plugins/factory/scripts/factory.py:3391`) without the path
replacement the gate and acceptance records already get (`_placeholders()`, used at `:2467` and
`:4201`). When an agent quotes command output that names this machine, such as `git worktree list`
in a behaviour check's `## Evidence`, the home-directory path is committed with the change. The
next gate then fails `test_nothing_in_the_repo_is_forbidden` on a change whose code is fine. On
2026-11-18 this happened three times: 124's landing (`reviews/land-2/behaviour.md:53`, the path to
`node`) and 131's (`reviews/land-1/behaviour.md:42`). 131's landing stopped red on it, and each
one was cleaned up by hand.

There's a second hole in `_placeholders()` itself. It writes the home directory as `HOME_MARK`,
`~`. A path under the home directory but outside the clone, or a clone path that output cut short
(131's `land-2.gate.md` quoted `/Users/<name>/<dir>/s...`), becomes
`~/<dir>/…`. That still matches the test's `~/[\w-]+/` pattern, so even a scrubbed
record can fail the gate.

## Outcome

- Every file the factory writes from an agent's reply (each reviewer's, the verifier's, the
  approver's, the builder's report, a spec draft) has gone through `_placeholders()`. A test
  plants a reply quoting the clone's path and the home directory, and finds `<path-to-clone>` and
  the home mark in the filed file, never the path.
- A path under the home directory, outside the clone or cut short, is filed in a form
  `tests/test_nothing_local.py` accepts. A test feeds such a path through `_placeholders()` and
  checks the result against that test's `PATTERNS`.
- A landing like 131's, whose agent quoted `git worktree list`, passes its gate without a hand
  edit.
- **Moves O6:** fewer factory runs stop on their own records, so a stop means something needs the
  person.

## Affected

- **Area:** the factory's mechanism, `plugins/factory/scripts/factory.py`, and the hand gate's copy
  in `scripts/sdlc.py`.
- **Files & components:** `cmd_agent`'s write of the reply, `_file_draft()` for a spec draft,
  `_placeholders()` and `HOME_MARK`; `sdlc.py`'s `_hand_placeholders()` and `HOME_MARK`, a pinned
  copy (`tests/test_hand_gate.py`); tests in `tests/test_factory.py`.
- **Downstream:** the board and `sdlc.py` read these files (rounds, `decision.md`, `verified.md`)
  through pinned copies of the factory's parsing. A replaced path changes only text inside a
  section, never a `VERDICT:`, `CHANGE:` or `NIT:` line's shape. Depends on nothing open, and
  reworks no earlier change in particular: the replacement was added for gate records and never
  reached replies.
- **Contracts:** `factory.py` never imports `sdlc.py`, so the copies stay copies, pinned by their
  tests; the Windows rules (`newline="\n"` on every write, POSIX forms compared too).

## Constraints

- Never rewrite what an agent concluded: only the machine's paths are replaced, so a reviewer's
  `CHANGE:` line still names the same file, as a repo-relative path.
- Records already committed in history are left as they are.

## Open questions

- What should the home mark be, so it never matches `~/[\w-]+/`: `<home>`, or `~` with no path
  after it? Changing it changes `sdlc.py`'s copy and any record a test pins.
- Should a reply also be checked against `.sdlc/terms.local`, the repo's own forbidden terms, or
  are paths enough?
- Should the agents' prompts also ask for `<path-to-clone>`, or is the script's replacement the
  whole fix?

## Approach

Run every reply `cmd_agent` files, and the spec draft `_file_draft()` writes, through
`_placeholders(text, root)` before it's written. Change `HOME_MARK`, and `sdlc.py`'s pinned copy
with it, to a form `test_nothing_local`'s `PATTERNS` never match, settled while planning, after
reading what the board and the pinned tests compare against. Add the two tests from the Outcome to
`tests/test_factory.py`, a planted reply and a `_placeholders()` result checked against the
`PATTERNS`, and run `tests/test_hand_gate.py` for the copy.
