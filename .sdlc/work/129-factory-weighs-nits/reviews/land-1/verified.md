No test in the diff puts a nit into a land round, so C1 holds. The code does filter on build rounds (`kind == "round"`), and no test pins that filter.

- KEPT: test: C1: tests/test_factory.py: no test has a `reviews/land-<n>/` round raise a nit, so the build-only filter in `agent_findings()` is unpinned

## Notes
I only read the diff, `agent_findings()` and the tests. I grepped `tests/test_factory.py` and `tests/test_land.py` for land-round nits and found none. I ran no tests.
