---
id: 032
slug: process-guide-in-plugin
kind: spec
created: 2026-10-27
updated: 2026-10-27
---

# 032 — Keep the plugin's process guide in the plugin, and only a host's answers in .sdlc/ · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1. The guide moves.** `guide/process.md` and `guide/review.md` hold today's
   `defaults/SDLC.md` and `defaults/REVIEW.md`, rewritten as in R2. They are read in place from
   the installed plugin; setup never copies them.
2. **R2. Answer slots.** Each answer slot in `guide/process.md` is a block of its own (a heading
   or a `- **lead**` bullet) holding a generic default where one exists: the failure to stop and
   how it gets past, worktree needs, Stage 1 push-backs, the gate's prose, the path to users, the
   scans, the always-Tier-2 carve-out, the severity, cost, value and theme bullets, and the
   change-type table. A test asserts every `<` prompt in `defaults/SDLC.md` sits in a block whose
   `doc_units()` key `guide/process.md` also has; the same for `defaults/REVIEW.md` against
   `guide/review.md`.
3. **R3. Answers templates.** `defaults/SDLC.md` and `defaults/REVIEW.md` become the answers
   templates: only the blocks with prompts, plus a `>` note saying the file holds this repo's
   answers to the plugin's guide, read with it, each block standing in for or adding to the
   guide's block of the same heading. Both keep the shipped-docs shape (`test_defaults.py`, its
   glob extended to `guide/*.md`).
4. **R4. Config.** `config` gives `docs.process` and `docs.review` a `guide` path (absolute, in the
   running plugin) and a `layout`: `answers` when `.sdlc/setup.json` records that layout for the
   doc, `full` when it doesn't (every host set up before this change). With `full`, `guide` is
   `null`, and readers read the host doc alone, as today. A missing review gives the guide alone
   (`source: plugin`), replacing `doc_path()`'s fallback to `defaults/REVIEW.md`.
5. **R5. Readers.** Every skill and factory agent that reads `docs.process` or `docs.review` (bug,
   intent, retro, setup, ship, spec, triage; `reviewer-code`, `spec-writer`) reads `guide`, when
   set, then the host's doc, and says the rule once: a host block replaces the guide's block with
   the same heading or lead; any other host block is added after its parent's. A skills test
   asserts each names `guide`.
6. **R6. `severities()`** reads the host's `- **severity:**` bullet under Bugs when it has one,
   else the guide's (`guide/process.md`, not `defaults/`). Tested with an answers file with and
   without the bullet, and a full-layout host.
7. **R7. Setup's record.** `cmd_record()` writes, for `process` and `review`, `layout: "answers"`
   and a `guide` hash (`unit_hash` of the whole guide) in place of block hashes. `HEALTH`,
   `PROJECT` and `PRODUCT` are recorded as today.
