VERDICT: PASS

I found no Critical or Required findings. I walked R1–R13 against the diff and the tests (`tests/test_autopilot.py` +540 lines). I did not run any named tests. The gate record `build/round-1.gate.md` is PASS (`./check.sh`, exit 0).

## Notes
- NIT: plugins/factory/scripts/autopilot.py:`cited_paths`: a directory such as `plugins/` or `docs/` counts as a cited path, so a `fixed` or `wrong` LEAVE can pass on a vague pointer. Require `is_file()`, or a path with more than one segment. {robustness S med}
- NIT: plugins/factory/scripts/autopilot.py:`preview`: with an explicit `--goal`, the alternatives pool is the proposed goal plus the first three alternatives, then cut to three again. A goal that sat among those loses the fourth candidate, so the list can come up one short. {robustness S low}
- NIT: plugins/factory/scripts/autopilot.py:`write_summary`: `## Left for you` prints only `fixed` and `wrong` seeds. `off-goal` seeds appear under `## The plan` ("Off the goal"). That matches R11, but a short pointer in `## Left for you` would help a reader. {docs S low}

Done well:
- The goal is a pure narrowing filter in `candidates()`, and `--begin` re-resolves it from `--goal` rather than re-proposing.
- `read_plan()` collects every refusal reason into one message, which makes the mend round useful.
- The old state shape resumes through `.get`, and the register is only read.
- The path check rejects absolute paths and `..`.
