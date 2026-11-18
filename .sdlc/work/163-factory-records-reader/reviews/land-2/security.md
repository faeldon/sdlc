VERDICT: PASS

## Notes

This round moves two parsers from `scripts/closing.py` into `scripts/factory_records.py` without changing what they do. I found no Critical or High issue, and nothing new to report at Medium or Low.

**Where untrusted data enters, and what I checked:**
- **The run files:** `runs/costs.jsonl` and `runs/land-times.jsonl` are written by agents' runs, so I treated them as untrusted.
  - `timed_rows`, `land_sinces`, `_json_rows` and `_run_time` moved with the same bodies. Each line goes through `json.loads`, and a line that doesn't parse is skipped.
  - Only dict rows are kept. Times are parsed with a fixed `strptime` format, and a `TypeError` or `ValueError` gives None.
  - The role is turned into text with `str()` and used only as a label. Nothing parsed reaches a shell, `eval`, a path or a template.
- **The git reads in `_lead_marks`:** they stay in `closing.py` and still run through `sdlc._git` with an argument list, never a shell.
  - The paths are now built from `branch`, `folder` and the module's fixed constants (`LAND_TIMES`, `COSTS`, with `.as_posix()`). They were literal strings before. Same inputs, same reach, and nothing from a record goes back into git.
- **`measure_change`:** its `cat-file -e` now builds the path from `DECISION_FILE` (`"decision.md"`), the same value as before.
- **Module purity:** `factory_records.py` still has no subprocess call and no import of `sdlc.py`. No dependency was added.
- **Destructive operations:** none added. The module writes nothing.

**Settled:** everything in round 1's security review. The rework touched none of it, and I didn't reopen it.

**What I checked:**
- The full `scripts/closing.py` diff from `972430a`.
- The moved functions and constants in `factory_records.py` (lines 43, 115–116 and 641–678).
- The builder's report in `build/land-2.md`.
- The gate record `build/land-2.gate.md`: `GATE: PASS`, `./check.sh` exited 0, tree unchanged. I didn't run the gate myself.

**What's done well:** close keeps its git access, and `factory_records.py` keeps all the parsing. As a result, every file name for agent-written records is spelled in one module, and the R5 boundary test now enforces that.
