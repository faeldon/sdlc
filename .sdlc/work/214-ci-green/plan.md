---
id: 214
slug: ci-green
kind: plan
created: 2026-11-21
updated: 2026-11-21
---

# 214 — CI on main passes again on Linux and Windows · plan

> How 214 is built: the files it changes, the order of its slices, the tests that prove each
> outcome, and what a revert would not undo. Written after reading the code and the CI logs of run
> 44894639869 (`Close 210-wait-previews`), whose six failures match every red run since 9b21760.

## Causes, from the logs

| Failure | Job | Cause | Where the fix goes |
|---|---|---|---|
| `test_check_leaves_out_the_template_plan_during_a_live_upgraded_build`, `test_a_live_first_build_hides_no_other_problem` | Windows | The **test** copies `templates/spec.md` with `write_text(...)` and no `encoding`, so Windows writes its `—` as cp1252 `0x97`; `is_unfilled()` reads UTF-8 correctly. No script bug. | the two tests; `test_windows.py` widened so a portable test can't do it again |
| `test_the_build_hash_moves_on_a_rebase_onto_a_moved_base` | Windows | **Script bug a host hits.** GitHub's Windows runners set `core.autocrlf=true`; checking the branch out again rewrites `src/app.py` as CRLF, and `_hand_digests()` hashes the bytes on disk, so the hand gate's build moves on a mere checkout. Any Windows host with `autocrlf` sees its green gate go stale. | `sdlc.py` and `factory.py`'s copy: hash each path as git would store it (`git hash-object --stdin-paths`, which applies the checkout's filters) |
| `test_the_builder_s_evidence_is_mended_once_a_round` | Windows | The test runs the `claude` fixture, a shebang script Windows can't execute, so `cmd_agent` fails to start it. No other portable test runs the fake. | the test: stand in for `factory._claude` itself, so it stays portable |
| `test_upstream_repo_comes_from_the_manifest` | Windows | Same shape: the `gh` fixture's shebang fake can't run, so the runner's real `gh` answers, and it isn't logged in. | the test: stand in for the GitHub tracker's `gh` calls, the login injected |
| `test_a_server_that_answered_and_closed_first_has_not_lost_its_port` | Linux | **Not a race; a script bug on Linux.** Linux refuses a bind over a TIME_WAIT left by a socket that didn't set `SO_REUSEADDR`, even when the prober sets it (macOS allows it), so `_binds()` reads a port only TIME_WAIT holds as taken and `_lost()` says lost. Reproduced in a `python:3.12-slim` container; `/proc/net/tcp` shows the port held by state `06` alone. | `factory.py`: `_lost()` doesn't call a port lost when on Linux only TIME_WAIT entries hold it |

The open questions, answered: `test_windows.py` scans only the scripts, and the bad write was in a
test, so the check widens to the body of every test marked `portable` (all 275 unencoded calls
across the suite would be a cleanup of its own; a portable test is the one that runs on Windows).
The hand-gate failure is a line-ending bug in the code; the mend failure is the test's. Whether a
landing should say CI is red goes to `notes.md` as a seed, not this change.

## Files to change

- `scripts/sdlc.py`: `_hand_digests()` hashes through `git hash-object --stdin-paths`; a path git
  can't take on a line (one holding a newline) keeps the sha256 of its bytes. `_SCP_RE` matches a
  host with no dot (nit 2026-11-21-21).
- `plugins/factory/scripts/factory.py`: the same `_hand_digests()` copy; `_lost()` and a new
  `_only_time_wait()` reading `/proc/net/tcp` and `tcp6` on Linux; `_binds()`'s docstring
  corrected.
- `tests/test_windows.py`: `test_every_portable_test_names_its_encoding`.
- `tests/test_sdlc.py`, `tests/test_readiness.py`, `tests/test_factory_agent.py`: the unencoded
  calls in portable tests; the mend test without the fake binary.
- `tests/test_upstream.py`: a `_logged_in()` helper instead of the `gh` fixture in R1's test; an
  undotted scp remote case.
- `tests/test_hand_gate.py`: the hash survives a CRLF checkout (`core.autocrlf=true`).
- `tests/test_factory_ui.py`: `_only_time_wait()` read from fixture tables.
- `docs/REFERENCE.md`: the hand gate's `Build:` is over each path as git stores it, so a
  line-ending checkout keeps a record current.
- `.github/workflows/check.yml`: the unverified claim about setup-uv's cache token goes (nit
  2026-11-21-23). Sensitive path: comment only.

Reused: `_git()`'s shape for the subprocess (`encoding="utf-8"`), `_hand_hash()` unchanged, the
existing pin `test_the_factorys_hand_build_is_sdlcs`.

## Work order

1. **Encoding.** Red: the new `test_windows.py` check lists the six unencoded calls in portable
   tests (and, on its first run, three `os.open` calls, which take flags; the check passes over
   `os.open` as `_unlf_writes()` does). Green: name `encoding="utf-8"` on each.
2. **Hand-gate hash.** Red: a hand-gate test that sets `core.autocrlf=true` and checks the branch
   out again sees the hash move (reproduces on macOS, since `autocrlf=true` converts everywhere).
   Green: `hash-object` in both copies; the factory pin holds.
3. **Mend test.** Swap the fake binary for a `_claude` stand-in. Red: the old test with the fake
   made non-executable (Windows' case) fails; green: the new one passes with no `claude` on PATH.
4. **Upstream test.** `_logged_in()`; red is the test with `gh` hidden from `PATH` (as on a machine
   without the fake), green with the stand-in. Then the nit: an undotted host case, red then green.
5. **Port.** Red: `_only_time_wait()` against fixture tables, and the existing test run in a Linux
   container. Green: the function and `_lost()`; the container run passes.
6. **check.yml comment** (nit 23).

## Tests

- `test_every_portable_test_names_its_encoding`: no portable test reads or writes text in the
  locale's encoding (the 0x97 failures).
- `test_the_build_hash_survives_a_crlf_checkout`: the hand gate's build doesn't move when git
  rewrites line endings (the hand-gate failure).
- `test_the_builder_s_evidence_is_mended_once_a_round`: unchanged in what it proves; runs on Windows.
- `test_upstream_repo_comes_from_the_manifest`: unchanged in what it proves; no machine login.
- `test_upstream_cut_places_a_path_after_a_colon_and_an_scp_remote`: plus `git@localhost:x/y`.
- `test_only_time_wait_reads_the_proc_tables`: TIME_WAIT alone is not held; a LISTEN or a bound
  socket is; no entry is not "only TIME_WAIT".
- `test_a_server_that_answered_and_closed_first_has_not_lost_its_port`: passes on Linux.
- The landing's CI run on both jobs is the outcome's proof (intent's Outcome 1).

## Rollback

`git revert` undoes everything. Nothing is written or published. One effect outlives a revert
either way: a hand-gate record written before this change names a build hashed the old way, so an
existing green hand gate reads stale once and wants `sdlc.py gate` rerun (and after a revert, the
same for one written under this change).
