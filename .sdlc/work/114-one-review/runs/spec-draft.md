---
id: 114
slug: one-review
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 114 — One review checklist and one findings record for ship and the factory · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1. The guide holds a keyed list of what a review covers.** `guide/review.md` gets a
   `## Review dimensions` section, after the Scope paragraph and before `## Pass 1 — Correctness`.
   Each dimension is one `- **<key>**` bullet holding a `Ship:` clause and a `Factory:` clause,
   saying who covers it in each way of building. A way that doesn't cover it says `not covered`.
   A dimension whose findings carry a pass tag also says `Pass: <correctness|contract|cost|context>`.
   The keys are `requirements`, `tests-fail`, `failure-classes`, `contract`, `security`, `cost`,
   `context`, `end-to-end`, `ui`, `ux`, `false-positives`, `pre-existing`, `nits`, `fresh-eyes`,
   `acceptance` and `recovery`. The test `test_every_review_dimension_names_both_ways`
   (`tests/test_defaults.py`) fails if any of these happens:
   - a bullet lacks either clause;
   - a `Pass:` isn't in `sdlc.FINDING_PASSES`;
   - a factory reviewer it names (`reviewer-<role>`) has no file in `plugins/factory/agents/`;
   - a key appears twice.
2. **R2. The guide stays an answer-free guide.** The new section holds no `<…>` prompt and no
   "A repo lists here" slot. It needs no new prompt in `defaults/`. `scripts/sdlc.py record` runs
   in the change's checkout, so `sdlc.py drift` reports nothing. Proof:
   `test_every_prompt_sits_in_a_guide_slot` and the gate's drift check both still pass, and no
   host's `REVIEW.md` needs an edit.
3. **R3. Ship's correctness pass names a test for each requirement.**
   - In `guide/review.md`'s Pass 1, a requirement's test is the one that would fail without its
     code. The review names that test, and the line whose removal would fail it, for every
     requirement.
   - In `skills/ship/SKILL.md` Step 3 item 1, a requirement whose test can't be named, or whose
     test could pass without its code, is a `[correctness]` finding.
   - Proof: acceptance checks in `checks.md` grep both files for the rule. Only a revert could
     fail them, so they are not suite tests.
4. **R4. The factory's code reviewer runs a context pass.** `plugins/factory/agents/reviewer-code.md`
   gets a fifth pass, Context. It reads the docs `[docs] context` names in `.sdlc/config.toml`
   (else `CLAUDE.md`, `.claude/CLAUDE.md` and `AGENTS.md`, the default in REFERENCE.md), plus any
   `CLAUDE.md` above a changed path, and asks ship's three questions of each.
   - A doc the diff makes false is a `- CHANGE: [context] <doc>:<line>: …`.
   - An addition is a CHANGE only when it meets ship's bar.
   - Anything else gets no line.
   - Proof: an acceptance check reads the agent file.
5. **R5. An agent's finding may name its pass.** A `- CHANGE:`, `- PREEXISTING:` or `- NIT:` line
   may open with `[<pass>] `, one of the four passes. `factory.py` takes it as that finding's pass
   and otherwise uses its role's pass: `security` is `contract`, and every other role is
   `correctness`. A tag outside the four is left in the text and the role's pass is used.
   `CHANGE_RE`, `PREEXISTING_RE` and their copies in `board.py` are unchanged. The test
   `test_a_finding_takes_its_tagged_pass_else_its_roles` (`tests/test_factory.py`) fails if a
   tagged line is filed under its role's pass, or an unknown tag changes the pass.
6. **R6. Reviewers list their nits in a form the script reads.** `reviewer-code`,
   `reviewer-security` and `reviewer-test` write their nits (at most five) as
   `- NIT: path:line: what` lines under `## Notes`, in place of free prose. `factory.py` reads them
   with a new `NIT_RE`. They never make a verdict `CHANGES`, and the verifier never sees them.
   - Proof: `test_nits_are_read_and_never_verified` (`tests/test_factory.py`) fails if a `- NIT:`
     line reaches the verify prompt or `read_rounds()`'s `changes`.
