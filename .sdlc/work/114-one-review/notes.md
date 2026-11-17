# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Evidence

Built by read-only `git log --first-parent main`, `git show <commit>:<path>` and `git log -p` on
`.sdlc/work/inbox.md`, from `6ae0834` (the first commit after `Close 103-landing-does-what-ship-does`)
to `main` at `ffca1a2`. The change's own commit is each `Close`'s first parent. Counts are lines:
`c` a reviewer's `- CHANGE:`, `p` a `- PREEXISTING:`, `k`/`d` a verifier's `- KEPT:`/`- DROPPED:`.
`F` is the `## F<n>` sections in the committed `findings.md`.

### Each change closed since 103

| Change | Built | Landed / reviewed | `Sdlc-Findings` | Factory rounds (round → role: verdict c/p) | Verifier |
|---|---|---|---|---|---|
| 098-board-fixes | factory | `by=person` | none | r1 code CHANGES c1, ui p1, ux CHANGES c2; r2 ux CHANGES c1 p2; r3 all PASS | r1 k3, r2 k1, d0 |
| 099-board-page-fixes | factory | `by=person` | none | r1 ui p1, ux CHANGES c1; r2 ux CHANGES c1 p1; land-1 ui p1, ux p1 | r1 k1, r2 k1, d0 |
| 101-factory-start-fresh | factory | `by=person` | none | r1, land-1: all PASS c0 | none |
| 102-sdlc-docstrings | factory | `by=person` | none | r1, land-1: all PASS c0 | none |
| 105-factory-run-records | factory | `by=person` | none (F0) | r1, land-1: all PASS c0 | none |
| 100-seeds-marked-by-changes | factory, shipped by hand | ship | `important=1 nit=1 … wrong=correctness:1 minor=cost:1` (F2) | r1 code PASS c0 | none |
| 104-landing-follows-main | factory | `by=person` | none | r1, r2, land-1, land-2: all PASS c0 | none |
| 106-factory-reviewer-coverage | factory | `by=person` | none | r1, land-1: PASS c0 | none |
| 107-board-needs-you | factory | `by=person unreviewed=unknown` | none | r1 code CHANGES c1, ux CHANGES c1; r2 PASS | r1 k2, d0 |
| 108-resolve-markers | factory | `by=person` | none | r1 code PASS c0 | none |
| 109-landing-stops-only-for-cause | factory | `by=person` | none | r1, land-1: PASS c0 | none |
| 115-intent-cases-grader | factory | `by=auto` | none | r1 code PASS c0 | none |
| 110-board-says-it-plainly | factory | `by=person` | none | r1 code CHANGES c1, ui p1, ux p1; r2 code p1, ux p1; land-1 code CHANGES c1, ux p1 | r1 k1, land-1 k1, d0 |
| 117-release-loose-ends | factory | `by=person` | none | r1, land-1: PASS c0 | none |
| 118-retro-spend-indicators | factory | `by=person` | none | r1, land-1: PASS c0 | none |
| 111-factory-loose-ends | factory, shipped by hand | ship | `important=1 correctness=1 fixed=correctness:1` (F1) | r1–r3 code CHANGES c1 each; r4 PASS; land-1 code CHANGES c1 | r1–r3 k1 each, land-1 k1, d0 |
| 116-register-and-docs | factory | `by=person` | none (F0) | r1 code CHANGES c1; r2, r3 PASS; land-1 code CHANGES c1; land-2 PASS | r1 k1, land-1 k1, d0 |
| 119-ui-review-folders | factory, shipped by hand | ship | all zero (F0) | r1 code PASS c0 | none |
| 113-hand-gate-slots | factory | `by=auto` | none | r1, land-1: code, test PASS c0 | none |
| 112-factory-tier-promotion | factory, shipped by hand | ship | all zero (F0) | r1 code, test, ui, ux PASS c0 | none |
| 122-retro-one-diff | factory | `by=auto` | none | r1 code PASS; land-1 behaviour PASS | none |

### Bugs with `Introduced by:` (filed since 103)

| Bug | Introduced by | Built | What escaped |
|---|---|---|---|
| 2026-11-17-85 | 106-factory-reviewer-coverage | factory, landed `by=person` | the ui and ux reviewers can't run at once |
| 2026-11-17-90 | 109-landing-stops-only-for-cause | factory, landed `by=person` | the behaviour reviewer's `exit:` lines |

Bugs filed since 103 without `Introduced by:`: 71–75, 78, 79, 86 (86 is a landing review's
false positive the verifier kept).

### What the rows say, against the spec's choices

- **Every escape since 103 is in a factory-built change** (85, 90), both landed by the person on the
  factory's review alone, with no `Sdlc-Findings` to read. Supports R7–R9: a factory review leaves
  no record retro can count beside ship's.
- **The factory's code reviewer already raises context findings, untagged.** 116 r1's one CHANGE is
  a doc (`docs/CONTRIBUTING.md:193`) the diff made false, and 110 r1's is a re-implementation
  (cost/contract), both filed as correctness by role. Supports R4 (ask for the pass on purpose) and
  R5 (the `[pass]` tag).
- **The factory's pre-existing findings reach the register only as `[idea]` seeds.** 098, 099 and
  110 raised ten `PREEXISTING` lines across rounds, and none reached the register as a `[bug]`;
  110's became seeds titled by their first sentence (e.g. 2026-11-17-84). Supports R17–R19.
- **The verifier has dropped nothing since 103** (every `verified.md` d0), and one kept change was
  a false positive (86). Supports keeping `wrong` from the verifier only as the agents' word (R11):
  ship may raise again what the verifier dropped.
- **Ship's own reviews of factory changes (100, 111, 112, 119) found 2 important, 1 nit**, and
  100's important was `wrong`. Nothing here argues against counting ship's apart (R9).
- **No row contradicts a choice in *Design*.** No blocking decision raised.

## Gaps left (R15)

- [x] gap: security: ship checks only secrets, plus the fresh reviewer on a sensitive path; it has no security pass at the depth of the factory's `reviewer-security`. → seed: 2026-11-18-2
- [x] gap: end-to-end: ship never runs the spec's path end to end, as the factory's `reviewer-behaviour` does at landing. → seed: 2026-11-18-3
- [x] gap: ui: ship has no UI review of a change that renders a page, where the factory runs `reviewer-ui` when `[ui]` is set. → seed: 2026-11-18-4
- [x] gap: ux: ship has no UX review, where the factory runs `reviewer-ux` when `[ui]` is set. → seed: 2026-11-18-5
- [x] gap: nits: the factory records its agents' `- NIT:` lines in `findings.md` but never weighs them (theme, cost, value) or files them as `[nit]` entries, as ship does. → seed: 2026-11-18-6
- [x] gap: landing rounds: `findings.md` holds only the build rounds (`reviews/round-<N>/`); the landing's review rounds (`reviews/land-<n>/`) are not in it. → seed: 2026-11-18-7
