DECISION: ESCALATE

**Why.** The reviews give no reason to stop. Both round-1 reviewers returned `VERDICT: PASS` with no CHANGE findings. The gate passed (`./check.sh`: 2200 passed, 9 skipped), and every requirement from R1 to R10 has its code and a named test. The escalation is only because three builder defaults in `decisions.md` (D1–D3) are still unticked: the build rests on calls you haven't confirmed. D1 also departs from the spec's literal wording in R8, though `plan.md` explains why. The change also adds a heading to `templates/retro.md`, a published template the script now reads.

**Open items**
- None. Neither reviewer, `code` nor `test`, raised a CHANGE. The `code` reviewer left two nits:
  - `_words()` also drops a person's own pasted `<tag>…</tag>` from the count. It undercounts and leaks nothing.
  - `_spend_text` could say why token medians still show when every change is unrecorded.

**Decisions to confirm**
- D1: R8's "left out of every median" is applied per measure. An unrecorded change is in no tool-call figure, but its comment lines (from git) and `out` tokens still count. The spec's literal reading would drop it from every median.
- D2: each change's own `spend` rows print only with `--metrics`. The summary (counts, `why`, medians, outliers, tools) always prints, so the spec's check `retro | jq .spend` shows no per-change rows without `--metrics`.
- D3: added code lines come from the same `git diff -U0` as the comment lines, filtered to code by `_kind()`, rather than from `rec["by_kind"]` (numstat). A suffix with no comment marker counts in `code_added` but not in `comment_base`.

**For the person at ship**
- **`scripts/metrics.py`, first.** Check that `_words()`, `_call()`/`_answered()` and the new `Sdlc-Tool` lines let only counts and `_prompt_name()` names out, never text or paths. Check also that `parse_trailers()` reads a `Close` commit without `tools=`/`words=` as unrecorded.
- **`scripts/retro.py`, next.** `_spend()`/`_spend_text()`, and the `--metrics` strip in `cmd_retro()` around line 1304.
- **`templates/retro.md` and the `TEMPLATE_READS` entry in `sdlc.py`.** A host whose retro template override has no `## Spend` will now see it under drift's `breaking`.
- **R11, at ship.** Ship still has to file the suite-pruning seed through `/sdlc:idea` (`inbox-commit`) on the base branch.

- IMPACT: minor — retro gains a `spend` block and close writes new additive trailers (`words=`, `tools=`, `Sdlc-Tool`); older readers ignore them. A host overriding `templates/retro.md` must add `## Spend`/`{{spend}}`, and drift flags that as `breaking`. Raise this to major if that obligation should count as breaking for a release.

**Undone items**
- UNDONE: R11, at ship: file the suite-pruning pass as a seed through `/sdlc:idea` (`inbox-commit`, on the base branch, never this branch), carrying 2026-11-12-2's third bullet: nothing looks at the tests already in the suite again (one whose code was rewritten, one a newer test repeats, one that passes for the wrong reason, the slowest). Needs per-test run times and a test-to-code map no host records today (spec, *Alternatives rejected*). → seed: Retro proposes a pruning pass over the test suite
- UNDONE: `retro()` and `retro_report()` each call `_change_rows()` per change, and `_spend()` now adds one `git diff -U0` per change on top; `_rework()` runs the same `-U0` diff. One diff per change shared between `_rework()` and `_spend()` would halve those calls. Not this change. → seed: Share one -U0 diff per change between retro's rework and spend

**How to recover**
- RECOVER: templates/retro.md: fix forward: a follow-up change removes `## Spend` from `templates/retro.md` and its `TEMPLATE_READS["retro.md"]` entry together, and runs `scripts/sdlc.py record`. Hosts that already copied or overrode the template keep their own text; drift's three-way check never proposes over a host's edit. `Close` commits already written with `words=`/`tools=`/`Sdlc-Tool` stay in history, and are additive, so nothing reads them wrongly.
