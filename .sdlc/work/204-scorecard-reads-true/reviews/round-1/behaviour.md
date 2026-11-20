VERDICT: PASS

I found no failures. The three outcomes hold in code and tests. I ran the live `retro` once, and the scorecard and surface come out as the spec says.

## Notes
- **Workarounds `unknown` block:** `_workarounds()` now builds it with `n` and `missing_because` in the same loop as `outside` and `hand_record`. The `scripts/retro.py` diff shows this, and `tests/test_retro.py` covers it. The live `retro` output has no `workarounds` key under `process`, so I couldn't read the block there.
- **Lead rows by way:** a way with no change in the window now gets `no <way> change in the window` from `_no_way()`, the same helper the escape rate uses. The live output shows that reason on the escape rate for `manual` and `unknown`. My search of the scorecard's lead rows found nothing, so I confirmed those rows by reading the diff and the passing tests, not from live output.
- **Surface retire list:** `_key_readers()` scans the scripts' `@command` functions with `ast` and reads skill files for `section.key` names. `git.base` has 36 command readers and 10 skill readers; `git.push` has the same commands and 7 skills. The live retire list holds 8 commands and no config keys at all, where the seed named 33 keys.
- **Window with no recorded commands:** in the current window, `git.base` shows `unused` with 0 uses, even though its readers are found. Its one change recorded no commands, so `config`, `close` and `new` also show `unused`. The window recorded no commands rather than the scan missing the keys, and earlier windows count `git.base` as used, which keeps it off the retire list. This is no fault of the change.
- **Tests:** `uv run --group dev pytest tests/test_retro.py tests/test_surface.py -q -n auto` gives 303 passed. The gate record `build/round-1.gate.md` reads `GATE: PASS`.
- **checks.md:** the change has none, so there is nothing to read.

## Evidence
$ cat .sdlc/work/204-scorecard-reads-true/build/round-1.gate.md | head -5
GATE: PASS

## Attempt 1

Verdict: PASS
exit: 0

$ git diff $(git merge-base HEAD main) -- scripts
(diff of scripts/retro.py, read: `_no_way`, `_code_reads`, `_key_readers`, `unknown` gets `n`)
exit: 0

$ uv run --quiet --script scripts/sdlc.py retro > /tmp/r.json
exit: 0

$ python3 (parse /tmp/r.json: surface.retire, git.base and git.push items, escape-rate reasons)
retire: {"after": 3, "windows": 7, "items": [8 command items, no key]}
git.push: used (uses 1); git.base: unused (uses 0, current window)
the escape rate's `manual` and `unknown` blocks show "no <way> change in the window"
exit: 0

$ uv run --group dev python /tmp/p.py   (`_key_readers(True)` for git.base and git.push)
both list 36 `sdlc.py` commands and the skills named above
exit: 0

$ uv run --group dev pytest tests/test_retro.py tests/test_surface.py -q -n auto
303 passed in 87.23s
exit: 0
