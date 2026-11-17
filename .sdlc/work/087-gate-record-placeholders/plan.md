---
id: 087
slug: gate-record-placeholders
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 087 — The factory's gate records hold no machine paths · plan

## Context

`factory.py gate` (`cmd_gate()`) copies the last `GATE_TAIL` (80) lines of the check's output as
they are into `build/round-<N>.gate.md` or `build/land-<n>.gate.md`, files committed with the
change. `claude plugin validate` prints absolute manifest paths on every run and `pytest -n auto`'s
failing worker lines the venv's, so every record carries the machine's checkout and home paths:
into a public history (083 already), and into this repo's next gate, red on `test_nothing_local`
(082, 085, each scrubbed by hand). This fixes bug 2026-11-17-13 at the one place the factory
writes the output.

## Changes

1. **`plugins/factory/scripts/factory.py`**: `_placeholders(text, root)` beside `cmd_gate()`, run
   on `output` before `tail` is built. In order, longest match first, each path as given and
   `.resolve()`d (macOS prints `/private/var/…` for `/var/…`), and in its POSIX form: the main
   checkout's root (first of `_all_checkouts(root)`) as `<path-to-clone>`, so a change's worktree
   reads `<path-to-clone>/.claude/worktrees/NNN-slug/…`; `root` itself, when it lies elsewhere, as
   `<path-to-clone>`; then `Path.home()` as `~`. The record's own lines, the tail's line count and
   its indent are unchanged. `CLONE_MARK` and `HOME_MARK` beside `GATE_TAIL`; the docstring says so.
2. **`tests/test_factory.py`**: `test_the_gate_records_no_path_of_this_machine`, built as the gate
   tests are, with `HOME` set to the tmp root so the checkout sits under home: a gate printing a
   manifest line under `$PWD` and a worker line under `$HOME`, exit 1; asserts neither path, given
   or resolved, is in the record, both placeholders are, and `read_gate()` still reads FAIL, exit 1.
   `gate --land` writes through the same lines, so one test covers both.
3. **Intent's open questions**, struck: history left as it is; agents quoting paths out of scope;
   `test_nothing_local` keeps reading the records.

## Verification

- `uv run --group dev pytest tests/test_factory.py -q -k gate` passes; the new test fails with the
  `_placeholders()` call taken out (checked: 1 failed).
- `./check.sh` passes: 1,877 tests in 39 s.
- Live: the next factory run's gate record in this repo holds no home path, and `test_nothing_local`
  stays green with no hand edit.
