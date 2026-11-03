---
id: 035
slug: honest-review-findings
kind: spec
created: 2026-11-03
updated: 2026-11-03
---

# 035 — Review findings a person can trust · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

The guide (seed 2026-11-03-1):

1. R1. `guide/review.md`'s reporting rules require every finding to cite its evidence as
   `path:line`, never a guess from a name; to name its class of bug and say whether other
   instances exist; and the findings to open with their count by rank, saying "nothing to fix"
   when there are none. A test asserts each rule is in the guide.
2. R2. The correctness pass asks, on a change with `fixes:`, whether the diff fixes the root cause
   or a symptom. A test asserts it.
3. R3. The guide has a slot `### Paths this repo's review skips` under `## Reporting rules`, with
   neutral text of its own; `defaults/REVIEW.md` prompts for it under the same key, and its
   failure-classes prompt says what failure looks like ("for docs, it lies; for config, it
   misroutes"). `test_every_prompt_sits_in_a_guide_slot` passes and `sdlc.py drift` is clean after
   `record`.

Pre-existing findings (seed 2026-11-03-2):

4. R4. The guide defines a third rank, **Pre-existing**: a finding whose evidence lies in lines the
   diff neither adds nor changes, and which the diff doesn't newly reach (a new call into old broken
   code is the diff's own finding, Important or Nit). It never blocks the commit. Ship's Step 4
   proposes each as a `[bug]` entry (`Severity:`, `Paths:`, an id from the same `next-entry` call),
   and Step 6 appends it after the WAIT.
5. R5. `ship_question()` and `preflight --question` take `--bugs`, adding a clause naming the bugs
   shown and the register they're filed in; a test pins the wording with and without it.

Every finding answered (seed 2026-11-03-3):

6. R6. Ship writes its findings to `.sdlc/work/NNN-slug/findings.md` right after its review, every
   run, a run that stops on an Important finding included: a named exception to
   confirm-before-writing like `base`, since it writes only the change's own uncommitted folder and
   a rerun rewrites it. The exception is stated in the skill and in `AGENTS.md`.
7. R7. `findings.md` follows `templates/findings.md`: each finding a `## F<n>. [<rank>] [<pass>]
   <title>` section with `Evidence: <path:line>`, `Class: <the class>`, `Disposition:
   <open|fixed|recorded|wrong|intentional|minor>` and, for `wrong`, `intentional` and `minor`, a
   `Reason:` line. A test asserts the template's shape.
8. R8. A rerun reads the existing `findings.md`: earlier F-ids are kept, one the diff no longer
   shows is marked `fixed`, one answered `wrong`, `intentional` or `minor` is never raised again,
   and new findings take the next ids.
9. R9. `sdlc.py findings <NNN>` (read-only) parses `findings.md` and prints its counts, the
   `Sdlc-Findings` line, and `problems`: a malformed section, an unknown rank, pass or disposition,
   a dismissal without a reason, a finding still `open`. Ship's Step 4 takes the trailer from it,
   never counting by hand. It has a `Bash(...)` rule in ship's `allowed-tools`, and in
   `ALLOW_RULES` if read-only commands are listed there.
10. R10. The trailer keeps `important`, `nit` and the four pass keys as now, and adds
    `preexisting=<n>` and one key per disposition whose value is its count by pass
    (`fixed=correctness:2,context:1`), or `0` when none. A test parses an old trailer and a new one
    through `metrics.parse_trailers()`, unchanged.
11. R11. `sdlc.py ship <NNN>` refuses while `findings.md` holds a finding still `open`, as it
    refuses an unticked undone item. A change with no `findings.md` is not refused, so every change
    opened before this one ships as before. A test covers both.
12. R12. Retro's `metrics_summary()` adds to each group `preexisting`, findings by pass, and
    dispositions by pass summed only over the changes whose trailer carries them, with `answered`
    counting those changes. An old trailer adds to the counts and never to the dispositions: a
    missing key is unknown, not zero. A test runs a window with one change of each.
13. R13. The retro skill says `metrics`' findings carry dispositions, and that the review's noise
    is `wrong` against everything answered, read only beside `answered`.

Docs and the seeds:

14. R14. `docs/REFERENCE.md` (the trailer, `findings.md`, the `findings` command),
    `guide/process.md`'s account of the review (three ranks, every finding answered) and
    `AGENTS.md` (the exception, a line on `findings`) say what changed.
15. R15. Seeds 2026-11-03-2 and 2026-11-03-3 are deleted from the register in this change's
    commit, which names them: a one-off, `idea:` stays single.

## Design

- **The guide.** R1–R4 are text in Pass 1 and Reporting rules. The new slot sits under
  `## Reporting rules`, keyed like `### The ways this repo's code fails`, so `doc_units()` places a
  host's answer there. This repo's `.sdlc/REVIEW.md` gets nothing (answers only).
- **`findings.md`** is a change artifact like `notes.md`, written by the skill (prose) and read by
  the script (counts). Ship's Step 3 ends by writing it from the review. Step 4 runs
  `sdlc.py findings <NNN>`, shows the count line first, and asks the person to answer each finding
  they dismiss; their answers are part of what the WAIT approves. Step 6 writes the approved
  dispositions into the file before `sdlc.py ship`, which refuses an `open` one.
- **Parsing.** `findings_entries(text)` reads the sections, their `Key: value` lines read as text,
  beside `nit_entries()`, returning entries and problems and never raising.
- **Trailer.** `findings_trailer(entries)` builds the line. Pass counts include pre-existing
  findings; `important` and `nit` count the diff's own.
- **Retro.** `metrics_summary()` extends the `findings` dict it already builds per group; nothing
  in `closed_changes()` changes, since it already reads the trailer from the change's own commit.
- **Ship's WAIT.** `ship_question()` gains `bugs: bool`, its clause beside the nits clause.

## Contracts touched

- **Confirm before writing: a policy edit, said loudly.** Ship gains a second named exception
  beside `base`: writing `findings.md` before its WAIT. It stays inside the rule's intent: it writes
  only the change's own uncommitted folder, holds no decision (dispositions are approved at the
  WAIT), and any rerun rewrites it. `AGENTS.md` names it.
