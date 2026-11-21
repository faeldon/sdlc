---
id: 207
slug: change-origin
kind: spec
created: 2026-11-21
updated: 2026-11-21
---

# 207 — A change records where its finding came from · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

No nit is taken in: the intent names none.

Assumptions checked in the code before designing: a closed change's record is built by
`_change_record()` (`scripts/sdlc.py`) from the intent at the `Close` commit's parent, the same way
`serves:` and `fixes:` are read, so the retrospective can read a new frontmatter key from history
with no new walk. `parse_trailers()` (`scripts/metrics.py`) reads `Sdlc-Origin: host` today as
`{"origin": {}}`: a single word with no `=` becomes a name with no fields, and it lands in the
`else` branch, so the value would be lost without R6. `fix_trailers()` (`scripts/closing.py`) is
the one place close builds a trailer from the intent, and `_step_remove_folder()` is where those
lines join the `Close` commit. Entry body lines are read only through `BODY_KEYS` and `BODY_RE`.
`tests/test_feature_map.py` collects every `"Sdlc-<Key>` string the code writes and fails when
`docs/FEATURES.md` doesn't name it.

1. **R1. Two values, one constant.** `sdlc.py` defines `ORIGINS = ("host", "self")`. `host` means
   the finding came from using what this repo makes in another repo. `self` means it came from
   working on this repo, a retrospective, a review finding or a nit included. No other value is
   valid. Test: `test_origin_values_are_host_and_self` (`tests/test_sdlc.py`) pins the tuple.
2. **R2. An open change's `origin:` is checked, and a missing one is fine.** `load_change()` reads
   `origin:` with `frontmatter_list()` into `rec["origin"]`: None when the line is absent or empty,
   otherwise its one value. A value not in `ORIGINS`, or more than one value, is an error in
   `rec["errors"]`, so `check` and `vet --strict` report it. A missing line adds no error.
   Tests (`tests/test_sdlc.py`): `test_vet_strict_passes_a_change_with_no_origin`, which fails if a
   missing line is refused, and `test_an_origin_outside_host_and_self_is_an_error`, which fails if
   `origin: elsewhere` or `origin: [host, self]` passes.
3. **R3. A closed change's record carries its origin, as text, unknown when unset.**
   `_change_record()` sets `rec["origin"]` to `host` or `self` from the intent's `origin:` line and
   to None otherwise (missing, empty or invalid). It never infers a value from `idea:`, `fixes:`,
   `closes:` or anything else. Test: `test_a_closed_change_without_origin_reads_none`
   (`tests/test_sdlc.py`) builds a history where one change has `origin: host`, one has
   `origin: self` and one has no line, and asserts `host`, `self` and None. It fails if the third
   reads as `self`.
4. **R4. Close writes `Sdlc-Origin` on the `Close` commit.** `origin_trailer(main, branch)` in
   `scripts/closing.py`, next to `fix_trailers()`, reads the intent at
   `{branch}:{work_rel}/{branch}/intent.md` and returns `["Sdlc-Origin: host"]` or
   `["Sdlc-Origin: self"]` for a valid value, and `[]` for no line, an invalid value, or any
   exception. It never raises. `_step_remove_folder()` appends its lines to the trailers it passes
   `_close_commit()`, after the `Sdlc-Fixes` lines. Test: `test_close_writes_an_origin_trailer`
   (`tests/test_archive.py`) closes a change with `origin: host` and finds `Sdlc-Origin: host` in
   the `Close` commit's body. It fails if the line is missing.
5. **R5. No origin, no trailer. A rerun or a drop writes none.** A change with no `origin:` line
   closes with no `Sdlc-Origin` line. A close rerun after the `Close` commit exists writes no
   second one, because `_close_commit()` already returns early when the folder is gone. A `Drop`
   commit carries none. Tests (`tests/test_archive.py`):
   `test_a_change_without_origin_closes_without_the_trailer`, and
   `test_a_dropped_change_carries_no_origin_trailer` (in the shape of the existing
   `"Sdlc-Fixes:" not in body` check on a `Drop` body).
6. **R6. `parse_trailers()` reads `Sdlc-Origin` back as text.** `origin` joins `mode`, `coverage`
   and `base` as a key whose value is kept as text, so `parse_trailers("Sdlc-Origin: host")` gives
   `{"origin": "host", ...}`. Every other key parses as it does today. Test:
   `test_parse_trailers_reads_origin_as_text` (`tests/test_metrics.py`) fails on the `{}` it reads
   today.
