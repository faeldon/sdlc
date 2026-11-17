---
id: 087
slug: gate-record-placeholders
tier: 1
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on:
fixes: [2026-11-17-13]
reworks: [073]
serves: [O2]
---

# 087 — The factory's gate records hold no machine paths

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`factory.py gate` (`cmd_gate()`, `plugins/factory/scripts/factory.py:1249-1302`) copies the last
`GATE_TAIL` lines of the gate's output, as they are, into `build/round-<N>.gate.md` (and
`build/land-<n>.gate.md` for a landing), a file committed with the change. Two of the gate's own
tools print absolute paths: `claude plugin validate`'s "Validating marketplace manifest: /…" and
"Plugin directory checks for /…" lines on every run, and under `pytest -n auto`, now this repo's
gate (082), each failing test's xdist worker line with the venv's path. So every record carries the
machine's home directory and the checkout's path into a change folder bound for a public repo, and
`tests/test_nothing_local.py`'s scan, which reads the untracked folder (082), fails the next gate
on the record itself.

On 2026-11-17: 082's builder edited its record by hand (decision D3), and the code reviewer found
attempt 1's lines still there; 085's record had to be scrubbed by hand at 085's ship (lines 43,
45, 61, 63); and 083's records reached `main` with the path, in `a17dd91` and `90d71b9`. In a host
running the factory the same happens with that host's paths, which no `test_nothing_local` of
theirs catches.

## Outcome

- **Moves O2:** a host running the factory never has its machine's layout written into its history
  by the factory itself.
- `cmd_gate()` writes the checkout's root as `<path-to-clone>` and the home directory as `~` in the
  tail before recording it, in both the round and the landing records. A test runs a fake gate
  printing both paths (as `claude plugin validate` and an xdist worker line do) and fails if either
  reaches the file; a second covers a checkout under the home directory, the root replaced first, so
  it reads `<path-to-clone>`, never `~/…`.
- A record's `Verdict:`, `Build:`, `Exit:` and attempt lines are unchanged, so `_factory_files()`'s
  `gate_fail` count and `verdicts`' gate state read every record, old and new, as before.
- The next factory run's gate records in this repo pass `test_nothing_local` with no hand edit.
- `./check.sh` passes.

## Affected

- **Area:** the factory's script gate.
- **Files & components:** `plugins/factory/scripts/factory.py` (`cmd_gate()`'s tail),
  `tests/test_factory.py`.
- **Downstream:** every factory run's gate records, here and in hosts; `/sdlc-factory:land`'s
  `gate --land` records; the builder, which reads a red record to fix the gate (it sees placeholders,
  and should still be able to follow them); close's `measure`, which counts the records' verdicts
  only.
- **Contracts:** *Nothing about a project or a workspace* (`tests/test_nothing_local.py`), which this
  makes the factory keep; *the scripts run on Windows* (the root and home matched as the OS prints
  them, both forms on Windows); the factory never imports `sdlc.py`.

## Constraints

- Only the copied output changes; the record's own lines and their parsing don't.
- No other absolute path in the output is touched: nothing outside the root and home is guessed at.
- The tail keeps its line count, so a red gate's useful output isn't cut shorter.

## Open questions

- ~~The history already holding paths (083's records on `main`): leave it, or rewrite it? Rewriting
  public history is its own decision, outside this change; say which in the notes.~~ Resolved:
  left as it is; this change stops new ones, and rewriting `main`'s public history is its own call.
- ~~Agents quote gate output in their own replies (082's builder report did; a reviewer may): is
  that the agents' prompts' job ("never quote a path outside the checkout"), or out of scope
  here?~~ Resolved: out of scope; the record they quote from now holds placeholders, and a prompt
  rule is a seed of its own if wanted.
- ~~Does `test_nothing_local` keep reading the factory's records? Once they're scrubbed it can, and
  it should, since they ship.~~ Resolved: yes, unchanged; it's what proves the fix holds.

## Approach

In `cmd_gate()`, before building `tail`, replace `str(root)` (and its `as_posix()` form) with
`<path-to-clone>`, then `str(Path.home())` with `~`, in `output`. Test with a fake check command
printing both kinds of line, in a scratch repo built as `tests/test_factory.py`'s gate tests are.
