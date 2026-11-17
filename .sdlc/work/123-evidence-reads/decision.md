DECISION: READY

**Why.** All eight requirements (R1–R8) have code and a test that fails without it. Both reviewers confirmed this in round 1 and again in round 2. Round 2 is all `VERDICT: PASS`: it fixed and added test rows for the three gaps round 1 found and the verifier kept (awk's `system (`, a digit file name after `>`, `>>` or `&>`, and `rg --pre`). The gate passes with 2255 tests. The one decision in `decisions.md` (R1: jq and awk count as reads) was ticked by the person, and the build follows it. Where the build is stricter than the spec, `plan.md` explains it.

**Open items**
- None. No CHANGE is still open after round 2.

**Decisions to confirm**
- None. The only line, R1, is ticked (`person, revise`).

**For the person at ship**
- **Look first at `is_read()` and its helpers in `plugins/factory/scripts/factory.py` (about lines 164–183 and 1040–1170).** This change loosens the factory's guard against claims nobody saw run. The allowlist is the whole risk: anything wrongly judged a read lets a result go unrecorded.
- **`git diff --ext-diff` and `--textconv` are still allowed.** Round 1's code reviewer flagged them as optional, and the build doesn't refuse them. They can run a program the repo's git config sets up, the same kind of gap as `rg --pre`. No later round or note picked this up.
- **Any line after a read counts as its output.** That includes a prose line written after a silent `cmp`. Round 1's test reviewer noted this as within the spec. It means a sentence after a read stands in for its `exit:`.
- **Check the R7 edits in `tests/test_land.py`.** `NO_EXIT` now uses a real non-read (`$ uv run pytest -q`), and 109's three landing tests should still be testing a missing exit.

- IMPACT: patch — factory landings and build rounds no longer stop or ask for a mend when a read that shows its output has no `exit:` line (bug 2026-11-17-90). Nothing new to do, nothing removed; a passing change now finishes on its own instead of by hand.

**Each undone item's disposition**
- UNDONE: `file` is on R1's plain-read list, but `file -C -m <magic>` compiles a magic file and writes `<magic>.mgc`. A later change could give `file` its own condition (no `-C`) the way `sort` has one; left as the spec lists it here. → seed: `is_read()` refuses `file -C`, and git's `--ext-diff`/`--textconv`
- UNDONE: `is_read()` keeps a descriptor digit before a redirection (`2>&1`, `2>/dev/null`) as an argument of its command, since `shlex` drops the spacing that tells `x 2>f` from `x 2 >f`. It never makes a non-read a read (the redirection is judged on its own), but a program condition that counts arguments would see one more. → dropped: no condition in `is_read()` counts arguments today, and the extra token can only make a command a non-read (at most one mend), never the reverse.

**How to recover**
- The prompt names no irreversible paths. `plan.md`'s Rollback (a `git revert`, since nothing is written, published or renamed) matches the files touched.
