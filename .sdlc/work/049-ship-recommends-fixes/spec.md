---
id: 049
slug: ship-recommends-fixes
kind: spec
created: 2026-11-12
updated: 2026-11-12
---

# 049 — Ship's question leads with its recommendation, and a recommended fix is one yes · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

**findings.md**

1. `DISPOSITIONS` gains `fix`: proposed for fixing before the commit. A `fix` finding needs a `Fix:`
   line saying the exact change, a problem without one (like a dismissal with no `Reason:`); only
   `important` or `nit` may be `fix`, never `pre-existing`. `sdlc.py findings` lists the `fix` ids
   beside `open`. Tests: parse with `fix` and `Fix:`, the problem without `Fix:`, the refusal on a
   pre-existing finding.
2. `sdlc.py ship` refuses while any finding is `fix`, as it does `open`, so `fix` never reaches a
   committed file or trailer and `Sdlc-Findings` gains no key: a fixed one counts `fixed`, an
   unfixed nit `recorded`. A test pins the refusal.
3. **Fresh review recorded (nit 2026-11-03-15).** On a deep diff, findings.md's note carries
   `Fresh review: ran` or `Fresh review: skipped, <why>`; `findings` prints it as `fresh` (`ran`,
   `skipped` with its why, or null); `sdlc.py ship` refuses a deep diff (`risk.deep`) whose
   findings.md says neither. The question reads the skip from the file; the `--fresh-skipped` flag
   goes. Tests pin all three.

**The question (`ship_question()`, from findings.md and the flags)**

4. Nothing `fix` or `open`: `Commit this, <clauses>? (yes / edit the message)`, with `fix all N
   first` before `edit the message` only when other fixable findings exist (nits `recorded` or
   `minor`).
5. Some `fix`, none `open`: `Fix F2 and F4, then commit this, <clauses>? (yes / fix all N first /
   commit without fixing, recording F2 and F4 as nits / edit the message)`. `fix all N first` only
   when there are fixable findings beyond the `fix` ones; `commit without fixing…` only when every
   `fix` finding is a nit (an Important can't land unfixed).
6. Some `open`: `Fix F1 and F3, then review again? (yes / fix all N first / edit the findings)`. An
   Important too big to fix inside a yes no longer stops ship with no question; it asks one that
   offers no commit.
7. "Fixable" for `fix all` is every finding not `wrong`, `intentional` or `pre-existing`, counted
   from the file; the question names no finding the file lacks.
8. **Issue numbers deduped (nit 2026-10-27-7):** `--closing 4 --closing 4` reads `closing #4 when
   it lands`; the existing refusals (neither, both, not on `closes:`) are unchanged.
9. `tests/test_preflight.py` pins each form, each option's presence and absence, and the
   full-clause example; the old `fix a finding first` wording appears nowhere in `scripts/` or
   `skills/`.

**Landing a yes**

10. `sdlc.py ship <NNN> --fixed F2,F4 --through F5` refuses, writing nothing, unless every id in
    `--fixed` reads `fixed` and no finding's id is above `--through` (the highest id the question
    was asked over). Ship runs it after the fixes and the rerun; a refusal is a stop and a new
    question. It is the "nothing new" check, by the script, not prose. Tests: a finding left `fix`,
    and a new F6, each refuse.
11. Ship's skill (Steps 3–6):
    - **yes to `Fix … then commit`:** makes each `Fix:` change, runs the gate, reruns the review
      (rewriting findings.md, each one `fixed`), runs `ship --fixed … --through …`, and commits
      with the approved message, its `Sdlc-Findings` line recomputed by `findings`. A failing gate,
      a refusal, or a fix that needs any other change to the message (its body, `How to recover:`,
      an entry) stops and asks again.
    - **`fix all N first`, or yes to `Fix … then review again`:** fixes, reruns the gate and the
      review, and asks again.
    - **`commit without fixing`:** each `fix` finding becomes `recorded` with its `[nit]` entry,
      shown with the findings and given its id by the same `next-entry` call, then commits.
12. **Eligibility for `fix`:** only a fix of cost S that touches only files the diff already
    changes; anything else stays `open` (Important) or `recorded`/`minor` (nit). Stated in the
    guide's review section, not in code; the `Fix:` line makes each one checkable by the person.

