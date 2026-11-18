# 153-risky-code-in-its-own-modules — entries

## [2026-11-18-104] [nit] the spec's `test_the_source_guards_reach_closing_py` plants all four cases (main ref, `gh` call, literal `work/`, second push).

Raised by the test review of 153-risky-code-in-its-own-modules, round 1: tests/test_sdlc.py:1921: the spec's `test_the_source_guards_reach_closing_py` plants all four cases (main ref, `gh` call, literal `work/`, second push). It plants only two, and the other two live in `test_work_folder.py` and presumably `test_skills.py`.

Theme: tests
Paths: tests/test_sdlc.py
Cost: S
Value: low
Raised by: 153-risky-code-in-its-own-modules (correctness)
