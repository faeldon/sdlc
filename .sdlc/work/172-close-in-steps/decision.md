DECISION: ESCALATE

**Why.** All four round-1 reviewers passed: code, security, test and behaviour. The gate is green (`./check.sh`, 3075 passed). The code and security reviewers compared the moved close code line by line with the old `cmd_close` and found it unchanged: same git commands, same order, same lock span. Each of R1–R9 has a test that fails without its fix. Two defaults still need the person. D4 is a REFERENCE.md edit the spec marks "ask first". D3 edits the test that enforces the push rule, in `tests/`, which the spec's R5 says fails review.

**Open items**
- None. No CHANGE is open in any round-1 review. Three nits are on record in `findings.md`:
  - F1 (code): the return annotation on `_close_steps`.
  - F2 (code): a leftover `lines = []` in `_step_measure`.
  - F3 (security): say in the docstring that `measure.errors` must never become a trailer.

**Decisions to confirm**
- SETTLED: D1: `plan.md` explains it under "Departures from the spec's Design": `@dataclass` fails on a module loaded by path and not in `sys.modules`. The plain class does the same job. code.md calls it a pure move and security.md says it "behaves like the dataclass, with nothing evaluated when the file loads". The gate is green.
- SETTLED: D2: the spec's own rule in R9 (ignore noise below a millionth, then round down) gives `4.7` for 0.30000000000000004, so the spec's `"4.69"` was an arithmetic slip. test.md confirms that the 0.305 → `4.69` case still covers rounding down, and that 0.65 → `4.35` and the old `3.75` assertion both hold.
- ESCALATED: D3: this default rewrites `test_only_the_named_steps_push`, the test that enforces the rule in AGENTS.md that only the named steps push. A default about that rule is policy, which is the person's to decide. It also goes against R5's line "A diff of `tests/` showing other edits fails review". security.md found the rewrite stricter: it matches whole words, the allowed callers are exactly `{cmd_publish, _step_push, cmd_release}`, and only `_run_close_steps` may call `_step_push`. It also leaves AGENTS.md's sentence that `_push` is called "by `cmd_close`" true only through `_step_push`.
- ESCALATED: D4: the spec says R14 is "ask first", and that is the person's call. `docs/REFERENCE.md` is the contract hosts read, so the builder's default can't stand in for their yes. The edit is one sentence, and it makes the docs match what the code writes.

**For the person at ship**
- Start with `_run_close_steps` in `scripts/closing.py`. Check that the lock is taken before the first step, let go after `remove folder` (or after `record` for a drop) and before `tell_issues`, and that the exit-3 and handoff-after-merge paths are still there.
- Then the rewritten `tests/test_skills.py::test_only_the_named_steps_push` (D3).
- Then the one changed sentence in `docs/REFERENCE.md` §Metrics (D4).
- `tests/fixtures/close-output.json` is untracked in the worktree, so make sure ship commits it. code.md also notes that the commit history can't show the characterization test passing on the old code before the move. The only evidence for that is the builder's report ("5 passed" on the old code), since this run lands everything as one commit.
- When this repo closes the change, the report should show `"ran": "merged code"` and exit 0.

- IMPACT: patch — close behaves the same. The cost ceiling no longer loses a cent, the docs now match the code, and the report gains a `measure.errors` key only when timing the lead time fails.

There are no `UNDONE` lines: `notes.md` doesn't exist, and the builder reports nothing left over. There are no `RECOVER` lines because the prompt names no irreversible paths. `plan.md`'s Rollback is a `git revert` of the change's commit.