7. **R7. The metrics contract is extended in its docstring.** `scripts/metrics.py`'s module
   docstring gains a paragraph that names `Sdlc-Origin: <host|self>`. It says close writes it from
   the intent's `origin:` line on `Close` commits only. It says a `Close` commit without it was
   closed before origins were recorded, or named none: unknown, never `self`. No existing
   paragraph changes. Test: the existing `tests/test_feature_map.py` check fails until
   `docs/FEATURES.md` names `Sdlc-Origin` (R12).
8. **R8. The retrospective counts the window's changes by origin.** `retro()` returns `origins`:
   `{"host": [names], "self": [names], "unknown": [names], "n": <closed changes in the window>}`,
   built from each closed change's `rec["origin"]` (R3). Dropped changes are not counted.
   `unknown` holds every change with no valid line, so a window from before this change reads as
   all unknown, never as all `self`. Test: `test_retro_counts_changes_by_origin`
   (`tests/test_retro.py`) closes one `host`, one `self` and one change with no line inside one
   window, then asserts the three lists and `n == 3`. It fails if the unset one is counted as
   `self`, or if a change from before the window is counted.
9. **R9. Retro's skill reads `origins` without naming any repo's goals.** `skills/retro/SKILL.md`
   describes `origins` in its list of figures. It reads the `host` changes as evidence from use in
   another repo, to set against any goal, milestone or bet the direction and product docs say waits
   on such evidence, citing the count and the `unknown` beside it. When every change in the window
   is `unknown`, the report says nothing about origins, so a host that never sets the line reads as
   it does today. The skill names no goal id and no bet of this repo. Test:
   `test_retro_skill_reads_origins` (`tests/test_skills.py`) asserts the skill names `origins` and
   that its text holds no `G<n>` id near it. It fails if the wording is pinned to this repo's
   direction doc.
10. **R10. `/sdlc:intent` proposes the line and asks no new question.** Step 1 proposes `origin:`
    the way it proposes `serves:`. It takes the value from the seed's or bug's `Origin:` line
    first, then from what the person said, and marks it `inferred` as `self` when nothing points at
    a host. Step 3 shows it with its source in a comment
    (`origin: host  # proposed from 2026-11-20-3`). Step 4's question names it: `, found in a host`
    or `, found here`, after the `serving` clause, in the single, factory and batch forms alike.
    Step 5 writes `origin: <value>` alone under `depends_on:` with the other approved lines.
    `edit a section` is how the person changes it. Test: `test_intent_proposes_an_origin`
    (`tests/test_skills.py`) asserts `skills/intent/SKILL.md` names `origin:`, both clauses and
    `Origin:`. It fails if Step 4's question drops the clause.
11. **R11. `/sdlc:idea` and `/sdlc:bug` write `Origin: host` when the account says so.** Each
    skill's Step 3 entry shape gains `Origin: host`, shown only when the person's account says the
    finding came from another repo. It is never written as `self`, and never names the repo,
    following the skills' existing "names no host" rule. `BODY_KEYS` gains `"Origin"`, so
    `parse_entries()` reads it into `fields`. Tests: `test_an_entry_reads_its_origin_line`
    (`tests/test_sdlc.py`) fails if `fields["Origin"]` is missing for an entry holding the line.
    `test_idea_and_bug_offer_an_origin_line` (`tests/test_skills.py`) fails if either skill's entry
    shape lacks it.
12. **R12. The docs say what the code now does.** `docs/REFERENCE.md`: *Metrics* names
    `Sdlc-Origin`, *Retrospectives* names `origins`, the intent's frontmatter keys list `origin:`
    with its two values and that missing means unknown, and the register's body lines list
    `Origin:`. `docs/FEATURES.md` gains an `Sdlc-Origin` bullet (what fails without it:
    `tests/test_feature_map.py`) and the `origin:` key, each with the file that specifies it.

## Design

**One key in the intent, read in three places.** The intent's frontmatter is the single source:
`origin: host` or `origin: self`, read as text with `frontmatter_list()` and never through YAML.
`ORIGINS` in `sdlc.py` is the only list of valid words. `closing.py` reads it as `sdlc.ORIGINS`
through its existing binding. `metrics.py` stays pure and doesn't need the list, because it only
keeps the trailer's text.

