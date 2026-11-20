VERDICT: PASS

This change has no spec, so I ran the Approach's three outcomes through the change's own tests and one direct check of the key-reader scan. All three outcomes hold.

- **Workarounds `unknown` block:** `_workarounds()` now gives `unknown` an `n`, in the same loop as `outside` and `hand_record`.
- **Lead time by way:** a way with no change now gets the `no <way> change in the window` reason. It uses the same `_no_way()` helper as the escape rate.
- **Config keys in the surface:**
  - `git.base` and `git.push` now have `sdlc.py` commands as readers. The scan returned `base`, `board`, `bugs`, `cases` and more for both keys, so they count as used whenever those commands ran.
  - A key whose every reader runs where no record shows it is `unmeasured` (`read only where no record shows it`), never `unused`, and the retire list skips it.
  - All config keys have at least one reader on this repo.
- **Docs:** `docs/REFERENCE.md` is updated to match.

I did not run the new `unknown` count, the lead-by-way note, or the key states on a real window of closed changes. They are covered only by the tests and the reader scan above.

## Notes
`checks.md` does not exist for this change, so there were no acceptance checks to read.

## Evidence
$ head -8 .sdlc/work/204-scorecard-reads-true/build/round-1.gate.md
GATE: PASS

## Attempt 1

Verdict: PASS
Command: ./check.sh
Build: 844f3c06533949c6
Exit: 0
(a read of the gate record, which owes no `exit:`)

$ git diff d09b19c013c5193e927514af7475adbdf22bc3c1...HEAD -- scripts/retro.py docs/REFERENCE.md
(the diff, as read above)
exit: 0

$ uv run --group dev pytest tests/test_surface.py tests/test_retro.py -q -n auto
310 passed in 35.22s
exit: 0

$ uv run --quiet python -c "<load retro.py and sdlc.py by path, print _key_readers(False) for git.base and git.push, count keys with no reader>"
git.base [('command', 'sdlc.py:base'), ('command', 'sdlc.py:board'), ('command', 'sdlc.py:bugs'), ('command', 'sdlc.py:cases')]
git.push [('command', 'sdlc.py:base'), ('command', 'sdlc.py:board'), ('command', 'sdlc.py:bugs'), ('command', 'sdlc.py:cases')]
0 keys with no reader
exit: 0
