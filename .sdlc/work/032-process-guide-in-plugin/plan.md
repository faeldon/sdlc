---
id: 032
slug: process-guide-in-plugin
kind: plan
created: 2026-10-27
updated: 2026-10-27
---

# 032 — Keep the plugin's process guide in the plugin, and only a host's answers in .sdlc/ · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Context

Setup copies all of `defaults/SDLC.md` (499 lines) and `defaults/REVIEW.md` (69) into a host,
though only the `<` prompts and a few settings are the host's; `drift()`'s three-way block compare
exists mostly to carry plugin updates past a host's ~30 lines. The spec
(`.sdlc/work/032-process-guide-in-plugin/spec.md`, R1–R14) moves the guide to `guide/`, read in
place; makes `defaults/SDLC.md` and `defaults/REVIEW.md` short answers templates; has `config`
give each reader the guide's path and the host's, with `layout` from `.sdlc/setup.json`; adds a
read-only `sdlc.py answers` that setup uses to migrate a full copy once (a shim, `remove_in
1.6.0`); and migrates this repo.

**Combining rule** (stated once in `guide/process.md`'s note and in each reader): host blocks are
`doc_units()` blocks; one whose key equals a guide block's key replaces it, any other is read after
its parent's guide block.

## Files to change

- `guide/process.md` (new): today's `defaults/SDLC.md`, prompts replaced by slot blocks (R2).
- `guide/review.md` (new): today's `defaults/REVIEW.md`, its note saying hosts add failure classes.
- `defaults/SDLC.md`, `defaults/REVIEW.md`: rewritten as answers templates (R3).
- `scripts/sdlc.py`:
  - `GUIDE_DIR = PLUGIN_DIR / "guide"`, `GUIDES = {"process": "process.md", "review": "review.md"}`.
  - `doc_path()` (422) → takes the manifest's layout: for `process`/`review` adds `guide` and
    `layout`; the review fallback becomes `GUIDE_DIR / "review.md"`. Callers: `cmd_config` (484),
    the skill-size reader (~4320), `cmd_readiness` (~5904).
  - `doc_layout(root, key) -> "answers" | "full"` reading `read_manifest()` (6089).
  - `severities()` (1268): host's bullet first, then `GUIDE_DIR / "process.md"`.
  - `cmd_record()` (~6105): gains `--answers process,review`, which setup passes after writing
    answers files (fresh setup or migration); those keys record
    `{"path", "layout": "answers", "guide": hash}`. Without it a key keeps the layout the manifest
    already has, and a full doc keeps today's block hashes until migrated.
  - `drift()` (6227): for an answers-layout process/review doc, no `_classify`; report
    `guide-changed` when the hash differs, `unknown` for a key not in the guide (nor a child).
  - `answers_for(root, key) -> dict` + `cmd_answers`: for a full doc, `doc_units` of the host,
    cut a block when `unit_hash` equals the manifest's recorded hash for that key or the guide's
    block now; output `{"text", "kept", "cut"}`. Parser `answers {process,review}`; `READ_ONLY`
    gains `answers`.
  - readiness: `docs.process`/`docs.review` item status `warn` with "migrate: `/sdlc:setup`" when
    layout is `full` (never required).
  - `landing_reach()` (3050): `parts[0] == "guide"` → `scripts = True` (live).
  - `HOST_DOCS` stays; a `GUIDED = ("process", "review")` set marks the two that split.
- `.sdlc/deprecations.toml`: `process-guide-split`, `remove_in = "1.6.0"`.
- Skills: `bug`, `intent`, `retro`, `setup`, `ship`, `spec`, `triage` — where they read
  `docs.process`/`docs.review`, read `guide` first when set, with the combining rule in one
  sentence. `setup`: fill the answers template's prompts; for a `full` doc, run
  `sdlc.py answers <key>`, show the diff and the `kept`/`cut` lists under its WAIT, write, record;
  plus its `Bash(...)` rule.
- Factory agents `reviewer-code.md`, `spec-writer.md`: same reading rule.
- `.sdlc/SDLC.md`, `.sdlc/REVIEW.md`, `.sdlc/setup.json`: migrated through `answers` + `record`.
- Tests:
  - `tests/test_defaults.py`: glob adds `guide/*.md` to shape checks (guide notes exempt from
    `HOST_COPY_RE`); new `test_every_prompt_sits_in_a_guide_slot` (R2); replace the two
    `OWN_COPIES` tests with `test_this_repos_answers_are_guide_keys` and
    `test_this_repos_answers_restate_no_guide_block` (R13); the seed-kinds test reads
    `guide/process.md` and `.sdlc/SDLC.md` combined.
  - `tests/test_playbook.py`: `DOC` → `guide/process.md`.
  - `tests/test_config_resolution.py`: review fallback path, `guide`/`layout` in config (R4).
  - `tests/test_setup_lifecycle.py`: existing three-way drift tests move to a full-layout record
    (unchanged behaviour); new tests for answers-layout drift (`guide-changed`, `unknown`), record
    writing `layout`, `answers` keep/cut with and without a record, edited block never cut (R7–R9).
  - `tests/test_bugs.py`: `severities()` with answers file with/without bullet, full layout (R6).
  - `tests/test_readiness.py`: `migrate` warn, `check --strict` unaffected (R10).
  - `tests/test_archive.py` (768–790): `guide/` paths read as live, `defaults/` still `hosts` (R12).
  - `tests/test_skills.py`: each reader names `guide` (R5); setup's rule for `answers`.
  - `tests/test_deprecations.py`: passes with the new shim.
- Docs: `AGENTS.md` (Mechanism vs. policy names `guide/`; the "process docs track the defaults"
  invariant → R13 rule; Setup's record paragraph mentions `layout`), `docs/REFERENCE.md`, README.

## Work order

1. **Guide and slots (R1, R2, R3).** `git mv defaults/SDLC.md guide/process.md`, same for review;
   carve each prompt into its own slot block with a generic default; write the two answers
   templates; extend `test_defaults.py` (shape glob, slot test), `test_playbook.py`. Stop: those
   tests pass; nothing reads `guide/` yet, so the suite still passes except tests pinning
   `defaults/SDLC.md` content, fixed here.
2. **Config and severities (R4, R6).** `GUIDE_DIR`, `doc_layout`, `doc_path` additions, the review
   fallback, `severities()`. Tests in `test_config_resolution.py`, `test_bugs.py`. Stop: suite.
3. **Record and drift (R7, R8).** `cmd_record` layout + guide hash; `drift` branch for answers
   layout; move existing drift tests to full layout explicitly. Stop: `test_setup_lifecycle.py`,
   `test_defaults.py` RECORD_CLEARS tests.
4. **Migration (R9, R10, R11).** `answers_for`/`cmd_answers`, `READ_ONLY`, readiness item,
   deprecation entry. Tests. Stop: suite.
5. **Readers (R5, R12).** Skills, agents, setup's migrate step and rule; `landing_reach`.
   `test_skills.py`, `test_archive.py`. Stop: suite.
6. **This repo (R13, R14).** Run `uv run --quiet --script scripts/sdlc.py answers process|review`
   from the worktree, review the kept/cut lists, write `.sdlc/SDLC.md`/`REVIEW.md`, run `record`;
   replace the OWN_COPIES tests; docs. Then `./check.sh`; `drift` must report nothing breaking
   or refreshable here.

## Tests

By requirement: R1/R2/R3 `test_defaults.py` (shape, slots), `test_playbook.py`; R4
`test_config_resolution.py`; R5 `test_skills.py`; R6 `test_bugs.py`; R7/R8/R9
`test_setup_lifecycle.py`; R10 `test_readiness.py`; R11 `test_deprecations.py`; R12
`test_archive.py`; R13 `test_defaults.py`; R14 manual read of the three docs at ship. End to end:
`test_adoption.py` keeps passing (it copies `defaults/REVIEW.md` into a scratch repo — now an
answers template — and must still close a change).

Manual: in a scratch repo copied with 1.4.0's `defaults/SDLC.md` and a `setup.json` recorded then,
`sdlc.py answers process` keeps a filled prompt and an edited bullet, cuts untouched text.

## Rollback

`git revert` of the change's commits restores `defaults/`, the script and this repo's docs. Not
covered: a host that ran `/sdlc:setup` on this version has answers-only docs and a `layout:
answers` record; on a reverted plugin those docs read as a (short) full copy. Recovery there is
`/sdlc:setup reset process` (and `review`) on the reverted plugin, which puts the full default back
after a diff.

## Decided while planning

`record` must not infer the layout from the doc's text. Setup passes `--answers process review`
after writing answers files, so the layout stays the record's (as the spec says), with setup its
only writer. Setup's skill gains that argument on its existing `record` rule.

## Where the build departed

- **The factory's agents don't read the guide (R5).** Their cached copy has no `sdlc.py` and
  can't reach the `sdlc` plugin's `guide/`. They carry the generic passes themselves, and now
  read the host's review doc as what the repo adds; `test_skills.py` pins that wording.
- **Readiness says `warn`, its detail starting `migrate:` (R10)**, rather than a new status, so
  setup's reading of `ok`/`warn`/`missing`/`n/a` is unchanged.
- **A full copy drifts against the guide**, not `defaults/`: `_copy_source()` names what each doc's
  copy was taken from, which for the process and review docs is now the guide.
- **A heading with nothing under it is structural**: it stands in for nothing. Written into the
  guide's note, the templates' notes and the R13 test, since without it a host's `## Running the
  stages` would replace the guide's.
- **This repo's answers were placed by hand** in the new slots, from what `answers` kept: the
  tool keeps a block under its old key, so a filled prompt stays in its old section rather than
  moving to its slot (`notes.md`).