- **Open changes** (`load_change()`, R2): `rec["origin"]` is set beside `rec["serves"]`, with an
  error for a bad value. `check` and `vet` report it the way they already report a bad `impact:`.
  A missing line is never an error, so every existing change and every host passes as it does today.
- **Closed changes** (`_change_record()`, R3): `rec.update(...)` gains `origin=None`. Then, after
  the intent is read, `rec["origin"]` is set to the line's value when it is in `ORIGINS`. Dropped
  changes come through the same function and get the field too, though R8 doesn't count them.
- **Close** (`origin_trailer()`, R4–R5): a sibling of `fix_trailers()` with the same shape. It
  reads the intent from the branch, returns lines, and returns `[]` on any failure. It is called
  in `_step_remove_folder()` and nowhere else, so `_step_record()` (a drop) never gets it. The
  trailer sits in the trailer block git reads, after `Sdlc-Base` and `Sdlc-Fixes`.
  `_close_commit()`'s early return on a folder `main` no longer tracks is what keeps a rerun from
  writing it twice. Nothing new is needed for that.
- **Reading it back** (`parse_trailers()`, R6): `("mode", "coverage", "base")` becomes
  `("mode", "coverage", "base", "origin")`. That is the whole parser change.
- **The retrospective** (R8): a small pure helper in `scripts/retro.py`, `_origins(changes)`, maps
  the window's closed changes (`f["changes"]`, already read with their intents) into the three
  lists and `n`. `retro()` adds `"origins": _origins(changes)` to its return dict. It reads the
  intent's value through the record, not the trailer (see *Alternatives rejected*). The trailer
  agrees with it by construction, because close writes it from the same line.
- **The seed** (R11): `BODY_KEYS` gains `"Origin"`. The skills write `Origin: host` only. When an
  intent takes a seed or bug, Step 1 of `/sdlc:intent` reads `fields["Origin"]` from the entry it
  already reads for `Theme:` and `Issue:`, and proposes `origin: host`.
- **The skills** (R9–R11) change prose only: no new command, no new `Bash(...)` rule, no new config
  key in `READS_CONFIG`, no second WAIT. Intent's Step 4 question gains one clause. Nothing is
  written before the yes, as now.

**Edge cases.** A seed with `Origin: host` taken into an intent the person then says came from this
repo: the person's word wins through `edit a section`, and the intent holds `self`. A change taking
several seeds where any says `Origin: host` gets `host` proposed, with the seed named in the
comment. An invalid value on a change already closed reads as unknown in the retrospective and gets
no trailer. It is never "corrected". History is never backfilled: older `Close` commits have no
trailer, and their intents have no line.

## Contracts touched

- **Mechanism vs. policy.** The plugin knows nothing about what a host builds. The two words are
  generic ("found using what this repo makes, elsewhere" against "found here"). Retro's skill reads
  `host` changes against whatever goal or bet the host's own direction and product docs name. It
  never names G7 or this repo's first bet (R9). The mechanism is in `sdlc.py`, `closing.py`,
  `metrics.py` and `retro.py`. The judgement (which value to propose) is in the skills.
- **Frontmatter is read as text** (`frontmatter_list()`). Every read of `origin:` goes through it,
  including the one in `closing.py`. `stamp_shipped` is untouched, and Step 5 adds the line by
  `Edit`, as it does `serves:`.
- **The metrics trailer contract: extend, never redefine.** One new key, one new docstring
  paragraph, and `origin` added to the text-valued keys in `parse_trailers()`. No existing key's
  format or reading changes. The paragraph says a missing line is unknown, matching the docstring's
  "unrecorded, never none" phrasing.
- **`templates/` is `[review] irreversible`.** The design doesn't touch `templates/intent.md`. The
  template doesn't carry `serves:`, `fixes:`, `closes:` or `reworks:` either: the skill adds each
  when it has a value. So no host's overridden template goes stale, and `TEMPLATE_READS`,
  `drift()` and `sdlc.py record` don't come into play.
- **Nothing about a project or a workspace.** The value is a class, `host`, and never a name: not
  in the intent, the entry, the trailer or the report. Test data uses neutral examples
  (`reopen-drafts`). A per-host label is out of scope (see the questions below).
- **Retro's `unmeasured`, never `unused`.** A change with no line is `unknown`, a list of its own,
  never folded into `self` (R3, R8). The report stays silent when everything is unknown (R9).
- **Closing.** The trailer joins the existing `Close` commit under the same `_main_lock()`, adds no
  git step and no new failure: `origin_trailer()` never raises, like `fix_trailers()`. A rerun
  resumes as before.