7. **R7. The factory writes the shared record.** `factory.py carry` writes the change's
   `findings.md` beside `notes.md`. It holds one `## F<n>. [rank] [pass] title` section for each
   distinct `(role, text)` across every complete `reviews/round-<N>/`, in round order, then role
   order (`REVIEWERS`), then line order. Rank and disposition:

   | What the reviewer raised | Rank and disposition |
   |---|---|
   | A CHANGE the verifier kept that the last complete round no longer asks for | `[important]`, `fixed` |
   | A CHANGE the verifier kept that is still asked for, so carried to `notes.md` | `[important]`, `recorded` |
   | A CHANGE the verifier dropped | `[important]`, `wrong`, with `Reason:` the verifier's text after its last ` — ` |
   | A `PREEXISTING` | `[pre-existing]`, `recorded` |
   | A `NIT` | `[nit]`, `minor`, with `Reason: raised by an agent; not weighed or filed` |

   In a round from before there was a verifier, every CHANGE counts as kept. Every section has
   these lines:
   - `By: <role>`.
   - `Evidence:` the line's leading `path[:line]`, or `reviews/round-<N>/<role>.md` when it opens
     with none.
   - `Class: <role> review, round <N>`.

   `carry` never writes `open` or `fix`, so `sdlc.py ship` and the landing never refuse over the
   agents' findings. The test `test_carry_writes_each_agent_finding_once_by_its_role`
   (`tests/test_factory.py`) builds two rounds and asserts each row of the table. It also checks
   that a CHANGE repeated word for word in round 2 is one finding, and that
   `sdlc.findings_entries()` reads the file with no problems. It fails if a finding is missing,
   doubled or unreadable by core.
8. **R8. Rerunning carry rewrites only its own sections.** A second `carry` (a restart, an upgrade,
   or a plain rerun) replaces only the sections whose `By:` names a factory role. It keeps:
   - the title and note, including any `Fresh review:` or `Skill evals:` line `_note_line()` wrote;
   - every other section, as written.

   Its sections are numbered after the highest id it kept, and two runs with nothing new leave the
   file byte for byte the same. The test `test_carry_rewrites_only_the_agents_findings` fails if a
   ship-written section or a note line is lost or renumbered, or a rerun changes the bytes.
9. **R9. Core reads agent findings and counts them apart.** In `scripts/sdlc.py`:
   - `FINDING_BY` becomes `("fresh", *AGENT_ROLES)`, where `AGENT_ROLES` is a copy of
     `factory.py`'s `REVIEWERS`, pinned by
     `test_finding_by_names_every_factory_reviewer` (`tests/test_findings.py`). An unknown
     `By:` is still a problem.
   - `findings_trailer()` counts only ship's own findings (no `By:`, or `By: fresh`) in every key
     it has today, and appends `agents=<n>`.
   - `cmd_findings()`'s `counts` likewise exclude the agents' findings, and it adds an `agents`
     count.

   The test `test_the_trailer_never_counts_an_agent_finding` fails if an agent's finding moves any
   existing key. A file with no agent findings gives today's line plus ` agents=0`.
10. **R10. The landing still records no Sdlc-Findings.** `land_message()` keeps writing no
    `Sdlc-Findings` line. The landed commit carries the agents' `findings.md` with the folder, and
    `Sdlc-Landed` is unchanged. Proof: `test_a_landing_commits_the_agents_findings_and_no_trailer`
    (`tests/test_land.py`) fails if the trailer appears or the file is missing from the commit.
11. **R11. Ship builds on the agents' findings without answering for the person.** In
    `skills/ship/SKILL.md` Step 3:
    - ship keeps every section with a factory `By:` exactly as written, never re-dispositions or
      renumbers one, and numbers its own after the highest id;
    - an agent's `wrong` (a verifier's drop) never stops ship raising the same fault as its own
      finding. The "never raise again" rule covers only answers the person gave.

    `skills/ship/factory.md` Step 4 shows the agents' findings under their verdicts, counted apart
    from ship's own. Proof: acceptance checks read both files.
