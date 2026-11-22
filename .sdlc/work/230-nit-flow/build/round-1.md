I've rerun everything my claims rest on, with a real exit after each command. Every requirement of 230 is built and the work is uncommitted. One gap remains: my second full `check 230` run was stopped at the background time limit, about 88% through, before it printed a result. So no full run of mine has finished green. The factory's gate will be the first.

What was built is unchanged from my last report:
- **Filing (R1–R3, R5, R6):** a role's nits are filed from its last build round only. A nit a later round doesn't raise again is not filed, and its findings.md section says why. A `low`-value nit is never filed.
- **Asking again (R4):** each reviewer is named the nits it raised in its last round, with their weights, through a new `## earlier` prompt part.
- **Core's reader (R9):** `sdlc.py` has its own copy of the factory's `Nits taken in:` reader, pinned against it by a test.
- **Retiring (R7, R8):** a nit can be retired as `duplicate`, `stale` or `wontfix`, unless an open change takes it in.
- **Skill and docs (R10, R11):** `/sdlc:idea`, `docs/REFERENCE.md`, the factory README and the code comments are updated.

All the new and reweighed tests are in the 889-test run below. They also include the fix for the earlier full-run failure: two tests took a `capsys` argument they never used, and `test_suite_shape.py` now passes. Ruff is clean. The old refusal text, the README's "at most five a change" and the replaced test are gone. `landing.py`, `guide/` and `defaults/` have no diff.

**plan.md:** written before the code and followed. The only departure from the spec is naming core's copy of `_section()` `_nit_section()`, which plan.md states.

**notes.md:** nothing left there.

- DECISION: [default] Name core's copy of the factory's `_section()` `_nit_section()`? Going ahead with it unless told otherwise.
  - OPTION: `_nit_section()` — no clash with core's existing `_section()`, which ignores case and skips code fences; the R9 test pins that both readers agree
  - OPTION: change core's `_section()` to the factory's shape — one name, but it changes what core's other callers get back
  - WHY: R9 asks for an exact copy, and core's `_section()` behaves differently
- DECISION: [default] Word the new `earlier` review part as "Nits you raised in round ${before}: ${nits}; raise again, word for word with its weights, any that are still true." Going ahead with it unless told otherwise.
  - OPTION: name the round (`before nits`) — the reviewer knows which of its replies the nits came from
  - OPTION: `nits` alone — one placeholder, as the spec's "its placeholder" reads
  - WHY: after a restart, the earlier round isn't the one just before, so it is worth saying

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q -n auto tests/test_factory_loop.py tests/test_bugs.py tests/test_skills.py tests/test_land.py tests/test_modules.py tests/test_prompts.py tests/test_nits.py tests/test_feature_map.py tests/test_suite_shape.py
889 passed in 95.71s (0:01:35)
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 230
........................................................................ [ 88%]
[killed: stopped at the background time limit before it finished]
exit: 137

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
348 files already formatted
exit: 0

$ grep -rn "is a nit: ship retires nits" scripts tests
exit: 1

$ grep -n "at most five a change" plugins/factory/README.md
exit: 1

$ grep -n "def test_a_nit_not_raised_again_is_still_filed" tests/test_factory_loop.py
exit: 1

$ git diff --stat -- plugins/factory/scripts/landing.py guide defaults
exit: 0
