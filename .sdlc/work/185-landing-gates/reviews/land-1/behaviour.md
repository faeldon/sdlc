VERDICT: PASS

The change does what the spec says. The 20 selected train tests for acceptance checks and `commands.build` pass, and I found no failing path.

## Notes
- **`## The docs state the landing's new gates`** (the only check in `checks.md`): I read it and did not run it. I expect it to pass.
  - The `grep` for the old wording ("The loop runs neither." or "harness asks before every run") finds nothing in `AGENTS.md` or `plugins/factory`. That `grep` exits 1, so the leading `!` makes the first clause true.
  - A looser search, without the trailing period, does match `SKILL.md:165`. That is the new text "The loop runs neither before a commit. After it, …", not the old rule.
  - `` `[commands] build` for `gate --land --build` `` appears once in `AGENTS.md`, and so does `checks_clearance()`.
  - `land-checks` appears once in the land `SKILL.md`, and `gate --land --build` once in the factory `README.md`.
- I did not run the whole suite. The round-2 gate record shows `GATE: PASS`.
- I ran no spec-level end-to-end `train --run`. The closest path I ran was the change's own train tests: the 20 selected with `-k "checks or build"`, which include the clearance and `gate --land --build` cases.

## Evidence
$ head -3 .sdlc/work/185-landing-gates/build/round-2.gate.md
```
GATE: PASS

## Attempt 1
```
exit: 0

$ grep -rnI "The loop runs neither\.\|harness asks before every run" AGENTS.md plugins/factory
```
(no output)
exit: 1

$ grep -c '`\[commands\] build` for `gate --land --build`' AGENTS.md; grep -c "checks_clearance()" AGENTS.md; grep -c land-checks plugins/factory/skills/land/SKILL.md; grep -c "gate --land --build" plugins/factory/README.md
```
1
1
1
1
```
exit: 0

$ uv run --group dev pytest tests/test_train.py -q -n auto -k "checks or build"
```
....................                                                     [100%]
20 passed in 20.48s
```
exit: 0
