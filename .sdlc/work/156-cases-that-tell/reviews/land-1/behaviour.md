VERDICT: PASS

The change does what the spec says, as far as I could run it without paid model calls. I ran the new tests and read the new commands' help output, but I did not run `claude plugin eval` itself because each run is a paid call.

## Notes

- **`checks.md`, "The docs say how the cases rerun, class the sandbox and land":** I expect it to pass. I ran each grep on its own and every pattern matched (`reruns alone, once`, the environment line, `test_no_grader_insists_on_a_tool`, `cases <NNN> --skip <why>`, the AGENTS.md rule, and `cases --skip` in the factory README). The negated pattern, `keeps each run's folder and trace`, matched 0 times, so `! grep -q` holds.
- **End-to-end path:** the new `factory.py cases --skip WHY` and `sdlc.py run-cases [--full] [--keep]` both exist and print the documented help.
- **Not run:** a real `run-cases` or the landing flow, which spend money. The tests that fake the eval calls cover those paths, and all 905 passed.

## Evidence

$ grep -c <each of the 7 check patterns, one grep per pattern>
1
1
1
1
0
1
2
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_evals.py tests/test_land.py tests/test_skills.py tests/test_factory.py
905 passed in 40.52s
exit: 0

$ uv run --quiet --script scripts/sdlc.py run-cases --help
usage: sdlc.py run-cases [-h] [--full] [--keep] [id]
exit: 0

$ uv run --quiet --script plugins/factory/scripts/factory.py cases --help
usage: factory.py cases [-h] [--skip WHY] id
exit: 0
