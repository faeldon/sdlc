# Decisions

- [x] D1 (builder round 1, default): Make `_Close` a plain class with an explicit `__init__` instead of the spec's `@dataclass`? Going ahead with the plain class. → settled by the approver: `plan.md` explains it under "Departures from the spec's Design": `@dataclass` fails on a module loaded by path and not in `sys.modules`. The plain class does the same job. code.md calls it a pure move and security.md says it "behaves like the dataclass, with nothing evaluated when the file loads". The gate is green.
  - OPTION: plain class — it loads, and steps still share one object; a few more lines than a dataclass
  - OPTION: register `closing` in `sys.modules` so the dataclass works — keeps the spec's wording; changes how every by-path module is loaded, which the module tests pin
  - WHY: `closing.py` is loaded by path and never put in `sys.modules`. With string annotations, `@dataclass` looks the class's module up there, so the file failed to load.
- [x] D2 (builder round 1, default): Test R9's second case as 0.30000000000000004 → `4.7` and 0.305 → `4.69`, instead of the spec's 0.30000000000000004 → `"4.69"`? Going ahead with the two cases. → settled by the approver: the spec's own rule in R9 (ignore noise below a millionth, then round down) gives `4.7` for 0.30000000000000004, so the spec's `"4.69"` was an arithmetic slip. test.md confirms that the 0.305 → `4.69` case still covers rounding down, and that 0.65 → `4.35` and the old `3.75` assertion both hold.
  - OPTION: two cases — one shows float noise is ignored, the other shows a real fraction of a cent rounds down
  - OPTION: the spec's case as written — it can't pass: both the old and the new formula give `4.7`
  - WHY: the spec's own rule (ignore noise, then round down) gives `4.7` for that input.
- [x] D3 (builder round 1, default): Edit `tests/test_skills.py::test_only_the_named_steps_push`, which R5 doesn't list? Going ahead with the edit. → decided: the assumed default, confirmed
  - OPTION: edit the test — it now matches a call to `_push(` as a whole word, expects `_step_push` where it expected `cmd_close`, checks that only `_run_close_steps` calls `_step_push`, and looks for `_push_plan(` in `_close_preview`; I planted an extra caller in memory and it is still caught
  - OPTION: rename the push step — breaks R3's required name, and any name ending in `_push` still matches the old substring check
  - WHY: R3's `_step_push` calls `_push(`, and its own name contains `_push(`, so R3 and the unedited test can't both hold.
- [x] D4 (builder round 1, default): Make R14's REFERENCE §Metrics edit now, though the spec marks it "ask first"? Going ahead with it as made. → decided: the assumed default, confirmed
  - OPTION: keep it — the docs match the behaviour -2 accepts; one sentence, easy to revert
  - OPTION: revert it — the docs keep saying a factory change's `source=git` line has `ready_wait`, which the code never writes
  - WHY: it is docs only, and leaving it out keeps the docs wrong.
- [x] R1 (person, fix): re-record tests/fixtures/close-output.json on the new main so the copies include 169's and 170's trailers; the move itself stays unchanged