8. **R8. `drift` for answers-layout docs** proposes no refresh. It reports `guide-changed` (with
   the guide's path) when the guide's hash differs from the record, and `unknown` (never
   breaking) for a host block whose key isn't a guide key or a child of one. For full-layout docs
   and for `HEALTH`, `PROJECT` and `PRODUCT`, it works as today. Each case is tested.
9. **R9. The migration.** A new read-only `sdlc.py answers <process|review>` prints, for a
   full-layout doc, the answers file it would become and `kept`/`cut` lists of block keys. A block
   is cut when its hash matches the recorded default's for that key or the guide's block now;
   every other block is kept, with its heading path. Setup shows it as a diff behind its one
   WAIT, writes it, then runs `record`, which marks the doc `layout: answers`. Tested for a host
   with a record and one without, and that a host's edited block is never cut.
10. **R10. Readiness** reports a full-layout process or review doc as `migrate`, a nudge, never a
    problem; `check --strict` doesn't fail on it.
11. **R11. The shim.** `.sdlc/deprecations.toml` gains `process-guide-split`, `remove_in =
    "1.6.0"`, naming `answers`, the `full` layout's branches in `config`, `drift` and
    `severities()`, and the readiness item.
12. **R12. Landing reach.** A landed change's paths under `guide/` count as live in
    `landing_reach()` (read at the next stage, nothing to do), never as `hosts`.
13. **R13. This repo migrates.** `.sdlc/SDLC.md` and `.sdlc/REVIEW.md` become answers files
    through `sdlc.py answers`, and `.sdlc/setup.json` is rerecorded. Two tests replace
    `test_this_repos_copy_keeps_the_defaults_sections` and
    `test_this_repos_review_keeps_every_default_failure_class`: every block key in this repo's
    copies is a guide key or a child of one, and no block is identical to the guide's.
14. **R14. Docs.** `AGENTS.md` replaces "This repo's process docs track the defaults" with R13's
    rule and names `guide/` beside `defaults/` and `templates/` under "Mechanism vs. policy";
    `docs/REFERENCE.md` and README describe the answers files, the guide, `layout` and the
    migration.

## Design

**Two files, one rule.** The guide is the plugin's account of the process; the host's file holds
only its answers. Both are cut by `doc_units()`, which already keys a block by its heading path, or
by its lead for a `- **lead**` bullet. A host block with a guide block's key replaces it; any other
follows its parent's guide block. Readers apply that while reading; nothing merges them on disk.
Setup already uses these keys, and `severities()` already does host-then-default.

**Slots.** The guide stops carrying `<` prompts. Where a host answers, it has a block of its own,
with a generic default where one makes sense (severity words, the nit rubric, change types) or a
line saying the host's answer goes here. The answers template carries the prompts in blocks with
the same keys, which R2's test pins.

**Layout lives in the record, not the text.** `.sdlc/setup.json`'s `docs.<key>.layout` says
whether a host's doc is answers or a full copy. `config` reads it, so no reader guesses from
content, and a host that never migrates keeps its full doc, read alone, until 1.6.0. After that a
full copy reads as answers that restate the guide, and `drift`'s `unknown` and R13-style checks
point at the blocks to cut.

**Migration is `drift`'s classifier, run once.** `answers` reuses `_classify()`'s inputs (the
recorded hashes, the default now) to decide plugin from host per block. Its output is text and
lists; setup shows and writes it after its WAIT, as it does a refresh today.

**Factory agents** read with `Read` and get paths from the build session's `config`: they follow
the same two paths, and their tools don't change.

## Contracts touched

- **"This repo's process docs track the defaults"** (`AGENTS.md`, `test_defaults.py`):
  **replaced on purpose** (R13, R14), by "this repo's copies hold only answers, checked against
  the guide". A policy edit made here with its reasoning: the old rule made each default edit
  twice and existed only because the copy carried the guide.
- **One shape for the shipped docs:** extended to `guide/*.md`; the answers templates keep it. A
  guide is never copied into a host, so its note may say what the plugin does.
- **Setup's record and `drift`:** `drift` gains `guide-changed` and an `unknown` key class, both
  reports. `breaking` is unchanged: no config key is retired and no template heading newly read,
  so `RETIRED_KEYS` and `TEMPLATE_READS` gain nothing. `record` writes something new for two
  docs; an old record reads as `full` (R4).
- **A shim gets its deprecation entry** (R11), and `cmd_release` refuses 1.6.0 while it remains.
- **Mechanism vs. policy:** the guide holds no host specifics; host text lives only in its file.
- **Confirm before writing:** the migration writes only behind setup's one WAIT; `answers` is
  read-only.
- **Narrow `allowed-tools`:** setup gains a rule for `sdlc.py answers`, as run; `answers` joins
  `READ_ONLY`.
- **`landing_reach`:** `guide/` is live (R12); a changed guide no longer asks hosts for setup.

## Alternatives rejected

- **A merged view printed by `sdlc.py guide`.** Rejected by the person: every skill runs another
  command, and the agents would need it in their tools.
- **Keeping the guide in `defaults/`.** `defaults/` means what setup copies; the guide is not.
- **Detecting the layout from the host doc's text.** A marker in prose, or guessing from
  headings; the record is the plugin's own state, and setup writes it anyway.
- **Severity words, change types and the nit rubric as config keys.** Prose with reasons a reader
  needs; as blocks they are answered like any slot, and `severities()` already parses one.
- **Migrating on `status` or automatically.** A write without a gate.

## Verification

- `uv run --group dev pytest -q tests/test_defaults.py tests/test_drift.py tests/test_setup_lifecycle.py tests/test_readiness.py tests/test_skills.py`,
  plus the new tests named under R2, R6, R8, R9 and R13.
- `./check.sh` passes.
- In a scratch repo set up at 1.4.0, `sdlc.py answers process` keeps a filled prompt and an
  edited bullet and cuts untouched plugin text; setup writes it, and `config` reports
  `layout: answers` with a `guide` path.
- In this repo, `.sdlc/SDLC.md` shrinks to its answers, and `config` names `guide/process.md`.
- `wc -l defaults/SDLC.md` falls from 499 to under about 80: a new host's setup diff for the
  process doc.
