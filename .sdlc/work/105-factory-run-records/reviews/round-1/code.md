VERDICT: PASS

I found no Critical or Required findings. I read the spec, plan, diff and tests, and `./check.sh` is green.

## Notes

**Requirement coverage.** Each requirement has code and a named test.
- **R1–R3:** `split_draft`, `_file_draft`, `agent --task spec` and `cmd_write_spec` match the spec. The fence tracker follows CommonMark: a fence closes only on the same character, at least as long, and with nothing after the marker. `write-spec` byte-copies with `shutil.copyfile`, refuses all three cases at once, and writes nothing on refusal.
- **R5–R7:** `_supersede_refusal` covers all five cases, and its order of checks is sound. Marking happens only for a new line, so a rerun is idempotent because the text is already known. The `open` and `decided` split reaches `loop_state`, `land_signals`, `cmd_decisions` and `_task("decided")`, which refuses a superseded D2 because `decided` is false for it. Ticking with a suffix keeps all three `LEDGER_RE` copies untouched, as the design says.
- **R10–R11:** `factory_first_build` never raises, and its time window and step check match R10. It hides only the plan-template problem, for `plan.md` at `stage: build`.
- **R4 and R9:** the build and spec skills, `builder.md`, the reviewer agents, `approver.md`, ship's `factory.md` and the README are all updated.

**Optional**
- `write-spec` copies whatever `runs/spec-draft.md` holds. If a later `agent --task spec` fails (`problem`), the old draft stays on disk, and the skill must not show it as new. Step 1 reads `to` only after a successful run, so this is fine today. A line in the skill saying "on `problem`, show nothing and stop" would make it explicit.
- When the reply has no frontmatter but does hold a question separator, `split_draft` treats that `---` as the frontmatter's opening. The spec names this edge and the supervisor's scaffold check catches it, so no change is needed.

**Nits**
- `.sdlc/work/inbox.md` is in the diff: the three seeds became `[building]`. That is expected bookkeeping, but the register is normally committed through `inbox-commit`. Check it doesn't ride on the change's branch, since AGENTS.md wants entries kept off a change's branch.

**Done well**
- Ticking a superseded line leaves the board's and metrics' readers correct with no code change. R8's two tests pin this rather than asserting new behaviour.
- The scaffold rule is copied rather than imported, and pinned by a test. `factory.py` still never imports `sdlc.py`.

**Ran:** `./check.sh` (ruff, format, full pytest, `claude plugin validate --strict`) passed. The factory plugin validation shows only an ICON_MISSING warning, which doesn't change the result. I did not run the by-hand scratch-repo check from the spec's Verification section.