12. **R12. The retro compares the two ways from the one record.** `retro()`'s bug pass gains
    `review_sources`. For every change in the window whose `findings.md` was read (`state: file`),
    it gives, per source (`ship`, `fresh`, and each factory role), counts of `important`, `nit`,
    `preexisting` and `wrong`, plus the number of changes that source reviewed. Each row of
    `important` carries its `by`. `retro_report()` prints one line per source. The test
    `test_review_sources_split_ship_from_the_agents` (`tests/test_retro.py`) fails if an agent's
    finding is counted under `ship` or the reverse.
13. **R13. The template and the factory's copy of it agree.** `templates/findings.md`'s note says
    that both ship and the factory write the file and that `By:` names the reviewer (`fresh` or a
    factory role, none for ship's own). It also says that the trailer counts ship's own alone.
    `factory.py` starts a missing file from `FINDINGS_HEAD`, a copy of the template's title and
    note, and `_note_line()` uses it too. The test `test_findings_head_is_the_template`
    (`tests/test_defaults.py`) pins the copy, as `NOTES_HEAD` is pinned.
14. **R14. The evidence is recorded and cited, as the builder's first step.** Before any code,
    the builder writes `## Evidence` in `notes.md`, built by read-only `git show` and `git log`
    from:
    - each change closed since 103, its `Sdlc-Findings` or `reviews/round-*` counts, and its
      `Sdlc-Landed`;
    - every `[bug]` with `Introduced by:`.

    Each choice in *Design* that names a gap cites its rows. If a row contradicts a choice, the
    build stops with a blocking decision and does not build past it. Proof: ship's correctness pass
    reads the section against this list.
15. **R15. Gaps left unfilled become undone notes the landing files as seeds.** For each gap
    *Design* leaves unfilled, `notes.md` holds one unticked `- [ ] gap: <dimension>: <what's
    missing>` item, written by the builder. No seed is filed by hand or through `/sdlc:idea`.
    - **At landing:** the approver proposes `- UNDONE: <item> → seed: <title>` for each, and
      `/sdlc-factory:land` (or `/sdlc:ship`, by `undone.md`) files them. Undone notes are already a
      landing risk signal, so the person's question shows every one.
    - **Proof:** `sdlc.py preflight 114`'s `undone` part lists each gap before landing, and after
      landing each is ticked `→ seed: <id>` with an id that resolves in `.sdlc/work/inbox.md`.
16. **R16. The docs say what is now true.** The docs this changes:
    - REFERENCE.md: the `findings.md` paragraph, the `Sdlc-Findings` paragraph, retro's
      `review_sources`, and the landing's `bug` disposition.
    - `plugins/factory/README.md`: *What it leaves*, the agents table, the code reviewer's context
      pass, `- NIT:`, and the landing's bugs.
    - AGENTS.md: *Ship*'s "Ship writes `findings.md` and the script only reads it" becomes
      "ship, and the factory's `carry`, write it".
    - `.sdlc/REVIEW.md`: a new `- **A finding counted for the wrong reviewer.**` class, pinned by
      R9's test.

    Proof: ship's context pass. The gate's `test_defaults` still passes on `.sdlc/REVIEW.md`.
17. **R17. The approver can propose a pre-existing finding as a bug.** In the approve prompt in
    `factory.py` and in `approver.md`, an unticked `pre-existing:` item may be proposed as
    `- UNDONE: <item text> → bug: <severity>: <path>[, <path>…]: <title>`. The severity is one of
    the words in the Bugs section of the process doc (`[docs] process`, else the guide's). Seed and
    drop stay as they are. A pre-existing item with no line is still carried as a seed titled by
    its first sentence, never filed as a bug with a guessed severity. `UNDONE_RE` and `TICKED_RE`
    gain `bug`, and `read_proposals()` returns `("bug", severity, paths, title)`. The test
    `test_the_approver_may_propose_a_preexisting_item_as_a_bug` (`tests/test_land.py`) fails if a
    `bug` line is unread, or if the approver's prompt and agent file lose the format.
18. **R18. The landing files approved bugs, and refuses bad proposals.**
    - **Checking (`land-check`):** reads the severity words from `sdlc.py bugs`'s `severities` (run
      through `_sdlc()`, as landing already runs `sdlc.py`).
    - **Bad proposals:** a `bug` proposal whose severity isn't among those words, whose paths are
      empty, or that is made on an item not starting `pre-existing:` leaves that change for
      `/sdlc:ship`, naming the item and the words. This is the same treatment as an irreversible
      path with no `RECOVER`. The script never guesses a severity.
    - **What the question shows:** each approved bug as `filed as a bug, <severity>: <title>
      (<paths>)`.
    - **Filing (`_dispose()`):** each approved bug is appended to the register with an id from the
      same one `next-entry` call the seeds use. The entry is `## [<id>] [bug] <title>`, a first body
      line `Found by the review of <NNN-slug>.`, the item's text, then `Severity: <severity>` and
      `Paths: <paths>`. It has no `Introduced by:`, which is for a confirmed escape. The item is
      ticked `→ bug: <id>`.
    - **Rerun:** a rerun finds the item ticked and files nothing twice.
    - **Commit message:** `land_message()` leaves bug ticks out of `Carried forward:` and `Dropped:`.

    The test `test_a_landing_files_each_approved_bug_once` (`tests/test_land.py`) fails if any of
    these happens:
    - the entry lacks `Severity:` or `Paths:`;
    - `sdlc.bug_entries()` reports a problem on it;
    - a rerun appends it again;
    - a bad severity lands the change in place of leaving it for ship.
19. **R19. Ship by hand offers the same disposition.**
    - `skills/ship/undone.md` offers a third disposition for an item starting `pre-existing:`: file
      it as a bug, proposed in the shape ship already uses for a Pre-existing finding (Step 4). It
      takes an id from the same `next-entry` call and is ticked `→ bug: <id>`. Ship's question
      counts it under `--bugs`.
    - `sdlc.py ship`'s refusal over an undone item names `→ bug: <id>` beside seed and dropped.
    - Proof: an acceptance check reads `undone.md`, and the test
      `test_ship_refusal_names_every_disposition` (`tests/test_sdlc.py`) fails if the message
      drops one.

## Design

### Assumptions, checked in the code

- Ship writes `findings.md`, and `findings_entries()` / `_findings_from_text()` are core's one
  parser (`scripts/sdlc.py:1193`, `:1252`). `By:` is validated against `FINDING_BY = ("fresh",)`
  (`:1190`, `:1300`).
- `findings_trailer()` counts every entry (`:1314`). No factory finding has ever been in a
  `findings.md`, so excluding agent findings changes no count in history.
- The landing writes no `Sdlc-Findings` on purpose (`factory.py:3562`,
  `plugins/factory/skills/land/SKILL.md:33`). It already creates `findings.md` for its note lines
  (`_note_line()`, `factory.py:3496`).
- `cmd_carry()` (`factory.py:1615`) runs at every `approve` step and already reads every complete
  round's verdicts, kept and dropped changes, and pre-existing lines. It writes each unresolved one
  to `notes.md` as `- [ ] pre-existing: …`.
- The approver proposes undone dispositions as `- UNDONE: … → seed|dropped: …`, through
  `UNDONE_RE` (`factory.py:2860`), the prompt at `:2501` and `approver.md:65`. `land_parts()`
  (`:3152`) defaults an unproposed item to a seed. `_dispose()` (`:3615`) appends `[idea]` seeds
  with ids from one `next-entry` call, and ticks `→ seed: <id>`.
- Those seeds carry no `Severity:` or `Paths:`. Evidence: inbox entries 2026-11-17-59 and -81 to
  -84, carried from 110's notes, where -81 and -84 name a fault and a path and -83 is plainly a nit.
- Two other pieces of code read these lines:
  - `sdlc.py ship` refuses only on unticked items (`:3405`), so a `→ bug:` tick needs no core
    parsing.
  - `bug_entries()` (`:1618`) requires `Severity:` among `severities()`'s words, which
    `sdlc.py bugs` prints (`:2638`).
- Retro already reads a change's `findings.md` from its commit with `by` in every row
  (`_review_at()`, `scripts/retro.py:1275`).
- The board reads `findings.md` only to move a hand-built change to Test (`board.py:228`), never for
  a factory run, so a factory-written file moves no card.

### The checklist (R1–R3)

The guide gets a new `## Review dimensions` section. Each dimension's bullet says who covers it in
each way of building. What it gives at the time of this change:

| Key | Ship | Factory | Pass |
|---|---|---|---|
| `requirements` | correctness pass | `reviewer-code` | correctness |
| `tests-fail` | correctness pass (R3) | `reviewer-test` | correctness |
| `failure-classes` | the review doc | `reviewer-code` reads it | correctness |
| `contract` | contract pass | `reviewer-code` | contract |
| `security` | secrets only, plus the fresh reviewer on a sensitive path | `reviewer-security` | contract |
| `cost` | cost pass | `reviewer-code` | cost |
| `context` | context pass | `reviewer-code` (R4) | context |
| `end-to-end` | not covered | `reviewer-behaviour` | correctness |
| `ui`, `ux` | not covered | `reviewer-ui`, `reviewer-ux` when `[ui]` is set | correctness |
| `false-positives` | the person answers each finding | `verifier` | (none) |
| `pre-existing` | filed as a `[bug]` | filed as a `[bug]` at landing (R17, R18) | (none) |
| `nits` | weighed and filed as `[nit]` | recorded only (R6) | (none) |
| `fresh-eyes` | `sdlc:reviewer` on a deep diff | every agent | (none) |
| `acceptance` | Step 1 | the landing's `accept` | (none) |
| `recovery` | `How to recover:` | the approver's `RECOVER` | (none) |

The guide is generic, so it names roles, never this repo's seeds. The gaps are tracked in
`notes.md` (R15).

### Gaps filled here, and why

Each gap goes where it costs least: a prompt or skill line before code, existing code before new.

- **Ship: does each test fail without its code (R3).** One rule in the guide every host reads and
  one line in ship. No agent is added to ship.
- **Factory: the context pass (R4).** The code reviewer already reads the policy and review docs by
  path from `.sdlc/config.toml`, so the context docs are a third read. A false doc becomes a CHANGE
  the builder fixes, as ship's Important finding would. No new agent and no new run.
- **Factory: pre-existing faults filed as bugs (R17–R19).** The path from reviewer to `notes.md`
  to landing already exists, so the bug is a third disposition on it. The approver judges severity,
  as ship's model does for a hand-built change. The script only checks the word against the host's
  list, and a bad word leaves the change for ship, never a guessed bug.
- **One record (R5–R13).** `carry` already holds every fact the record needs, so writing
  `findings.md` there is one function over data it already reads.

### Gaps left, as undone notes (R15)

The builder writes these as `- [ ] gap: …` items; the landing makes them seeds.

- Ship's security depth beyond secrets.
- Ship running the spec's end-to-end path.
- Ship's UI and UX review.
- The factory's nits weighed (theme, cost, value) and filed as `[nit]` entries.
- The landing review rounds (`reviews/land-<n>/`) added to `findings.md`.

### The record (R7–R9)

`findings.md` keeps one shape. `By:` is absent on ship's own findings (every file in history reads
that way), is `fresh` for the fresh reviewer, or names a factory role. `carry` builds its sections
from `read_rounds()` and `read_verified()`, which it already calls. It reads `NIT_RE` beside
`PREEXISTING_RE`, and parses an optional `[pass]` prefix off the text with one regex. It writes with
`newline="\n"`. It finds its own sections by `By:`, so it keeps:

