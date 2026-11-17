VERDICT: PASS

No Critical or Required findings. I checked each of R1–R18 against the code and the tests, and none is missing.

## Notes

- **Optional, README:** the rewritten `/sdlc-factory:land` bullet has one line well over 100 columns ("the nits its intent or spec names by id retired, committed, brought up to date…"). Re-wrap it for consistency with the file.
- **Optional, `_amend_record()`:** it only reads `git log -1 %B` for `Sdlc-Landed:` when something is dirty, which matches R4. The "`HEAD` isn't the landing's commit" guard fires only on dirty state, so a clean `HEAD` that isn't the landing's commit passes through unchecked. That is harmless, because nothing is amended.
- **Checked, not a defect:** `resolve --continue` writes `land-<land_round()>`. A round of 0 would read as a pre-change marker and always signal. `cmd_land` creates `reviews/land-<n+1>/` on `rebased` and `conflict` (line 2549) before `resolve` runs, so the round is at least 1 in practice.
- **Done well:**
  - `settled` is a narrow, documented parameter. The pass stands when the landing's own record moves `HEAD`, and `land-verdicts` output is unchanged.
  - `cmd_land_close` reads the `by=auto` trailer before `_amend_record()` moves `HEAD`, so the R15 guard sits in the script, not only in the skill.
  - The nit register edit happens only after `ship` succeeds.
  - The factory still never imports `sdlc.py`.
  - The new subprocess call names `encoding="utf-8"`, and the new `write_text` passes `newline="\n"`.
- **Ran:** `uv run --group dev pytest -q -n auto` passed (2008 tests). `ruff check` and `ruff format --check` were clean.
- **Not run:** `claude plugin validate` and the paid skill cases. If `preflight` puts the land skill's cases in scope, the person decides whether to pay for a run.
