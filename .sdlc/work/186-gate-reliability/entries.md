# 186-gate-reliability — entries

## [2026-11-19-75] [idea] test_train's by() should share _uv()'s offline fallback

Left undone by 186-gate-reliability, carried forward when it landed: `tests/test_train.py`'s `by()` runs `uv run --script` on a copy of the plugin at a new path, as the adoption tests did, so a gate with no network can fail it the same way. It could share the adoption tests' `_uv()` (offline from uv's cache, else a skip naming the network).
See .sdlc/work/186-gate-reliability/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-76] [nit] `"network was disabled" in cached.stderr` depends on uv's exact wording.

Raised by the code review of 186-gate-reliability, round 1: tests/test_adoption.py:65: `"network was disabled" in cached.stderr` depends on uv's exact wording. If a later uv words it differently, an offline run with an empty cache returns the failing result instead of skipping, so the gate goes red on the network again. Matching "offline" or "disabled" as well, or checking `--offline`'s non-zero exit more loosely, would be sturdier.

Theme: robustness
Paths: tests/test_adoption.py
Cost: S
Value: med
Raised by: 186-gate-reliability (correctness)

## [2026-11-19-77] [nit] `test_with_the_index_unreachable_a_copy_of_the_script_runs_from_uvs_cache` passes on the old code too.

Raised by the code review of 186-gate-reliability, round 1: tests/test_adoption.py:529: `test_with_the_index_unreachable_a_copy_of_the_script_runs_from_uvs_cache` passes on the old code too. It only fails once uv's cached index answers are stale, as the builder says. It shows the fallback works but isn't a regression guard.

Theme: tests
Paths: tests/test_adoption.py
Cost: M
Value: low
Raised by: 186-gate-reliability (correctness)

## [2026-11-19-78] [nit] the builder's note is right that it also runs `uv run --script` and could share `_uv()`.

Raised by the code review of 186-gate-reliability, round 1: tests/test_train.py: the builder's note is right that it also runs `uv run --script` and could share `_uv()`. Filed as a follow-up.

Theme: refactor
Paths: tests/test_train.py
Cost: M
Value: med
Raised by: 186-gate-reliability (correctness)