- ship's sections, if a person ran ship and then restarted the build;
- the note lines the landing writes.

Duplicates are judged by `(role, text)`. A repeat the verifier dropped as settled, but worded
differently, stays one more `wrong`; the template's note says so.

A pre-existing finding is in the record twice, by design. In `findings.md` it is `[pre-existing]`
`recorded`, which is how the review saw it. In the register it is a `[bug]` once the landing files
it, which is what is done about it. Ship's pre-existing findings already work the same way.

### Counting (R9–R12)

- **The trailer.** `Sdlc-Findings` keeps meaning ship's review: its keys count entries with no
  `By:` or `By: fresh`, and `agents=` says how many agent findings the file held and left uncounted.
- **The landing.** It writes no trailer, so `Sdlc-Landed: by=auto` is never next to numbers that
  read as a person's review. A bug filed at landing has no `Introduced by:`, so it never counts as
  an escape.
- **The retro.** It compares the two ways from the files: `review_sources` groups by `by`, and
  `_review_at()` already returns it.

### Edge cases

- **A run with no complete round** (stopped, or escalated before a review). `carry` writes the note
  alone, or leaves an existing file's sections as they are.
- **A round from before the verifier.** Every CHANGE counts as kept.
- **A change landed before this change.** It has no agent sections, and retro counts it as
  `unknown` for agents, never as zero.
