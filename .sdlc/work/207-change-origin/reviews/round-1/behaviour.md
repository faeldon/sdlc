VERDICT: PASS

No CHANGE or DECISION to raise. The new tests pass and the skill and doc edits match the spec. I did not run the real `close` and `retro` against a scratch repo, so the end-to-end path rests on the tests. D1 and D2 in `decisions.md` are the builder's own defaults, and I left both open.

## Notes
- **End-to-end path.** The spec's by-hand path is to close a change with `origin: host`, then check the trailer on the `Close` commit and `origins.host` in `retro`'s JSON. `test_close_writes_an_origin_trailer` and `test_retro_counts_changes_by_origin` cover both, and both pass. The other six selected tests (the other `test_archive.py` origin tests and the `parse_trailers` one) pass too.
- **Code and skills.**
  - `origin_trailer()` in `scripts/closing.py` is added and called when the `Close` commit is built.
  - `skills/intent/SKILL.md` has the `origin:` proposal, and Step 4 carries the `found in a host` / `found here` clause.
  - `batch.md`, `skills/idea` and `skills/bug` carry the `Origin:` line.
  - `skills/retro/SKILL.md` describes `origins` and says nothing when all are unknown.
- **Docs.** `FEATURES.md` names `Sdlc-Origin`, `origin:` and `origins`, and `REFERENCE.md` was updated.
- **Gate.** The record `build/round-1.gate.md` says `GATE: PASS`. I did not rerun the suite.
- **`checks.md`.** The file doesn't exist, so there is nothing to read or run.
- **Decisions.**
  - D1 masks `plugin=<version>` in `tests/fixtures/close-output.json`, a stale fixture that is unrelated to this change but needed for a green gate.
  - D2 leaves `origin:` unset on 207's own intent.
  - Both are the builder's defaults and the person can overrule them at ship.

## Evidence
$ head -5 .sdlc/work/207-change-origin/build/round-1.gate.md
GATE: PASS

## Attempt 1

Verdict: PASS

$ git status --short
 M docs/FEATURES.md … M tests/test_skills.py
?? .sdlc/work/207-change-origin/

$ uv run --group dev pytest -q -p no:cacheprovider tests/test_archive.py -k origin tests/test_metrics.py::test_parse_trailers_reads_origin_as_text tests/test_retro.py::test_retro_counts_changes_by_origin
6 passed, 170 deselected in 15.12s
exit: 0

$ uv run --group dev pytest -q tests/test_sdlc.py tests/test_skills.py -k origin
9 passed, 717 deselected in 0.28s
exit: 0

$ grep -n "origin" scripts/closing.py | head -20
558:def origin_trailer(main: Path, branch: str) -> list[str]:
1149:    trailers = c.captured + based + fixes + origin_trailer(c.main, c.branch)

$ grep -n -i "origin" skills/retro/SKILL.md | head
62:- `origins`: …
346:   Read `origins.host` as evidence from use in another repo …
349:   When every change in the window is `unknown`, say nothing about origins.

$ grep -n "origin\|Origin\|found in a host\|found here" skills/intent/SKILL.md skills/idea/SKILL.md skills/bug/SKILL.md skills/intent/batch.md | head -30
skills/intent/SKILL.md:130: … :212: … `found in a host` … skills/idea/SKILL.md:115: `Origin: <host…>` skills/bug/SKILL.md:119 …

$ grep -n "Origin\|origin" docs/REFERENCE.md docs/FEATURES.md | head
docs/FEATURES.md:63, 190, 202; docs/REFERENCE.md:449 …
