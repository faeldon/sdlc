---
id: 114
slug: one-review
kind: plan
created: 2026-11-17
updated: 2026-11-18
---

# 114 — One review checklist and one findings record for ship and the factory · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `.sdlc/work/114-one-review/notes.md` (new): R14's `## Evidence`, R15's `- [ ] gap:` items.
- `guide/review.md`: `## Review dimensions` (R1), Pass 1's test-per-requirement rule (R3).
- `.sdlc/setup.json`: rerecorded by `sdlc.py record` (R2).
- `skills/ship/SKILL.md`: Step 3 item 1 (R3), and the "never raise again" rule scoped to the
  person's answers (R11).
- `skills/ship/factory.md`: a Step 3 keeping the agents' sections as written and never bound by an
  agent's `wrong` (R11), and Step 4 showing the agents' findings, counted apart. *Departure from
  R11's wording:* the spec puts the keep rule in `SKILL.md` Step 3, but
  `test_ship_s_skill_stays_under_its_budget` holds `SKILL.md` to 475 lines and says what only some
  runs need goes in a branch file. Agent sections exist only on a factory-built change, exactly
  when `preflight`'s `branches` names `factory.md`, so the rule is read on every run it applies to.
- `skills/ship/undone.md`: the `→ bug:` disposition for a `pre-existing:` item (R19).
- `plugins/factory/agents/reviewer-code.md`: pass 5, Context (R4); `[pass]` tags (R5); `- NIT:` (R6).
- `plugins/factory/agents/reviewer-security.md`, `reviewer-test.md`: `- NIT:` lines (R6), `[pass]` (R5).
- `plugins/factory/agents/approver.md`: the `→ bug:` proposal (R17).
- `plugins/factory/scripts/factory.py`:
  - `FINDING_NIT_RE` (the agents' `- NIT:`; *departure from R6's wording:* `NIT_RE` already
    names the register's `[nit]` heading, so the spec's name is taken) and `PASS_TAG_RE`, `ROLE_PASS`, `finding_pass()` (R5, R6);
    `read_rounds()` gains `nits` per review, never in `changes`.
  - `FINDINGS_HEAD` (R13), `agent_findings()`, `finding_section()` and `write_findings()`,
    called from `cmd_carry()` (R7, R8); `_note_line()` starts a missing file from
    `FINDINGS_HEAD`. `_change_path()`/`_change_lead()` read past a `[pass]` tag, so a tagged
    CHANGE still resolves by its lead and is judged pre-existing by its path.
  - `bad_bugs()`, `severity_words()` (R18), called from `land_signals()`, so `land-check` and
    `land` refuse alike.
  - `UNDONE_RE`, `TICKED_RE` gain `bug`; `read_proposals()` returns `("bug", severity, paths,
    title)`; `land_parts()` carries a `bug` item; `land_signals()`/`cmd_land_check()` refuse a bad
    proposal against `sdlc.py bugs`'s `severities`; `land_question()` names filed bugs; `_dispose()`
    appends `[bug]` entries; `land_message()` leaves bug ticks out (R17, R18). The approve prompt
    names the format (R17).
- `scripts/sdlc.py`: `AGENT_ROLES`, `FINDING_BY`, `findings_trailer()` and `_findings_report()`
  count ship's own only and add `agents` (R9); the ship refusal names `→ bug: <id>` (R19).
- `scripts/retro.py`: `review_sources` and `review_unknown` in `bugs_retro()` (`_review_sources()`),
  `by` on each `important` row, the report's lines after the escapes table (R12).
- `plugins/factory/skills/land/SKILL.md`: the `bug` disposition, its exclusions and its `shown`
  line (R18).
- `tests/test_bugs.py`: `bugs_retro()`'s empty shape and `important` rows gain the new keys.
- `templates/findings.md`: the note says both write it and who `By:` names (R13).
- Docs (R16): `docs/REFERENCE.md`, `plugins/factory/README.md`, `AGENTS.md` (*Ship*),
  `.sdlc/REVIEW.md` (a new failure class).
