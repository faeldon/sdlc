---
id: 036
slug: review-depth-by-risk
kind: plan
created: 2026-11-03
updated: 2026-11-03
---

# 036 — Review depth set by what a change touches · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

Two refinements of the spec, agreed or found while planning. R9's paragraph is **`How to
recover:`**, naming for each irreversible path either the command that reverses it or "fix
forward: …" (the follow-up change and release, such as a new release plus `/sdlc:setup` in each
host), and the WAIT clause reads `with how to recover it shown`. And
`test_sdlc_loads_nothing_from_plugins` asserts the repo root has no `agents/`; its point is that
`sdlc`'s default scans never reach `plugins/factory/`, which a root `agents/` holding only `sdlc`'s
own agent keeps true, so the test is narrowed to say that.

## Files to change

- `scripts/sdlc.py`:
  - `CONFIG_KEYS["review"] = {"sensitive": [], "irreversible": []}`, both in `LIST_KEYS`, so
    `load_config()` validates them like `version_files` (R1).
  - `risk_paths(paths, patterns)`: a `/`-suffixed prefix, else `fnmatch.fnmatchcase` (R2).
  - `_risk_report(root, path)`: the diff's paths from `changed_paths(checkout_of(path), trunk)`,
    both sides of a rename, as `_nits_report()` builds them; `sensitive`, `irreversible`, `deep`;
    a `risk` part in `cmd_preflight()` (R3).
  - `ship_question(..., sensitive, irreversible, fresh_skipped)`: `touching sensitive paths a, b
    and c` (five, then `and N more`), `with how to recover it shown`, `without the fresh review
    (<why>)`; `cmd_ship_question()` computes the first two from `_risk_report()`, the third from
    `--fresh-skipped` (R4, R8, R9).
  - `FINDING_KEYS` gains `By`; `findings_entries()` reports a `By:` other than `fresh`;
    `findings_trailer()` appends `fresh=` and `fresh_wrong=`; `_add_findings()` sums them only
    from trailers carrying them (R7).
  - `landing_reach()`: root `agents/*.md` reported under `agents` as `sdlc:<name>` (R11).
- `agents/reviewer.md` (new): `name: reviewer`, a description saying when not to use it,
  `tools: Read, Grep, Glob`; read-only, the guide's reporting rules, sections in `findings.md`'s
  shape with `By: fresh` (R6).
- `skills/ship/SKILL.md`: Step 0's `risk` part; Step 2 runs the build on a deep diff whatever
  `build_when` says; Step 3 spawns `sdlc:reviewer` on a deep diff and merges its findings
  (`By: fresh`, an unconfirmed one proposed `wrong` with why) or records the skip; Step 4 drafts
  `How to recover:` when `irreversible` is set; Step 5 passes `--fresh-skipped`; `Agent` in
  `allowed-tools`; names `review.sensitive` and `review.irreversible` (R4, R6–R9).
- `skills/setup/SKILL.md`: a gap question for both lists, with candidates it finds (R10).
- `templates/findings.md`: the `By:` line in the note.
- `guide/review.md`, `guide/process.md`, `docs/REFERENCE.md`, `AGENTS.md` (R12); `record` after
  the guide edits.
- `.sdlc/config.toml`: R13's lists for this repo.
- `.sdlc/work/inbox.md` at ship: 2026-11-03-5 and -6 deleted, and -7's `After:` line (R14).
- Tests: `tests/test_risk.py` (new), `tests/test_findings.py`, `tests/test_retro.py`,
  `tests/test_preflight.py`, `tests/test_skills.py`, a `landing_reach` test.

## Work order

1. Config keys, `risk_paths()`, `_risk_report()`, the `risk` preflight part; `test_risk.py`.
2. `ship_question()`'s clauses and `--fresh-skipped`; preflight tests and the skill's sentence.
3. `By:` in findings, the trailer keys, retro's sums; tests.
4. `agents/reviewer.md`, the narrowed root-agents test, `landing_reach()`; tests.
5. Ship and setup skills, `READS_CONFIG`; skill tests.
6. Template, guides, REFERENCE, AGENTS.md, this repo's config; `record`; `./check.sh`, its own exit
   code read.

## Tests

- R1–R3: `test_risk.py`: defaults, a host's lists, a non-list warned; prefix, glob, rename; the
  `risk` part empty, sensitive, irreversible.
- R4, R8, R9: clause tests through `ship_question()` and `cmd_ship_question()`.
- R5: a skill text test that ship never changes `tier:` from risk.
- R6: the agent's `tools` hold only Read, Grep and Glob; ship's `allowed-tools` holds `Agent`;
  Step 3 names `sdlc:reviewer`.
- R7: `By: fresh` parsed, any other `By:` a problem, `fresh=` and `fresh_wrong=` in the trailer,
  retro's sums.
- R10: `READS_CONFIG` entries; setup names both keys.
- R11: `landing_reach(["agents/reviewer.md"])["agents"] == ["sdlc:reviewer"]`.
- R12–R14: drift clean; at ship.

## Rollback

`git revert` of the ship commit undoes the code. Not undone by it: hosts that ran `/sdlc:setup`
keep the template's `By:` line and any `[review]` keys they set (harmless: an unknown key warns).
Fix forward for those: a release without them, then `/sdlc:setup` in each host. Seeds 2026-11-03-5
and -6 would be refiled by hand.
