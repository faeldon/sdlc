---
id: 060
slug: rework-as-declared-fix
kind: spec
created: 2026-11-16
updated: 2026-11-16
---

# 060 — Rework as a declared fix, with surviving lines as the cross-check · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1.** An intent's `reworks:` line is read as text (`frontmatter_list()`), like `depends_on:`;
   `load_change()` keeps the ids as `reworks` and records an error for a value that isn't a change
   id or names the change itself. Tests pin both errors and the inline and block forms.
2. **R2.** `check --strict` refuses a `reworks:` id naming no closed, dropped or open change,
   walking history only when some open change has one, as it already does for a bug's
   `Introduced by:`. A test pins the refusal and that an id naming a closed change passes.
3. **R3.** Retro's `rework` lists declared links from changes closed in the window:
   `{"change", "reworks", "days", "via": ["reworks"]}`, the earlier change anywhere in history
   (before the window, or dropped: `dropped: true`), whatever the gap. An id naming no change is a
   `problems` line. A test pins a declared link 20 days apart.
4. **R4.** A bug fixed in the window (its `Sdlc-Fixes:` line on the fixing change's `Close`) whose
   `Introduced by:` names a change makes the same link, `via: ["bug <id>"]`; one pair declared both
   ways is one entry with both reasons. A test pins the merge.
5. **R5.** Retro's new `rework_questions` lists the pairs blame finds and no declared link covers:
   for each change closed in the window, the lines its diff removed or replaced (the old side of
   `git diff -U0 <base> <sha>`, change folders and the register left out), blamed at its base, each
   blamed commit matched to an earlier change in the window (the commits between that change's
   base and its `sha`): `{"change", "touches", "files", "lines"}`. Tests: appending to a file an
   earlier change wrote yields nothing; replacing its lines yields one question; with a `reworks:`
   link the same replacement yields no question and one rework entry.
6. **R6.** File-pair rework, `REWORK_DAYS`, `REWORK_COMMON_SHARE`, the `rework_common` key and the
   `every_change` exclusion go; their tests are replaced by R3–R5's.
7. **R7.** `/sdlc:intent` Step 1 asks, when the Problem traces to an earlier change, which
   change(s) it reworks; Step 3 shows the `reworks:` line, Step 5 writes it under `depends_on:`. No
   new stop: it's part of the interview. A test asserts the text.
8. **R8.** Retro's skill text describes `rework` (declared, `via`) and `rework_questions`
   (questions to raise, never counted), and its architecture and process passes no longer cite
   `rework_common` (hotspots and `co_change` carry that weight). A test asserts `rework_common` is
   in no skill.
9. **R9.** `templates/intent.md`, `TEMPLATE_READS` and `drift` are unchanged: `reworks:` is written
   by the skill when asked, as `fixes:` and `closes:` are. Nothing reaches a host through setup.
10. **R10.** `stamp_shipped` leaves a `reworks:` line as written; a test pins it.
11. **R11.** `AGENTS.md` (the retrospectives paragraph), `docs/REFERENCE.md` (retro's rework,
    intent frontmatter keys), and `guide/process.md` only if its account of rework says "shared
    files".
12. **R12.** `./check.sh` exits 0.

## Design

**Frontmatter.** `reworks(text)` mirrors `depends_on()`. `load_change()` validates it as it does
`depends_on`. `check` collects `reworks` ids across open changes and, when any, reuses the lazy
`closed_changes(..., read=False)` walk it makes for `Introduced by:`, plus
`dropped_changes(..., read=False)` names.

**Declared links.** `closed_changes(read=True)` already reads each closed intent at its commit; it
gains `reworks` as it reads `idea`. In `retro()`, each in-window change's `reworks` is resolved by
`names_change()` against `closed_changes(home, None, …)` and the dropped changes; bug links come
from the fixed bugs `bugs_retro()` reads from `Sdlc-Fixes`, with the fixing change's name. Links
merge by `(change, reworks)`, `via` reasons unioned.

**Blame cross-check.** For each in-window change with a known base (`_change_base()`):
`git diff -U0 --no-renames <base> <sha>` → old-side hunks `-a,b` with `b > 0`; per file,
`git blame --porcelain -L a,+b … <base> -- <file>` → the commit of each removed line; a commit is
owned by the in-window change whose `git rev-list <base>..<sha>` holds it (built once). Hits group
by pair; pairs a declared link covers drop out. Cost is bounded by the window and by removed lines
only, so appends cost nothing. Parsing (`removed_ranges(text)`, `blame_commits(text)`) is pure, in
`indicators.py`.

**Skills.** `skills/intent/SKILL.md` Step 1, in **Affected** beside the `depends_on:` ask: "Ask too
whether the problem traces to an earlier change: each one goes on a `reworks:` line,
`reworks: [041]`, which retro counts as rework." Step 5 writes it with the other frontmatter lines.
`skills/retro/SKILL.md`: the `rework` bullet and the pass text citing `rework_common` rewritten.

## Contracts touched

- **Frontmatter read as text** (`frontmatter_list`, never YAML): `reworks:` exactly as
  `depends_on:`.
- **`stamp_shipped` edits lines in place**: untouched; R10 pins it leaves the new line alone.
- **`fixes:` keeps its meaning** (inbox bugs); `reworks:` is apart, and R4 reads `Introduced by:`
  only.
- **Always Tier 2, "a change to what something a host already has means"**: retro's `rework`
  changes meaning and its `rework_common` key goes. Hosts' past direction docs quoted the old
  figure; the first retrospective after the update reads a different signal, which the retro
  skill's text says.
- **Metrics trailers**: `Sdlc-Rework`, `Sdlc-Fixes`, `Sdlc-Base` are read, never changed.
- **`indicators.py` is pure**: the new parsers take git's text, no subprocess.
- **Windows**: the new git calls go through `_git`; paths compared as git prints them, all with
  git's default quoting (059's lesson).
- **Intent's WAIT** unchanged; the question is inside the interview.
- **Templates**: none changed (`templates/` is irreversible), R9.

## Alternatives rejected

- **Keeping the file pairs as a fallback**: they are the noise this removes.
- **Counting blame hits**: a planned follow-up replacing a first draft isn't a fix; hits stay
  questions.
- **A commented `# reworks:` line in `templates/intent.md`**: reaches every host irreversibly for a
  key most intents never need; `fixes:` and `closes:` have none either.
- **`check` validating only the id's shape**: a wrong id would silently drop a declared link, and
  the walk `Introduced by:` already makes is cheap to reuse.
- **`git log -L` per earlier change**: walks forward from every earlier hunk; blaming what later
  changes removed reads less.

## Verification

```bash
uv run --group dev pytest -q tests/test_retro.py tests/test_sdlc.py tests/test_skills.py tests/test_indicators.py
uv run --quiet --script scripts/sdlc.py retro | jq '{rework: (.rework|length), questions: (.rework_questions|length)}'   # this repo: 0 declared, a few questions, from 50 pairs
./check.sh
```