- **The register.** `Origin:` is a body line like `Theme:`, written by `/sdlc:idea` and `/sdlc:bug`
  through `inbox-commit` as today. Release, publish and measuring still never read the register:
  the retrospective reads origin from the intent, not from the entry.
- **Skills invariants** (`tests/test_skills.py`). No new bash, no new rule, one WAIT each as
  before, and the question still asks in a dialog. Intent's question text changes, so any eval case
  or fixture that quotes it must be checked. `tests/test_evals.py` builds every fixture under
  `vet --strict` in the gate, and R2 keeps a fixture without the line passing.
- **A doc's claim the change made false** (REVIEW.md). REFERENCE.md's *Metrics* and
  *Retrospectives*, its list of intent keys, its list of register body lines, and FEATURES.md are
  each updated in the same change (R12). `AGENTS.md`'s map doesn't name the trailer list or the
  intent keys, so it doesn't change.

No invariant needs to move.

## Alternatives rejected

- **Retro reads the `Sdlc-Origin` trailer instead of the intent.** `Sdlc-Fixes` is a trailer
  because the register loses the bug entry at ship. The intent is never lost: `closed_changes()`
  already reads it at the `Close` commit's parent. Reading the record keeps one source, works for a
  change closed by any plugin version, and doesn't let a measuring hiccup decide an origin. The
  trailer is still written, as the intent asks, so `git log` on the base branch shows the origin
  without opening the change's commit, and outside tools can grep for it.
- **Inferring the origin.** For example, `closes:` set meaning `host`, or a nit-born change meaning
  `self`. That is a guess written into history. A filed issue's own axis is already recorded by
  `closes:` and `Sdlc-Triaged`. The intent rules out guessing.
- **A third value, `issue`.** Whether someone filed an issue is already on `closes:`. A filed
  issue's finding came from a host or from here like any other, so `issue` would mix two axes and
  make the counts overlap.
- **A frontmatter key in `templates/intent.md`.** That would put an irreversible-path edit, a
  `drift` and `record` cycle, and stale host overrides into the change to show an empty line every
  host would have to leave blank. The skill writes it like `serves:`.
- **A config switch (`[retro] origins = true`) to turn the line on.** That is a new key, a new
  setup question and a new `READS_CONFIG` entry, which conflicts with the intent's "no new
  question". Whether hosts should see the line at all is left to the person (below). The switch is
  the way to do it if the answer is "this repo only".
- **Counting seeds by origin in the retrospective.** The intent's Outcome counts landed changes. An
  open seed's origin is read when an intent takes it, and shows up in the count once that change
  lands. A register count can be added later without changing anything here.
- **Editing `.sdlc/DIRECTION.md`'s G7 sentence in this change.** Only `cmd_retro_commit` writes the
  direction doc. The next retrospective, reading `origins`, is what retires that sentence.

## Verification

```bash
./check.sh
```

Healthy output: ruff check and `ruff format --check` clean, `pytest -n auto` all passed (including
the new tests named in R1–R11 and the existing `tests/test_feature_map.py`), and
`claude plugin validate --strict` passes.

```bash
uv run --group dev pytest -q tests/test_archive.py -k origin
uv run --group dev pytest -q tests/test_metrics.py::test_parse_trailers_reads_origin_as_text
uv run --group dev pytest -q tests/test_retro.py::test_retro_counts_changes_by_origin
uv run --group dev pytest -q tests/test_sdlc.py -k origin
uv run --group dev pytest -q tests/test_skills.py -k origin
uv run --group dev pytest -q tests/test_evals.py tests/test_adoption.py tests/test_feature_map.py
```

Healthy: every selection passes. `test_evals.py` and `test_adoption.py` show that a change with no
`origin:` line still runs from `new` to `close` and passes `vet --strict`.

By hand, in a scratch repo after the change lands: close a change with `origin: host`, then
`git log -1 --format=%B <base>` shows `Sdlc-Origin: host` in the trailer block, and
`sdlc.py retro`'s JSON shows that change under `origins.host`.

Boundaries. **Always:** read `origin:` as text, write the trailer only for a valid value, count a
missing line as unknown. **Ask first:** any change to the intent Step 4 question beyond the one
clause, and any edit to `templates/`. **Never:** name a host anywhere, infer or backfill an origin
into history, refuse a change for a missing line, or edit the direction or product doc from this
change.

