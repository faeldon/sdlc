The factory's spec-writer is now told to put every nit it takes in on a `Nits taken in:` line. A test fails if either place stops saying so. The work is uncommitted, and I ran only the named tests below, not the full suite; the gate runs that.

**What changed:**
- **`plugins/factory/agents/spec-writer.md`** has a new "Nits taken in" bullet under *How to write it*. It uses the wording from `skills/spec/SKILL.md`: each nit taken becomes a requirement and its id goes on the Requirements section's `Nits taken in: <id>, <id>` line. An id written anywhere else is never taken in. It also follows the intent's constraint: take in only the nits the intent or the person names, never one unasked.
- **`plugins/factory/prompts/spec.md`**: the `draft` part (still one line) now says the same thing in short.
- **`tests/test_skills.py`**: I added both files to 181's `test_every_place_that_takes_a_nit_in_names_the_marker`. I ran it before the wording went in, and it failed on both files as expected; it passes now.
- **`tests/prompts/spec.txt` and `spec-upgraded.txt`**: re-recorded with `SDLC_RECORD_PROMPTS=1`, because the draft line comes first in both prompts. The only difference in each is the new sentence.
- **`intent.md`**: I struck through the open question and wrote the answer under it (see the decision below).
- How `factory.py` reads the marker is unchanged.

There is no `plan.md`. Your prompt asked for one, but `intent.md` says Tier 1 and this is a wording change to two files plus a test, which is under the threshold for one. There is no `checks.md` either: the test covers the requirement, and nothing went into `notes.md`.

- UNTESTABLE: none

- DECISION: [default] Should the spec prompt only say how to write the nits the intent names, without handing the spec-writer a list of open nits on the change's paths? Going ahead with "only those the intent names" unless told otherwise.
  - OPTION: only those the intent names — matches the constraint "never takes a nit in unasked", and needs no new script code; the spec-writer doesn't see other nits on the same paths
  - OPTION: hand it the open nits on the change's paths, as `sdlc.py nits --touching` gives the core skill — the same offer `/sdlc:spec` makes; needs `factory.py` to run it and add it to the prompt, which the intent rules out ("wording only")
  - WHY: the intent's Constraints ("Wording only", "only those the intent's Problem or the person names"), and the spec-writer can only read files, not run commands

## Evidence

$ uv run --group dev pytest -q tests/test_skills.py::test_every_place_that_takes_a_nit_in_names_the_marker   (before the wording)
FAILED tests/test_skills.py::test_every_place_that_takes_a_nit_in_names_the_marker
1 failed in 0.71s
exit: 1

$ SDLC_RECORD_PROMPTS=1 uv run --group dev pytest -q tests/test_prompts.py -k "spec"
4 passed, 56 deselected in 0.20s
exit: 0

$ uv run --group dev pytest -q tests/test_prompts.py
60 passed in 2.67s
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py -k "nit or agent or spec_writer"
21 passed, 398 deselected in 0.12s
exit: 0

$ uv run --group dev ruff check tests/test_skills.py && uv run --group dev ruff format --check tests/test_skills.py
All checks passed!
1 file already formatted
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py::test_every_place_that_takes_a_nit_in_names_the_marker
1 passed in 0.09s
exit: 0
