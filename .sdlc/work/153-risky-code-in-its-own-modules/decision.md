DECISION: READY

**Why.** All four reviewers in round 1 (code, security, test, behaviour) returned `VERDICT: PASS`, and the gate record shows `./check.sh` green: 2934 passed, 28 skipped. The security reviewer compared every moved definition with the base. Every one in `closing.py` is identical. In `landing.py` only three differ, and only in the ways R5 allows. The behaviour reviewer ran the R7 `--help` comparison and all 12 outputs were byte-identical. The base lists both modules under `[review] sensitive` (commit 57275df), so this run got full depth with the security pass, as R11 requires.

**Open items**
- None. The one finding is a nit, recorded in `findings.md` as F1 (by `test`), not a change request. It says `test_the_source_guards_reach_closing_py` plants only two of the four cases; the other two are planted in `test_work_folder.py` and `test_skills.py`.

**Decisions to confirm**
- No blocking decisions are unticked.
- SETTLED: D1: R3's test (spec R3) covers functions only ("fails on … a function defined in the script that only the module calls"). Keeping a constant in the script and reading it through the binding moves less than the spec allows, not more, and stays inside the Boundaries' "mechanical move". The security review found every moved body identical apart from the allowed prefix. Keeping the pinned `FACTORY_*` family whole means the pin tests stay as they are.
- SETTLED: D2: Spec R1 says `closing.py` holds "each helper that only close's code calls (by the rule in R3)". R3 says a name moves "when only moved code calls it". `plan.md` lists the measure step among the helpers that move. The `Sdlc-*` trailer format itself is unchanged (R7, `test_metrics` green), and the security reviewer agreed with the default.

**For the person at ship**
- **Start with the two module docstrings:** `scripts/closing.py` and `plugins/factory/scripts/landing.py`.
- **Then the loaders:** `_load_closing()` in `sdlc.py`, and `_Names` and `_load_landing()` in `factory.py`.
- **Then the rewritten `test_only_the_named_steps_push`.** It now reads each file on its own, so check it still pins exactly one `git push`.
- **Read `git diff <base> -- tests/` for R6.** Two reviewers sampled it rather than reading all of it.
- **The new CONTRIBUTING.md *Layout* rows** weren't checked by any reviewer.
- **Watch this change's own close.** `main`'s pre-move `sdlc.py` hands off to the merged one, and that handoff is the first real run of the move. Expect `ran` to name the merged script and no `refusals`.
- **One question in `intent.md` is still open:** whether to wait for the release so the move lands on a released base. That's your call on timing.

- IMPACT: none — this is a pure move between files. No command, flag, output, trailer or config key changes; `--help` is byte-identical, and nothing a host configures or sees names a moved function.

**Undone items:** none. The change has no `notes.md`, and the builder reports nothing left.
