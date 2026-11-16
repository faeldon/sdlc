---
id: 062
slug: backlog-readiness-and-themes
kind: spec
created: 2026-11-16
updated: 2026-11-16
---

# 062 — Readiness groups for the backlog, and taking a theme as one change · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1.** Each `next_up()` item carries `group`: `ready` for the rules `priority` (high), `bug`,
   `milestone`, `series` and `nits` (a person or a review already weighed them), `decide` for
   `idea` and `low` (seeds no one ranked). The rule order inside each group is unchanged. A test
   pins each rule's group.
2. **R2.** Status prints Next up as `Ready to build: N`, then `Needs a decision: M (K low)`, each
   with its lines; the two share the existing ten-line cap (`NEXT_SHOWN`), ready lines first.
   `(+X more: status --all)`, `Themes:`, the waiting count and the milestone lines are unchanged.
   A group with none prints its header with `0` and no lines. A test pins the output.
3. **R3.** `status --all` prints, under each theme holding two or more ideas, the command that
   takes them all: `→ /sdlc:intent <id> <id> …`. A test pins it.
4. **R4.** `intent_ideas(text)` returns every value on an intent's `idea:` line, read as text;
   each record gets `ideas` (the list) beside `idea` (its first value, kept for every JSON reader).
   A single id, a quoted title, and the old whole-heading form read exactly as today; the existing
   tests pass unchanged.
5. **R5.** `sdlc.py ship` deletes each entry the change's `ideas` names, saying so for each it
   can't find, and refuses, before writing anything, when any one matches two headings, as it does
   today for one. A test ships a two-seed change and finds both entries gone.
6. **R6.** `check`'s orphan-`[building]` link, `next_up()`'s open (`named`) and shipped seeds,
   `_milestone_verdicts()` and `_open_claims()` read `ideas`. Tests: both seeds of an open
   two-seed change stay out of Next up; a milestone seed shipped as a change's second idea reads
   `shipped`; `inbox-commit` won't remove either while the change is open.
7. **R7.** `/sdlc:intent` given several entry ids writes them all on one `idea:` line
   (`idea: [2026-10-24-4, 2026-11-12-2]`), tags each `[building]` with its pointer line, and
   drafts one Problem covering them; Step 3 shows the line. A test asserts the text.
8. **R8.** The status skill's text describes the two groups and the theme command, and its
   precedence rule 9 reads "the first `Ready to build` line, else the first `Needs a decision`
   line". A test asserts both.
9. **R9.** `AGENTS.md`'s inbox paragraph (an open change's `idea:` names one or more entries) and
   `docs/REFERENCE.md` (the `idea:` line's list form; status's two groups).
10. **R10.** `./check.sh` exits 0.

## Design

**Groups.** `READY_RULES = ("priority", "bug", "milestone", "series", "nits")`. `next_up()` already
builds items in rule order; it sets `item["group"] = "ready" if item["rule"] in READY_RULES else
"decide"`. The status printer partitions the shown items (the first `NEXT_SHOWN` of
`ready + decide`) under the two headers; the header counts are of each whole group, `low` counted
apart.

**The theme command.** In `next_up()`'s `all` groups, each theme's idea entries with an `id` give
`"command": f"/sdlc:intent {' '.join(ids)}"` when there are two or more; the `--all` printer adds
the line under the theme.

**Many seeds.** `intent_ideas(text) = frontmatter_list(text, "idea") or []`, empty values
dropped; `intent_idea()` becomes `(intent_ideas(text) or [""])[0]`. `load_change` and
`_change_record` set `ideas` and `idea`. Ship loops `_seed_lines()`/`_drop_seed()` over each
value, from the last line up so earlier line numbers hold, after checking every value for the
refusal first. The readers in R6 change from `rec["idea"]` to `rec["ideas"]`.

## Contracts touched

- **Frontmatter read as text** (`frontmatter_list`): `idea: [a, b]` read as `depends_on:` is, never
  YAML, which would read a date-shaped id as a date.
- **A reference is an id or a title, matched by `ref_matches()`/`same_ref()`, never by title
  alone**: each value is matched on its own, as one is today.
- **Always Tier 2, what an existing frontmatter key means**: `idea:` gains a list form; every
  single-value intent, history's included, reads as before (R4). Retro reads closed intents with
  `_change_record`, which now yields `ideas`.
- **`stamp_shipped` edits lines in place**: the `idea:` line is untouched; an existing test covers
  it.
- **A nit is never put forward as a seed**: nits keep their own `nits` line in `ready` and never
  enter the theme command, which names ideas only.
- **`inbox-commit` never removes an entry an open change names**: `_open_claims()` covers every
  value of `ideas` (R6).

## Alternatives rejected

- **Inferring effort from the text, or asking for a size tag on each seed**: the seed asked for
  nothing tagged by hand, and kind, `Priority:` and placement already say who weighed an entry.
- **A separate skill for readiness**: status stays the one place that ranks the backlog; the groups
  are a printing split of what `next_up()` already computes.
- **A `theme:` frontmatter key ship expands to its seeds**: a theme's members change after the
  intent is written, so ship would delete seeds the change never considered.
- **Two lines, `idea:` and `ideas:`**: a second key for one meaning, and every reader reads two
  keys forever.

## Verification

```bash
uv run --group dev pytest -q tests/test_next_up.py tests/test_sdlc.py tests/test_inbox.py tests/test_skills.py tests/test_archive.py
uv run --quiet --script scripts/sdlc.py status          # Next up: "Ready to build: 2" then "Needs a decision: 25 (16 low)"
uv run --quiet --script scripts/sdlc.py status --all    # a theme with 2+ ideas shows "→ /sdlc:intent <id> <id>"
./check.sh
```