- Tests: `tests/test_defaults.py`, `tests/test_factory.py`, `tests/test_land.py`,
  `tests/test_findings.py`, `tests/test_retro.py`, `tests/test_sdlc.py`.
- `.sdlc/work/114-one-review/checks.md` (new): R3, R4, R11, R19's acceptance checks.

Reused, not re-derived: `read_rounds()`, `read_verified()`, `_rounds_at_depth()` (what `carry`
already reads), `_change_lead()`/`_change_path()` for `Evidence:`, `sdlc._findings_from_text()`
for the round trip, `_sdlc()` for `bugs`, the one `next-entry` call in `_dispose()`, `_review_at()`
in retro.

## Work order

1. **The guide's dimensions (R1, R2, R3's guide line).** Test first
   (`test_every_review_dimension_names_both_ways`), then the section, then `sdlc.py record`.
2. **Core counts ship's own (R9).** `AGENT_ROLES` pinned to `REVIEWERS`; the trailer and
   `findings` counts leave the agents' out, with `agents=`.
3. **The factory reads a finding's pass and the agents' nits (R5, R6).** `finding_pass()`, the nit
   regex, `read_rounds()`; the verify prompt still built from `changes` only.
4. **`carry` writes `findings.md` (R7, R8, R13).** `FINDINGS_HEAD` pinned; the sections from the
   rounds; a rerun replaces only factory-`By:` sections and is byte-stable.
5. **The landing commits it, no trailer (R10).** A test over `cmd_land`'s commit.
6. **Bugs at landing (R17, R18).** Regexes, proposals, land-check's refusal, the question, the
   filing, the rerun.
7. **Ship by hand (R11, R19).** The refusal text test; `undone.md`, `SKILL.md`, `factory.md`.
8. **Retro (R12).** `review_sources` and its report lines.
9. **Prompts and docs (R4, R6's prompts, R16).** Agent files, README, REFERENCE, AGENTS.md,
   REVIEW.md; `checks.md`.

Each step ends with its tests and `./check.sh` green.

## Tests

- R1: `test_every_review_dimension_names_both_ways` (`tests/test_defaults.py`).
- R2: `test_every_prompt_sits_in_a_guide_slot` and the gate's drift check, unchanged.
- R3, R4, R11, R19 (prompt and skill text): acceptance checks in `checks.md`.
- R5: `test_a_finding_takes_its_tagged_pass_else_its_roles` (`tests/test_factory.py`).
- R6: `test_nits_are_read_and_never_verified` (`tests/test_factory.py`).
- R7: `test_carry_writes_each_agent_finding_once_by_its_role` (`tests/test_factory.py`).
- R8: `test_carry_rewrites_only_the_agents_findings` (`tests/test_factory.py`).
- R9: `test_finding_by_names_every_factory_reviewer`, `test_the_trailer_never_counts_an_agent_finding`
  (`tests/test_findings.py`).
- R10: `test_a_landing_commits_the_agents_findings_and_no_trailer` (`tests/test_land.py`).
- R12: `test_review_sources_split_ship_from_the_agents` (`tests/test_retro.py`).
- R13: `test_findings_head_is_the_template` (`tests/test_defaults.py`).
- R14, R15, R16: ship's review reads `notes.md` and the docs; `sdlc.py preflight 114` lists the
  gaps.
- R17: `test_the_approver_may_propose_a_preexisting_item_as_a_bug` (`tests/test_land.py`).
- R18: `test_a_landing_files_each_approved_bug_once` (`tests/test_land.py`).
- R19: `test_ship_refusal_names_every_disposition` (`tests/test_sdlc.py`).

## Rollback

`git revert` undoes everything here. Not covered: `[bug]` entries a landing has already filed in a
host's register (they are ordinary entries: retire them with `/sdlc:idea` if unwanted), and
`findings.md` files with factory `By:` sections already committed with landed changes. Core
before this change reads `By: code` as a problem, so after a revert `sdlc.py findings` on such a
change reports it; history is never rewritten, and retro's `_review_at()` lists the problem rather
than miscounting. `templates/findings.md` is read in place from the plugin, so a revert reaches
every host on the next release.
