VERDICT: PASS

Every requirement R1–R14 has a test that fails without it, and none of the tests can pass vacuously.

## Notes

- **Gate:** `build/round-1.gate.md` is PASS, with `3081 passed, 28 skipped` and a passing `claude plugin validate --strict`.
- **Tests I ran:** I ran only the tests named for this change, in the foreground: `uv run --group dev pytest -q tests/test_retro.py tests/test_metrics.py -k "runtime or coverage or underneath or no_factory or never_mentions or greyed"`. 11 passed, 334 deselected.
- **R1:** The fixture covers a main session, a factory agent's session and a sub-agent's transcript.
  - It includes a `<synthetic>` model, an empty value, and an entry from another branch (`OTHER`).
  - It checks that the same version on two entries gives one event, and that the summary is unchanged with and without the `runtime` events.
- **R2:** The round trip covers `2.1.10` staying text, `/` and `~` being cleaned, sorting and deduplication, and a None result.
- **R3:** Three tests in `test_archive.py` cover the line's position after `Sdlc-Lead`, a drop writing `plugin=` alone, and `runtime=failed` with the close still landing. `test_adoption.py` also pins the line's regex.
- **R4–R7:** The window mixes the five cases the spec lists, and the expected `missing_because` dicts are written out.
  - It checks that spend's `missing_because` equals its `why`.
  - R6 is parametrised over 4 of 10, 5 of 10 and 0 of 0.
  - The report test checks the italics and the `a hint` ending.
  - It also checks the no-metrics case and the empty-window case.
- **R8–R10, R12:** These are covered, including `null` rather than `false` when a side recorded nothing.
  - They also cover the first-retrospective and no-retrospective cases, and a role-model fallback for a change with no `Sdlc-Runtime`.
  - The R12 test stubs `subprocess.run` so anything but git raises.
- **R11:** The test walks the JSON keys and checks the report text.
- **R13–R14:** `templates/retro.md` has no diff. `skills/retro/SKILL.md` gains one Trust bullet and `docs/` mentions `Sdlc-Runtime`.
- **`decisions.md`:** D1–D3 are builder defaults and none is blocking, so I raised nothing against them.
- **`checks.md`:** The change has none, and no requirement needed one.
