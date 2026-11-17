VERDICT: PASS

I ran the end-to-end path the spec describes, which feeds replies through `read_evidence()` and `is_read()`. It does what the spec says. No `checks.md` exists for this change, so there was nothing to read there.

## Notes
- **Reads with output:** `cat plan.md` with output and no exit gives no problem. `git -C . show`, `2>&1` and `2>/dev/null | head` are judged reads.
- **Non-reads still need an exit.** `uv run pytest -q | grep passed`, `cd x && ./check.sh`, `cat a >2`, `cat a &`, `env cat a`, `sort -o f a` and `tee f` are judged non-reads. A test run with output and no exit still gives ``has no `exit:` line``.
- **Awk:** `awk '$2 > 0 {print $1}'` is a read.
- **Tests:** the three test files the change touched (`tests/test_factory.py`, `tests/test_land.py`, `tests/test_skills.py`) pass: 649 tests. That covers the new tests for R1–R8, including 119's two replies and the builder's read.
- **Gate:** `build/round-2.gate.md` and `build/land-1.gate.md` exist, and I did not rerun the gate. The `round-2.gate.md` tail shows plugin validation passed, with one icon warning that is not part of the check result.
- **Not run:** the spec's by-hand step, which swaps `$ uv run pytest -q` into R5's fixtures. The tests and my probe cover the same ground.

## Evidence
$ cd /Users/jafaeldon/projects-personal/sdlc/.claude/worktrees/123-evidence-reads; cat .sdlc/work/123-evidence-reads/intent.md; ls .sdlc/work/123-evidence-reads .sdlc/work/123-evidence-reads/build; cat .sdlc/work/123-evidence-reads/checks.md; git diff f182a9dd704363199e1562f2378ff39f24019940...HEAD --stat
(printed the intent, the folder listing and a 37-file diff stat, 1125 insertions and 34 deletions; `checks.md` is absent)
exit: 0

$ cat .sdlc/work/123-evidence-reads/spec.md; cat .sdlc/work/123-evidence-reads/decisions.md; tail -15 .sdlc/work/123-evidence-reads/build/round-2.gate.md; git diff f182a9dd704363199e1562f2378ff39f24019940...HEAD -- plugins/factory/scripts/factory.py
(printed the spec, the decisions, the gate tail showing "Validation passed", and the `factory.py` diff)
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_factory.py tests/test_land.py tests/test_skills.py 2>&1 | tail -4
649 passed in 28.33s
exit: 0

$ uv run python /tmp/p.py 2>&1 | tail -15
cat a 2>&1 True
cat a 2>/dev/null | head True
cat a >2 False
uv run pytest -q | grep passed False
git -C . show HEAD:a True
awk '$2 > 0 {print $1}' f True
cd x && ./check.sh False
cat a & False
env cat a False
sort -o f a False
tee f False
['r: `uv run pytest -q` has no `exit:` line']
exit: 0