- **A hand ship of a factory change.** Ship keeps the agents' sections, adds its own, and its
  trailer counts only its own. Its undone `pre-existing:` items may be filed as bugs (R19).
- **A host whose process doc names no severity words.** `sdlc.py bugs` gives an empty list,
  `bug_entries()` then accepts any word, and land-check does the same. The approver's word stands.
- **A landing rerun after filing.** The items are ticked `→ bug: <id>`, so nothing is filed again.

### Evidence

- **What I read.** The inbox shows the factory's pre-existing findings landing as titled-by-sentence
  `[idea]` seeds (2026-11-17-59, -81 to -84). It also shows two review-shape failures, which a
  record with `By:` and `wrong` would count: 2026-11-17-90 (`Introduced by: 109`, the behaviour
  reviewer's `exit:` lines) and 2026-11-17-86 (a landing review's false positive, which the
  verifier kept).
- **What is still to read.** The per-change tally from commits is R14, the builder's first step.

### Boundaries

- **Always:** keep `Sdlc-Findings`' existing keys and their meaning; keep a factory finding out of
  ship's counts; keep core and the factory reading each other's files through pinned copies; file a
  bug only on an approved proposal with a known severity.
- **Ask first:** filling any gap in R15's list; adding a pass to `FINDING_PASSES`; giving
  bugs filed at landing an `Introduced by:`.
