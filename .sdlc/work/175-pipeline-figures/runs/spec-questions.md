
**Revised as asked:** the line `Nits taken in: 2026-11-19-19, 2026-11-19-21` now opens the
Requirements section, so the landing retires both nits. R13 and R14 still say what each fix is.
Nothing else in the draft changed.

**Resolved**
- *Are the train's figures read from the change's records at its `Close` commit's parent, or
  written as a trailer when it closes?* They're read from the records at the change's own
  commit, the `Close` commit's parent (`_records_at()`, as `_autonomy()` and `_cost()` read
  them). No trailer is needed: everything the train's state held is copied into
  `ejections.jsonl`, `land-train.md`, `land-step.md`'s `MOVES:` and the landing gate files.
- *Do the gate files record the slot wait today?* No. `gate_slot()` yields `waited`, and both
  `cmd_gate()`s print it but don't write it. This change adds a `Waited:` line to both writers
  (R3).
- *Mends per change.* These are already in `autonomy.spurious_stops`, so they aren't repeated
  (R12).
- *Full-depth share.* No record holds depth today. This change adds a `DEPTH:` line to
  `runs/step.md` (R6), and older runs are missing.

**Left for the person**
- **Two factory record lines.** The intent lists only core files under *Affected*, but slot wait
  and depth have no record. This spec adds `Waited:` and `DEPTH:` to `factory.py`'s records,
  plus `Waited:` to `sdlc.py gate`. The alternative is to leave both figures out (in
  `unmeasured`) and report the rest.
- **Landings from before `unreviewed=` existed.** `metrics.py`'s contract says a landing without
  `unreviewed=` has none, so the spec counts it in `none`. That contract can't tell "none" from
  "before the field". Treating it as missing would need a cut-off the records don't give.
- **The plan confirms from history** that `runs/step.md`, `land-step.md`, `land-train.md` and
  `build/land-accept.md` are committed with a factory change. Any that isn't makes its figure
  missing for every change.