- **One WAIT per writing skill:** ship keeps exactly one; the bugs clause joins its question.
- **Ship's question worded by `preflight --question`:** `--bugs` goes through `ship_question()`.
- **Narrow `allowed-tools`:** one new rule for `findings`, written exactly as the skill runs it.
- **The metrics trailer is a contract:** extended with new keys; existing keys keep their meaning.
- **`sdlc.py` never writes artifact prose:** the skill writes `findings.md`; the script reads it.
- **Shipped doc shape:** `templates/findings.md` follows `test_defaults.py`'s template rules.
- **Guide edits rerun `record`; `.sdlc/REVIEW.md` holds answers only.**

## Alternatives rejected

- **A mechanical "pre-existing" check in `preflight`** (cited line outside the hunks): it needs
  findings handed to the script as structured input before the review is done, and can't see the
  case that matters most, a new call into old code. The `path:line` evidence rule lets the person
  check the call instead.
- **Remembering earlier findings only within the session:** "fixed" would go uncounted across
  sessions, and phase 3 would read counts, not what the review saw.
- **`idea:` taking a list** so one change builds three seeds: a frontmatter key history's readers
  parse, too much contract for a one-off.
- **Dismissal reasons in a commit-body paragraph:** `findings.md` holds them, committed with the
  change.
- **A cheap pre-existing fix offered as "fix it now":** the person can still answer `fixed` by
  fixing it in the change; the skill only makes a bug entry the default.

## Verification

- `./check.sh` passes: ruff, format, pytest, `claude plugin validate --strict`.
- `uv run --quiet --script scripts/sdlc.py drift` from this worktree reports nothing after `record`.
- `uv run --quiet --script scripts/sdlc.py findings 035` on this change's own `findings.md` prints
  counts, the trailer and no problems.
- The retro tests show `answered` and dispositions for a new trailer and none for an old one, in a
  scratch repo.
- Shipping this change uses its own new flow (`_own_script()`), and its trailer carries
  dispositions.
