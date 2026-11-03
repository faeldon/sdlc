---
id: 037
slug: escaped-bugs-tune-review
kind: spec
created: 2026-11-04
updated: 2026-11-04
---

# 037 — Retro tunes the review from the bugs that got past it · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1.** `Sdlc-Fixes:` gains `paths=<p1>,<p2>` from the bug's `Paths:` (spaces dropped), or
   `paths=unknown` when the entry has none. Lines without the key still parse, and read as paths
   unknown. A test pins both.
2. **R2.** Each row of `retro`'s `bugs.escapes` keeps `change`, `bugs` and `tier`, and adds
   `escaped` (each bug's id, title, severity, paths) and `review`: what that change's ship review
   left, read from its own commit (the `Close` commit's parent). `review.state` is `file` (it has
   a `findings.md`), `trailer` (only `Sdlc-Findings`) or `unknown`; `review.counts` the trailer's
   counts or null; `review.findings` each finding's id, rank, pass, title, class, disposition,
   `by` and evidence. `unknown` never reads as a clean review. Tests cover all three states.
3. **R3.** Each finding in R2 carries `on_paths`: true when its `Evidence:` path equals, sits
   under, or contains one of the escaped bugs' paths; false when none; null when the bugs' paths
   are unknown. Tests cover a file, a directory prefix and unknown paths.
4. **R4.** `bugs.rate` gives `window` and `previous`, each `{escapes, changes, rate}`, and `trend`:
   `up`, `down`, `flat` or `unknown`. Escapes are bugs, open or fixed anywhere in history, whose
   reported date falls in that window and whose `Introduced by:` names a change; retired bugs never
   count. The previous window runs between the two newest `Retrospective` commits. `trend` is
   `unknown` with no previous window or when either has fewer than `RATE_MIN_CHANGES = 5` closed
   changes. Tests cover each trend.
5. **R5.** `bugs.important` lists every Important finding in the window's closed changes, from each
   one's `findings.md`: change, id, pass, title, class, disposition; `bugs.important_unknown` counts
   the changes with no file.
6. **R6.** The retro skill's Process pass says, for each escape, which layer should have caught it:
   no finding on its paths (the passes missed it), a finding on its paths answered `wrong`, `minor`,
   `intentional` or `recorded` (seen and let through), or review unknown. It proposes a missed
   class, or a class two or more changes' Important findings share, as a **seed** whose body holds
   the exact `- **lead**` bullet for the review doc's "ways this repo's code fails" (or a lint rule
   or test instead), citing the bug ids, the change and its findings.
7. **R7.** On `trend: up` the skill proposes a tightening seed (the exact path for
   `[review] sensitive`, the fresh review always on, or a class made blocking); on `down` or `flat`
   with `[review]` lists set, it may propose a loosening seed; on `unknown` it says why and
   proposes nothing about depth. Every such seed states both rates and how many changes they rest
   on.
8. **R8.** Retro writes nothing it didn't before: `cmd_retro_commit()`'s allowed paths and the
   skill's `allowed-tools` unchanged. The skill's Out of scope names the review doc and
   `.sdlc/config.toml`, and a skill test pins that.
9. **R9.** A repo with no bugs: `escapes` is `[]`, `important` only what `findings.md` files show,
   `rate` zero escapes, every other key of `retro`'s output unchanged, and the skill says nothing
   about review depth.
10. **R10.** Docs: `docs/REFERENCE.md` (`Sdlc-Fixes` `paths=`, retro's new `bugs` keys),
    `guide/review.md` (the slot says retro proposes leads for it from escapes), `AGENTS.md` (the
    bugs paragraph names the pairing). `sdlc.py record` if the guide changes.
11. **R11.** At ship, 2026-11-03-7 leaves the register through `idea:`, -8 deleted by hand, -9's
    `After: 2026-11-03-8` line removed, -13's `After:` reduced to `2026-11-03-12`.

## Design

- **Fixes trailer.** `fix_trailers()` already reads the entry's `fields`; it appends `paths=` from
  `Paths:` split on commas. `metrics.parse_trailers()` needs no change: `paths` comes through as a
  string field, which a reader splits on `,` (`unknown` → none).
- **Reading a review from history.** `_review_at(home, name, sha)`: `git show
  <sha>:<work_rel>/<name>/findings.md`, parsed by the same parser `findings_entries()` uses (split
  into a text-in helper, so `check` and retro share it), plus the `findings` trailer
  `closed_changes()`'s record already holds. `bugs_retro()` already builds `history` (every closed
  change, read) and walks the escapes; each escape row now collects its bugs, and calls
  `_review_at` once per change.
- **Paths overlap.** `on_paths` compares the evidence's `path` (before `:line`) with each bug path:
  equal, `path.startswith(bug.rstrip('/') + '/')`, or the reverse.
- **Rate.** `retrospectives(home, trunk)` returns every boundary newest first;
  `last_retrospective()` becomes its first, so there is one reader. Escapes for a span come from
  open bugs plus the fixed ones in every `history` record's `metrics.fixes`, by `reported` date;
  changes for the previous span from `closed_changes(home, older, newer, read=False)`. Trend
  compares `rate` with `previous.rate`, `flat` when equal.
- **Important findings.** `retro()` reads `findings.md` from each window change's own commit (one
  `git show` each), keeping Important rows.
- **Skill.** The Process pass's `bugs` paragraph is rewritten for R6–R7; Step 3's Seed disposition
  says a review-doc or `[review]` proposal is a seed whose body holds the exact text; Out of scope
  adds the review doc and `.sdlc/config.toml`. No new tools or commands.

## Contracts touched

- **Metrics trailers are a contract, extend never redefine:** `paths=` is a new key on
  `Sdlc-Fixes`; old lines read as unknown.
- **Retro read-only until its WAIT, one commit through `retro-commit`:** unchanged (R8).
- **`findings.md`'s format (035):** read only; the parser is shared, not forked.
- **Ids matched with `names_change()`:** escapes already resolve this way; the review lookup uses
  the resolved name.
- **Bugs are `/sdlc:bug`'s to file and retire:** retro still never touches `[bug]` entries.
- **Allowed-tools exact, one WAIT:** no new commands; the WAIT wording is unchanged (seeds already
  counted).
- **Release, publish and measuring never read the register:** untouched; the register is read in
  `fix_trailers()` at close, as now.

## Alternatives rejected

- **Retro edits `REVIEW.md` and `[review]` itself:** review depth would change on `main` with no
  ship review. The person chose seeds.
- **A `Class:` key on `[bug]` entries:** asks `/sdlc:bug` for a judgment better made at retro,
  beside the review that missed it.
- **A configurable rate threshold:** speculative; the script reports the numbers, a minimum sample,
  and the direction, and the person judges at the WAIT.
- **Rate as bugs attributed to changes closed in the window:** the newest window always looks clean
  because its bugs haven't been found yet; reported-in-window per closed-in-window compares like
  with like.
- **Building 2026-10-25-12's `reworks:` too:** its own design, left out by choice.

## Verification

- `./check.sh`, its exit code read directly.
- `uv run --group dev pytest tests/test_retro.py -q`, new cases for R1–R5 and R9.
- `sdlc.py retro` on this repo: `bugs.rate` (previous window 2026-10-24..2026-10-26),
  `escapes: []`, `important` from 035's and 036's `findings.md`, no other key changed.
- `sdlc.py drift` empty.
