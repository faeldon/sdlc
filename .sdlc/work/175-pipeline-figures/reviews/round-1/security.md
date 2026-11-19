VERDICT: PASS

## Notes

No security problem in this change is exploitable. Nothing at Critical, High or Medium.

**Trust boundaries the diff touches**
- **Run records → `retro`.** The new `pipeline_counts()` reads files a run committed into the change's folder: the gate files, `land-train.md`, `land-accept.md`, `ejections.jsonl`, `land-times.jsonl`, `conflicts.md` and `step.md`. It reads them at the change's own commit through `_records_at()`, which calls git with a list of arguments (`git show <sha>:<folder>/<rel>`, `git ls-tree`). No shell runs. `rel` is always a module constant or a path that `ls-tree` returned, and the code only uses that path after `gate_kind()` accepts it. The data goes into numbers and JSON only: nothing is run, evaluated or turned into HTML. STRIDE:
  - **Tampering:** a change's own branch could fake its figures. The result is only a wrong number in a read-only report, and no gate decision uses these figures. Low.
  - **Denial of service:** see the regexes below.
- **Regexes.** All the new patterns are anchored, and none has nested quantifiers that overlap: `WAITED_RE`, `DEPTH_RE`, `TRAIN_GATE_RE`. The `_none_reason()` fix `(\s+[^\s=]+=\S*)+$` needs whitespace between groups, and the key can't contain `=`. So each word splits only one way, and the old risk of slow backtracking on hand-written `Sdlc-Coverage` values is gone. This is a fix, not a new risk.
- **`step.md`'s `DEPTH:` line.** `step_text()` writes it only when `out["depth"]` is exactly `full` or `light`. The script's `depth()` sets that value, not any model output, and the reader's regex accepts only those two words. Nothing new can be injected through it.
- **Gate records' `Waited:`.** Both writers (`factory.py` and `sdlc.py` `cmd_gate`) take `waited` from `gate_slot()`'s monotonic timer, which is a float the script controls. Neither writes it from outside input.
- **`unreviewed`.** This change only counts the existing `Sdlc-Landed unreviewed=` field. A missing value is counted as missing, never as `none` (D1), so the report never says more was reviewed than any record shows. I agree with D1 from the security side.

**Other checks**
- **Secrets:** none in the code, the test fixtures or the change's artifacts.
- **Dependencies:** no new ones.
- **Destructive operations:** none. `retro` writes nothing new, and the only `landing.py` edit moves the `LAND_TRAIN` constant into `factory.py`.
- **`--metrics`:** without it, `cmd_retro` drops the per-change `pipeline.changes` list, the same way it treats `cost` and `spend`.

**What I checked:** I read `intent.md`, `decisions.md` and the full diff under `scripts/` and `plugins/`. I grepped to confirm `waited` comes from the slot context in both gate writers, that `CONFLICTS` is defined in both `sdlc.py` and `factory_records.py`, and how `_records_at()` builds its git calls. I didn't rerun the gate: `build/round-1.gate.md` records `./check.sh` passing (`GATE: PASS`, exit 0).

**Done well:** an absent `Waited:` or `DEPTH:` line reads as None, never 0. That keeps the figures honest, which matters for the unreviewed-landings count, the one figure here that is about risk.
