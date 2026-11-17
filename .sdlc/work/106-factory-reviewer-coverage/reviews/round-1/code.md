VERDICT: PASS

## Notes

I found nothing Critical or Required. `./check.sh` is green: ruff and the formatter are clean, 2006 tests pass, and `claude plugin validate --strict` passes. I walked R1–R14 against the diff and the new tests.

**Optional**
- `plugins/factory/scripts/factory.py`, `_fixture_copy`: the copy is replaced before the server starts. If a server from an earlier crashed shot is still running, it keeps writing into the old copy. I think that is acceptable, since `_stop` kills the process group in a `finally`.
- `factory.py`, `cmd_start`: the new `light` line comes after the "Each role's model…" comment, so the comment now sits above the wrong statement. Move the `light` line above that comment.
- The spec says `serve.sh` builds in `<dir>`, and the plan's "As built" notes `<fixture>/drafts`. The `serve.sh` header says this too. Nothing to fix; the deviation is documented.

**Decisions**
- D1–D3 in `decisions.md` are all `[default]` and unanswered. I reviewed against the defaults the builder took, and I agree with all three:
  - D1: the two existing light tests move to Tier 1.
  - D2: a `[light] reviewers` with no known reviewer is not treated as set.
  - D3: a single-file fixture is copied under its own name.

**Done well**
- `light_reviewers()` is one small function, and `depth()` uses it for both the expected reviewers and the "beyond" test, so R6 holds without a special case.
- `_inside()` rejects absolute paths, drive anchors, and `..` on any platform.
- `_fixture_copy()` handles Windows read-only git objects.
- With no fixture set, `shots()` behaves exactly as before.
- The board fixture's `build.sh` refuses an existing target, and `gates` is data, not code.

**Ran**
- `./check.sh` in full.
- I did not run `serve.sh` by hand with Playwright, so the rendered cards are unverified by me.
