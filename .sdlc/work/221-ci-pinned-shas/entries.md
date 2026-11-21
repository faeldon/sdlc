# 221-ci-pinned-shas — entries

## [2026-11-22-6] [nit] `USES` only matches `uses:` at the start of a line or after `- `, so a quoted value (`uses: "a/b@v4"`) would slip through unchecked

Raised by the code review of 221-ci-pinned-shas, round 1: tests/test_ci.py:15: `USES` only matches `uses:` at the start of a line or after `- `, so a quoted value (`uses: "a/b@v4"`) would slip through unchecked

Theme: robustness
Paths: tests/test_ci.py
Cost: S
Value: low
Raised by: 221-ci-pinned-shas (correctness)

## [2026-11-22-7] [nit] the workflow glob misses `.github/workflows/*.yaml`, which GitHub also runs, so an unpinned action there would pass the test; glob both extensions

Raised by the security review of 221-ci-pinned-shas, round 1: tests/test_ci.py:52: the workflow glob misses `.github/workflows/*.yaml`, which GitHub also runs, so an unpinned action there would pass the test; glob both extensions

Theme: robustness
Paths: tests/test_ci.py
Cost: S
Value: med
Raised by: 221-ci-pinned-shas (contract)

## [2026-11-22-8] [nit] `VERSION` demands a `v` plus digits, so a comment like `# release-2` would be refused; that is stricter than the outcome's wording but matches the plan

Raised by the test review of 221-ci-pinned-shas, round 1: tests/test_ci.py:16: `VERSION` demands a `v` plus digits, so a comment like `# release-2` would be refused; that is stricter than the outcome's wording but matches the plan

Theme: tests
Paths: tests/test_ci.py
Cost: S
Value: low
Raised by: 221-ci-pinned-shas (correctness)

## [2026-11-22-9] [nit] `USES` still misses a quoted `uses: "a/b@v4"`

Raised by the code review of 221-ci-pinned-shas, round 2: tests/test_ci.py:15: `USES` still misses a quoted `uses: "a/b@v4"`

Theme: robustness
Paths: tests/test_ci.py
Cost: S
Value: low
Raised by: 221-ci-pinned-shas (correctness)

## [2026-11-22-10] [nit] `VERSION` demands `v` plus digits, so a comment like `# release-2` is refused; this is stricter than the outcome's wording but matches the plan

Raised by the test review of 221-ci-pinned-shas, round 2: tests/test_ci.py:16: `VERSION` demands `v` plus digits, so a comment like `# release-2` is refused; this is stricter than the outcome's wording but matches the plan

Theme: tests
Paths: tests/test_ci.py
Cost: S
Value: low
Raised by: 221-ci-pinned-shas (correctness)