**Measuring (`metrics.happy()` and retro)**

13. `happy()` takes the count of `fixed` findings in the change's findings.md (close reads it from
    the branch with `_findings_from_text()`). Ship reads `yes` when it ran once with no revise
    reply (as now); `fixed` when it ran more than once, with no revise reply, and the file holds a
    `fixed` finding; `no` otherwise. Old trailers never hold `fixed`. Tests cover each.
14. `metrics_summary()`'s `first_time` for ship counts `yes` and `fixed`, and reports `ship_fixed`,
    the share that was `fixed`; a trailer without the value reads as before. Tests pin both.

**Docs**

15. `skills/ship/SKILL.md` describes the forms, the answers and the clean-rerun gate;
    `templates/findings.md` gains `fix`, `Fix:` and the `Fresh review:` note; `guide/review.md` the
    eligibility rule; `docs/REFERENCE.md` the disposition, the question's forms, `ship=fixed` and
    the note; `AGENTS.md`'s "Review findings" names `fix`. `.sdlc/setup.json` is re-recorded;
    `tests/test_skills.py` invariants hold.

## Design

`ship_question()` keeps its clause logic and takes the change's `findings` report. A pure helper,
`_question_head(findings)`, returns the lead (`Commit this` / `Fix F2 and F4, then commit this` /
`Fix F1 and F3, then review again`) and the options from the `fix`, `open` and fixable counts.
`cmd_ship_question` reads `findings_entries()` itself, so the skill passes no finding ids.
`_issues()` dedupes first. The fresh clause comes from the file's note: `_findings_from_text()`
also returns `fresh`, parsed from a `Fresh review:` line outside the sections.

`cmd_ship` gains `--fixed` and `--through`, checked before it stamps anything; without them it
behaves as now, plus the `fix` refusal and the deep-diff fresh refusal.

`measure_change`'s `finish()` reads `{branch}:{folder}/findings.md`, counts `fixed`, and passes it to
`happy(..., review_fixed=n)`. `metrics.py` stays pure. `metrics_summary()` adds `fixed` to the ship
tally.

## Contracts touched

- **A skill's WAIT, what it approves and when (always Tier 2 here).** This is the change: a yes now
  approves fixes described in `Fix:` lines and a commit after them, on condition that the gate and
  the review pass and the script's `--fixed/--through` check holds; anything else asks again. Ship
  still never pushes, and nothing commits before a yes.
- **The skill words no question:** every form comes from `ship_question()`, pinned by
  `tests/test_preflight.py`.
- **Trailers extend, never redefine:** `Sdlc-Findings` gets no key, since `fix` can't be committed;
  `Sdlc-Happy` gets a new value, `fixed`; old trailers keep their meaning.
- **findings.md from history:** old files have no `fix` and no note; they parse as now and read
  `fresh: null`. Retro's `_review_at()` uses the same parser.
- **`templates/` is irreversible:** the commit carries `How to recover:` (a host's copy reaches
  hosts only through `/sdlc:setup`; fix forward with a release).
- **Confirm before write:** `findings.md` stays ship's one write before the WAIT besides `base`; the
  fixes are written only after a yes.
- No policy change.

## Alternatives rejected

- **`Fix: now` beside `recorded`/`open`:** two lines deciding one meaning.
- **Committing after `fix all` without asking again:** it would commit unseen fixes larger than the
  question described.
- **Counting a rerun-for-own-findings as `ship=yes`:** redefines `yes` on new trailers.
- **The skill judging "nothing new" in prose:** a permission-relevant check belongs in the script
  (`--fixed/--through`).
- **Keeping `--fresh-skipped`:** two sources for one fact; the file is the one history keeps.

## Verification

- `./check.sh` passes, with the new `test_preflight`, `test_findings`, `test_metrics` and
  `test_retro` cases.
- `uv run --quiet --script scripts/sdlc.py preflight <NNN> --question` on a fixture change prints
  each form.
- `sdlc.py drift` clean after `record`.
- Manual, at this change's own ship: the review uses the new question, and the person sees it.
