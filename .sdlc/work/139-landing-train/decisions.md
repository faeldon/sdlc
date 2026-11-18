# Decisions

- [x] D1 (builder round 1, default): The `train-resolve` prompt names each change's spec and diff (`git show <sha>:…/spec.md`, `git show <sha>`) for the builder to read, rather than inlining n specs and diffs. Going ahead unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: name them — a short prompt whatever the batch size; the builder reads what it needs with Bash
  - OPTION: inline them — nothing to run, but five specs and diffs can be most of a prompt
  - WHY: R3 says the prompt "holds" them and its test "names" them; naming satisfies both readings and keeps the cost bounded
- [x] D2 (builder round 1, default): `eject` is a step of its own in `runs/land-step.md` (R18), its `- PROBLEM:` line reading `ejected from the train: <reason>` with the gate file; the board shows it as a stop. Going ahead unless told otherwise. → settled by the approver: R18 lists `eject` as one of the new steps in `runs/land-step.md` and asks the board to show it as a stop. The build does exactly that: `LAND_STEPS` gains `stack` and `eject`, the board shows `eject` as a stop, and `test_a_train_member_shows_its_place_and_an_ejection` pins it. The record's problem line carries R7's `ejected from the train: <reason>`, so R7's "records a stop" is met in substance.
  - OPTION: a step `eject` — the record says what happened; the board's stop handling covers it
  - OPTION: `STEP: stop` with `AFTER: eject` — R7's literal "records a stop", but `eject` is not a position on the track
  - WHY: R18 lists `eject` among the steps and asks the board to show it as a stop
