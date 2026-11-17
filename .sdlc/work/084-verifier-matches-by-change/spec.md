---
id: 084
slug: verifier-matches-by-change
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 084 — The verifier's answer matches its change by more than exact text · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. R1. The verify prompt lists each change the round asks for with an id, `C<n>` from 1, in the
   order `read_rounds()` reads them (the `REVIEWERS` order, then each file's line order, each
   `(role, text)` once), as `- C1: code: <the reviewer's text>`; a test pins the order and that a
   repeated line gets one id.
2. R2. An answer line may open its change with that id: `- KEPT: code: C1: <any words>` and
   `- DROPPED: code: C1: <any words> — <why>`. `read_verified()` resolves it to change C1 and
   records the reviewer's own text as the answer's `change`, so `settled()`, `carry`, rework's KEPT
   list and the landing check read the same text they do today. Tested with words that differ from
   the reviewer's.
3. R3. An answer with no id resolves as before, by exact `(role, text)`; failing that, by its
   `path:line` lead, when exactly one change of that role in the round has that lead and no other
   answer resolves to it. A test built from 078's round-1 `code.md` and `verified.md`, as they are,
   reads one change, answered once, dropped, with no problem.
4. R4. Each of these is still a problem, and `verdicts` still says `stop`, each pinned by a test:
   a change no answer resolves to; a change two answers resolve to; an id outside the round's
   (`C9` of three); an id whose change is another role's; an unnumbered answer whose lead matches
   two changes of its role, or none.
5. R5. `verified.md`'s line shape stays `- KEPT|DROPPED: <role>: <rest>`, so the board's
   (`scripts/board.py:39-40`) and `measure`'s (`scripts/sdlc.py:3636-3637`) copies of the patterns
   are unchanged and still count every line by role: `Sdlc-*` trailers for a run with ids equal
   those for the same answers without. The pinning tests stay green unedited.
6. R6. `plugins/factory/agents/verifier.md` tells the verifier to open each answer with its
   change's id, then say the change in its own words, and keeps the example lines in that shape.
7. R7. `./check.sh` passes.

## Design

The id is the order, not new data. `read_rounds()` already gathers each round's
`reviews[role]["changes"]` in a fixed order, and the verify prompt (`factory.py:1480-1494`) is built
from that same structure, so a helper `asked_changes(reviews) -> list[(id, role, text)]`, used by
both, numbers them once: deduplicated with `dict.fromkeys` as `read_verified()` already does.

`read_verified()` keeps its loop over `KEPT_RE` and `DROPPED_RE` (unchanged patterns) and adds a
resolve step for each answer, in order:

1. `ID_RE = ^C(\d+):\s*(.*)$` on the answer's text: the id must name a change of the round whose
   role is the answer's, else a problem naming the id.
2. Exact `(role, text)`, today's rule.
3. The lead, `path:line` (the text up to its second `:` when what's between is digits, reusing
   `_change_path()`'s split), matched against the same lead on that role's changes: only when it
   is unique among them and not already taken by an earlier answer.

A resolved answer stores the reviewer's text as `change`; the dropped one's `why` is still split at
the last `DROP_WHY`. The counting rule then runs on resolved changes: every asked change exactly
once, every answer resolved to one. Problems keep their wording, so `verdicts` and the stop text
read as now.

## Contracts touched

- **Metrics trailers are a contract: extend, never redefine.** Nothing here changes a trailer or
  its counting: `measure` still counts `DROPPED` lines by role (R5).
- **The factory's copies of `sdlc.py`'s parsing, each pinned by a test.** The patterns don't
  change, so neither do the copies or their pins; the new id lives inside `<rest>`.
- **Agents that judge have no Write.** Unchanged: the verifier returns text, `factory.py` files it.
- **The factory never imports `sdlc.py`.** Unchanged.

## Alternatives rejected

- **Fuzzy text matching** (a similarity threshold): a model's summary of one change can sit as
  close to another's as its own, and a threshold is a judgment the script can't explain in a stop.
- **Ids written into the reviewers' files**: every reviewer prompt and file would change, and a
  reviewer numbering wrongly is a new failure; the order already is the number.
- **A new line shape, `- KEPT: C1: …`**: the board's and `measure`'s `([a-z]+):` role group would
  stop matching, breaking the per-reviewer `dropped` counts and three pinned copies.
- **Asking the verifier again on a mismatch**: a second paid run to fix what the script can read
  already; kept as a possible seed, not this change.

## Verification

- `uv run --group dev pytest tests/test_factory.py -q -k verif` — R1-R4's tests pass.
- `uv run --group dev pytest tests/test_metrics.py tests/test_board.py tests/test_archive.py -q`
  — the pins and the `dropped` counts pass unedited (R5).
- `./check.sh` exits 0.
- Live, once landed: `factory.py verdicts 078 --head 7bf646e` no longer says `stop` for
  `reviews/round-1/verified.md`, and names the next step.
