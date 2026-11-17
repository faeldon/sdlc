VERDICT: PASS

No Critical or Required findings. Every requirement from R1 to R16 has code, and the new tests exercise each of them.

## Notes

**Optional**
- `plugins/factory/skills/land/SKILL.md`, lines 108 and 158: `current` and `pass` still say "go to 4". The new step 4 begins "else go to 5", so the flow is correct. The text is easy to misread, and "go to 4 (or 5 when no fix was asked)" would be clearer.
- `plugins/factory/skills/land/SKILL.md`, step 4 says "once", but a `moved` return sends the change back to step 1. After that, it is unclear whether the fix is asked for again. A line saying the fix is not repeated would settle it.
- `cmd_land_fix --commit` does not check that the builder's reply, `build/land-<n>.md`, exists before it amends. The commit is still safe, because it needs an ask and some dirty path outside the folder, but a builder that crashed after a partial edit would be committed without a report.
- `plugins/factory/README.md`: the edited bullet runs well past the file's wrapping width. The `Sdlc-Landed` line and the "land … fix" sentences are both over-long, so reflow them.

**Nit**
- `.sdlc/work/inbox.md` is modified, with both seeds marked `[building]`. This looks like the build's own bookkeeping, but confirm it is meant to ride on the change's branch. AGENTS.md says only `inbox-commit` commits the register, always on the base branch.

**Done well**
- The move is recorded in `runs/land-moves` before `_amend_record()`, so the commit the move was found on carries it. There is no second amend path.
- A race with close is detected by counting the base branch's commits, never by matching close's refusal text.
- `moves` is read from the base branch beside `auto` and `batch`, and the bound is tested both ways. `also` defaults to empty, so 097's amend behaviour is unchanged.
- `unreviewed` goes in the body and in the `Sdlc-Landed` trailer as a count. Its measure path leaves the field out for any change that isn't a landed one with the field.
- The fix signal is checked both at `land` and at `land --close`.

**Ran**
- `pytest -n auto tests/test_land.py tests/test_metrics.py tests/test_skills.py tests/test_factory.py`: 640 passed.
- I did not rerun `./check.sh`. The builder's `build/round-1.gate.md` shows validation passed.