- **Never:** add a factory agent to ship; force a ship pass into a round; edit a host's
  `REVIEW.md`; guess a bug's severity; rewrite a landed change's history to backfill a record.

## Contracts touched

- **A host's review doc is its answers to the guide, read block by block.** The new section is
  guide text with no slot and no prompt, so no host block keys to it and no host's `REVIEW.md`
  changes. Because the guide changes, `sdlc.py record` runs, and the gate's drift check stays
  clean.
- **This repo's process docs hold only its answers.** The `.sdlc/REVIEW.md` addition is a
  plugin-only failure class under *The ways this repo's code fails*, not a restated guide line.
- **`Sdlc-Findings` and the metrics trailers: extend, never redefine.** `agents=` is appended.
  Every existing key counts what it always has, because no committed `findings.md` holds an agent
  finding. Retro reads a trailer without `agents=` as unknown there, as it already does for
  `fresh=`.
- **A factory review is never counted as the person's.** The landing commit keeps no
  `Sdlc-Findings`, and `Sdlc-Landed` is untouched.
- **`factory.py` never imports `sdlc.py`; it runs it only for fresh, upgrade and landing.**
  - The new cross-reads are copies, each pinned by a test: `FINDINGS_HEAD` (the template's head) in
    the factory, and `AGENT_ROLES` (the factory's `REVIEWERS`) in core.
  - The severity words come from running `sdlc.py bugs` inside `land-check`, a landing step. The
    approve step never runs `sdlc.py`.
- **The register.** The landing already appends seeds to it in the change's worktree, and they ride
  the change's commit. Bugs take the same path, with ids from the same `next-entry` call, so no two
  share one. `inbox-commit` stays the only code that commits the register on its own.
- **Confirm before writing.** A bug is filed only after the person's yes to the landing's question,
  which names it. Undone notes are already a risk signal, so the batch can't pass itself.
- **Agents that judge have no Write.** `factory.py` writes `findings.md` and the register, never an
  agent.
- **AGENTS.md's *Ship* says "Ship writes `findings.md` and the script only reads it".** That stops
  being true: the factory's `carry` writes it too. This is an edit to the architecture map, said
  here so it is a decision and not a side effect (R16). Nothing under *Invariants the tests
  enforce* moves.
- **`[review] irreversible` names `templates/`.** R13 edits `templates/findings.md`, so ship (or
  the approver's `RECOVER`) gives `How to recover:`. The template is read in place, never copied
  into a host, so a revert reaches everyone on the next release.
- **The scripts run on Windows.** Every new write passes `newline="\n"`, and paths in `Evidence:`
  and `Paths:` are `as_posix()`.
- **No agent but the builder runs `checks.md`.** No prompt here adds a run.

## Alternatives rejected

- **Factory reviewers inside ship, or ship's passes as a factory round.** The intent's constraint
  rules both out: standardize what is covered, not how it runs.
- **New passes (`security`, `test`, `behaviour`) in `FINDING_PASSES`.** They would add trailer keys
  and retro columns for every host. The dimensions map onto the four passes.
- **An `Sdlc-Findings` trailer on the landing commit, counted from the agents' findings.** Retro
  would read it as ship's review, the one thing the intent forbids.
- **Agent findings counted in the existing keys.** That redefines `important=` and the rest for
  every factory change shipped by hand.
- **Leaving the rounds as the only record and teaching retro to parse `reviews/round-*` from
  history.** That makes two shapes and two parsers, where the intent asked for one record.
- **`By: ship` on ship's own findings.** Every file in history lacks it, so absent has to mean ship
  anyway.
- **A context agent of its own in the factory.** It would cost one more run a round, when the code
  reviewer already reads the docs beside them.
- **A pass inferred from a finding's path.** The `[pass]` tag is explicit and costs nothing when
  absent.
- **Backfilling `findings.md` into landed factory changes.** History is the copy and is never
  rewritten.
- **Filing every pre-existing item as a bug with a default severity, or one the script picks.** A
  guessed severity skews the bug counts retro ranks by. An unproposed item stays a seed, and a bad
  word leaves the change for ship.
- **Copying `severities()` into `factory.py` so the approve step can name the words.** That is
  another parser to pin, when the landing already runs `sdlc.py` and can check the word there.
- **Seeds for the gaps filed now through `/sdlc:idea`.** You chose undone notes: the landing files
  them as it files any other, behind the question that names them.
- **`Introduced by:` on a bug the landing files.** The fault predates the change by definition, so
  naming the change that last touched the path is a guess, and retro would count it as an escape.

## Verification

```bash
./check.sh
uv run --group dev pytest -q tests/test_findings.py tests/test_factory.py tests/test_land.py tests/test_retro.py tests/test_defaults.py tests/test_sdlc.py
uv run --quiet --script scripts/sdlc.py drift
uv run --quiet --script scripts/sdlc.py preflight 114
uv run --quiet --script scripts/sdlc.py findings 114
uv run --quiet --script scripts/sdlc.py accept 114
```

What healthy output looks like:

- **`./check.sh`:** exits 0, with ruff clean, the format check clean, every test passing and
  `claude plugin validate --strict` passing. The new tests named in R1, R5–R10, R12, R13 and
  R17–R19 are in the count.
- **`drift`:** reports nothing for `guide/review.md`.
- **`preflight 114`:** its `undone` part lists one `gap:` item per R15 entry.
- **`findings 114`:** this change's own ship review prints a trailer ending ` agents=0`.
- **`accept 114`:** runs R3's, R4's, R11's and R19's checks, each exiting 0 and leaving the tree as
  it was.
- **Manual (the person's call, paid):** `/sdlc-factory:eval` before and after R4/R6's prompt edits.
  Keep them only if `reviewer-code`'s score holds or rises.
- **Manual:** a factory run on a scratch change with a reviewer's `- PREEXISTING:` line, then
  `factory.py carry` twice. `findings.md` lists each kept, dropped, pre-existing and nit line once,
  with `By:`. The approver proposes `→ bug:`, and `/sdlc-factory:land` names the bug in its question
  and, on yes, files it. `sdlc.py bugs` then lists it with no problems, and the item reads
  `→ bug: <id>`.

