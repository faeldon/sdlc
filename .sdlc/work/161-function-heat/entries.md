# 161-function-heat — entries

Retire 2026-11-18-102: taken in by 161-function-heat

## [2026-11-18-108] [nit] `heat()` ignores the `--root` blame edge when a file was created after the boundary.

Raised by the code review of 161-function-heat, round 1: `.sdlc/function-heat.py:123`: `heat()` ignores the `--root` blame edge when a file was created after the boundary. A commit that only added the whole file counts as 1, which is correct, but a one-line comment would say so

Theme: docs
Paths: .sdlc/function-heat.py
Cost: S
Value: low
Raised by: 161-function-heat (correctness)
