I've built 137. Nothing is committed, and the full gate passes (`./check.sh`: 2448 passed, 13 skipped).

## Slices built
1. **The alternatives go into the ledger (R1–R3).** Agents can now put indented `- OPTION: <option> — <pros and cons>` lines and a `- WHY:` line under any `DECISION`. `decisions` copies them under the ledger line. A line that has no options gets them filled in once, either from a later raise of the same question or from the approver's `ESCALATED` line. After that it never gets more, and a rerun changes no byte. `read_ledger()` gains `options`, `why` and `settled`. A ledger written before this change reads exactly as it did, with the new fields empty.
2. **The approver weighs each default (R5–R7).** The approve prompt now names every open default by id. It asks for one `- SETTLED: D<n>: …` or `- ESCALATED: D<n>: …` line per default, and names the ones that still have no options.
   - `decisions` reads the current `decision.md` only. It ticks a settled default `→ settled by the approver: <reason>`.
   - It refuses to settle a blocking line, a decided line, a superseded line, an unknown id, or an id named twice, and lists each in `unsettled` with why. The JSON gains `settled`, `unsettled` and `bare`.
   - A settled line is neither open nor decided: `verdicts` doesn't count it, `--task decided` refuses it, and it is never read as an upgrade answer.
   - `approver.md` explains all this.
3. **The landing (R8, R9).** It now counts `assumed` only from open defaults, which also stops it listing a superseded default as assumed. Settled defaults get their own list and their own heading, "Settled by the approver". A settled default is also a landing signal of its own. Landing a change still confirms open defaults only, never a settled one.
4. **Status, board and metrics (R10, R11).**
   - `sdlc.py` and `board.py` each get a pinned copy of the settled mark, so neither counts a settled line as the person's answer.
   - `_factory_files()` counts `defaults_settled`, and `metrics.rework()` adds it to `Sdlc-Rework` whenever that count is there. The `metrics.py` docstring names the key.
5. **`factory.py ask NNN [--answered D2,D3]` (R13, R14).** A new read-only command for a change at `stage: test`.
   - It lists the open items, each with the reply that raised it, its question, options, why and the approver's escalation reason, and lists the settled ones apart.
   - Given the ids just answered, it says what comes next: `decide`, `rebuild` (with `then`: `/sdlc-factory:build` after an ESCALATE, `/sdlc:ship` after a READY) or `ship`.
   - I ran the real command once: it refused this change because it is at `stage: build`, as it should.
6. **Prompts and skills (R4, R12, R15, R16).**
   - The builder and all six reviewer prompts show the `OPTION`/`WHY` lines with an example.
   - Ship's `factory.md` shows each open default with its options, and settled lines as a list of their own.
   - The build skill's line "escalates while any is unconfirmed" now says what the approver does, and its restart and final report name settled lines apart.
   - New skill: `plugins/factory/skills/decide/SKILL.md`. It asks each open item in a dialog of its own and writes nothing before its single WAIT. After a yes it edits the ledger to `→ decided:` and runs `ask --answered <ids>`.
7. **Docs (R17).** The factory README, the factory.py docstring, REFERENCE.md's "What needs me" paragraph, and AGENTS.md's list of writing skills.

## Tests added
Every test the spec names is in place, in `tests/test_factory.py`, `tests/test_land.py`, `tests/test_sdlc.py`, `tests/test_board.py`, `tests/test_metrics.py` and `tests/test_skills.py`. Each requirement's test failed for the expected reason before its code went in, with two exceptions:
- **The R4 prompt test** never failed in front of me, because I edited the prompts before writing it. The prompts at `HEAD` contain no `- OPTION:` lines, so it would fail there.
- **R12 and R15** were also written after their prompt or skill edits. Only the R15 gate test failed once, and that was on the skill's own wording.

Three existing tests changed:
- `test_the_build_session_brings_the_persons_decisions_to_them`: its "still unticked" check now uses the new wording, as R5 says.
- The superseded-default test gains a check that the landing doesn't list a superseded default as assumed (R8).
- `test_archive.py`'s close-trailer test now expects `defaults_settled=0` for a factory change. That zero is a real count; a change built by hand still gets no key.

## plan.md
I wrote it before any code. Afterwards I added the files the plan hadn't listed (`test_land.py`, `test_archive.py`) and the helper functions as built (`sub_lines`, `sub_text`, `approver_weighing`, `_settle_refusal`, `weigh_text`, `reply_path`). I wrote no `notes.md` and no `checks.md`.

## Decisions
- DECISION: [default] A default the approver settled stops a batch from landing on its own (R9, which `spec-questions.md` left to you). Going ahead with that unless told otherwise.
  - OPTION: a landing signal — you see every approver call before it reaches main; fewer batches pass by themselves
  - OPTION: no signal — a READY batch whose only open items the approver settled lands `by=auto`, which helps O6 more; an agent's call reaches main without you seeing it
  - WHY: the spec as approved has R9, and its Boundaries put it under "Asks first"
- DECISION: [default] Keep the change that stops the landing listing and signalling a superseded default as assumed in this change, not split out. Going ahead unless told otherwise.
  - OPTION: keep it here — `open` is one check across `verdicts`, `decisions` and the landing; it changes the landing's signals slightly
  - OPTION: split it out — this change stays narrower; the landing keeps the old check that counts superseded lines as assumed
  - WHY: R8 asks for this check, and it matches what 105 R7 already says a superseded line is

## Evidence

$ ./check.sh > check-run.log 2>&1; echo "exit: $?"; grep -E "passed|failed|ruff|files already formatted|All checks" check-run.log
exit: 0
All checks passed!
250 files already formatted
2448 passed, 13 skipped in 231.31s (0:03:51)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_factory.py tests/test_land.py tests/test_skills.py tests/test_metrics.py tests/test_board.py tests/test_sdlc.py tests/test_archive.py -k "alternatives or bare_line or settle or settled or weigh or superseded or ask_ or garbled or decide or factorys_files or patterns or pinned or absent or zero or build_session"
85 passed, 4 skipped in 73.24s (0:01:13)
exit: 0

$ uv run --group dev pytest -q -rs tests/test_land.py tests/test_factory.py -k "settled or superseded"
8 passed, 352 deselected in 10.46s
exit: 0

$ uv run --quiet --script plugins/factory/scripts/factory.py ask 137
"137-approver-weighs-defaults is at stage: build, not stage: test: a run still building asks its own blocking decisions, through the session running it"
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k "alternatives or bare_line or settle or settled or weigh or superseded_default_is"
12 failed, 3 passed, 273 deselected in 21.67s
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -k "settled"
2 failed, 64 deselected in 80.85s (0:01:20)
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_sdlc.py tests/test_board.py tests/test_metrics.py -k "settled or garbled or pinned or patterns or absent or zero or factory_parsing"
5 failed, 8 passed in 16.46s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k "ask_"
6 failed, 1 passed, 287 deselected in 9.44s
exit: 1
