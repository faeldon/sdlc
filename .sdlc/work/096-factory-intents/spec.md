---
id: 096
slug: factory-intents
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 096 — Intent opens several changes from one run · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. A single run is unchanged: an argument with no `;` opens one change exactly as today (the
   interview, Step 4's question in every form, `EnterWorktree` after a by-hand yes), and the
   existing intent cases and skill tests pass unedited.
2. An argument holding `;` is a batch: groups separated by `;`, each one or more register ids, then
   optionally `as <slug>`, `tier <1|2>`, `after <slug>` (another group of the same call) and
   `— <words>` (the person's words for that change alone, last). The skill proposes a slug and a
   tier for each group without one before it asks the script anything.
3. `sdlc.py groups "<group>" "<group>" …` reads a batch and writes nothing. Each argument is one
   group with its `—` words removed and its `as` and `tier` present. Its JSON gives each group's
   slug, tier and `after`; each id's kind (`idea`, `bug`, `nit`), title and `Issue:` numbers, from
   `inbox_entries()`; `created`, the open change with that slug if there is one; then `order`, the
   groups in creation order, and `refusals`.
4. `groups` refuses, naming the group: an id the register doesn't hold; an id in two groups; an id
   tagged `[building]` or named by an open change's `idea:` or `fixes:`; a group with no id, or
   with no `as` or `tier`; a Tier 0 group (it gets no folder); two groups with one slug; a slug a
   closed or dropped change already used; an `after` naming no group of the batch; a cycle of
   `after`s. A refused batch writes nothing, and its refusals are shown before any question.
5. `order` puts each group after the one its `after` names and keeps the given order otherwise; its
   tests pin a chain, a fan-out (two groups after one) and the given order on a tie.
6. Each group with an `after` reports `depends_on`, the number of the change it waits on, once
   `created` holds it, and null before. The skill writes a `depends_on:` line only from that field,
   read after the change it names was created, never a number from `next` or from memory.
7. The batch's text lives in `skills/intent/batch.md`, which `SKILL.md` names and reads only when
   the argument holds `;`. The WAIT and its literal batch question stay in `SKILL.md`, which keeps
   one WAIT heading (`test_a_skill_s_side_files_are_named_by_it_and_hold_no_gate`).
8. Every intent is drafted in full and shown before the question, as a single run drafts one: every
   template section, a Tier 1's Approach naming each nit taken in, the proposed `serves:` line with
   where it came from. A group's Problem quotes its entries' own prose and its `— words`.
9. One question for the whole batch, as land asks: `Create these <n> changes in this order, each in
   a new worktree and branch off <git.base>, <slug> (Tier <t>, serving <O1 (name)>), …? (yes /
   leave one out / edit one / no)`, with `, each opening its GitHub issue with its title and intent`
   after `<git.base>` under `ids_from: github`. `leave one out` and `edit one` take the person's
   answer, run `groups` again without that group (or with it changed), redraft only what changed,
   and ask again; a group whose `after` names one left out is refused by `groups`, and that is
   shown. The yes approves every change listed and nothing else.
10. After the yes, each change in `order` is created as a single run creates one: `sdlc.py new
    <slug> --tier <t> --title "<title>" --worktree`, the repo's `worktree_setup` in a subshell when
    set, the intent written with its `idea:`, `fixes:`, `closes:`, `serves:` and `depends_on:`
    lines, its seeds tagged `[building]` in its own worktree's register, then `sync`. `groups` runs
    again before each change that has an `after`. The session never enters a worktree and ends
    where it started.
11. A stop partway leaves what was created complete: a refusal from `new` (GitHub unreachable, say)
    stops the run, and the report names the changes created and those not reached. The same command
    run again shows the created ones as `created` (R3), skips them, and creates the rest with their
    `depends_on:` read from the created ones; a test runs `groups` over a folder where one group's
    slug already exists.
12. The report gives each change's number, issue and worktree, and its next command: `/sdlc:spec
    NNN` (Tier 2) or plan mode (Tier 1) from a new session in its worktree, or `/sdlc-factory:build
    NNN` from the main checkout when `factory.enabled`; and, for a change with `depends_on:`, that
    it waits on that change landing.
13. `allowed-tools` gains `Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py
    groups *)`, `groups` joins `READ_ONLY`, and every command in `batch.md`'s bash blocks has a rule
    (`test_skills.py`).
14. REFERENCE.md and README.md say it where they describe opening a change, as do the skill's
    description and `argument-hint`, and `plugins/factory/README.md`'s hand-off from intent.

## Design

**Script (mechanism).** `cmd_groups(root, groups)` in `sdlc.py` parses each argument into ids (the
register's id shape), `as`, `tier` and `after` with a tokenizer of its own (never `shlex` on joined
text); joins the ids against `inbox_entries()` (kind, title, `Issue:` numbers); reads open changes
through `change_dirs()` for `created`, `idea:` and `fixes:` (by `frontmatter_list()`, never YAML);
checks slugs against `_used()`, the same check `cmd_new` refuses on, so a refusal `new` would give
is seen before the question; and orders by a stable topological sort, finding cycles by the same
walk. It prints JSON (`groups`, `order`, `refusals`) and exits 1 with refusals. A slug is matched
by `slugify()`'s result, so `as Board-Fixes` and `board-fixes` are one slug.

**Skill (judgment).** `SKILL.md`'s Step 0 says an argument holding `;` is a batch, which reads
`batch.md` at each step that names it; Step 4 gives the batch question beside the single one; the
rest is unchanged. `batch.md` holds, in step order: splitting on `;` and keeping each group's
`— words` aside; proposing a slug and tier for each group missing one; `groups`; drafting each
intent by Steps 1–3's rules; showing them compactly, a change per section; after the yes, the
creation loop of R10; the report of R12. The interview is skipped: each group's entries and words
are its answers, as a brief's are, and a question only the person can answer goes in that intent's
Open questions.

**Rerun.** `created` is what makes a rerun safe: a slug that is an open change was made by an
earlier run of this batch or by hand, and is skipped either way.

## Contracts touched

- **A skill's WAIT (always Tier 2).** Intent keeps one WAIT heading; the batch question approves
  only the changes it lists, every one drafted and shown first, and never stands for a later run.
- **Numbering.** The batch never numbers anything: every number comes from `new`, under its lock or
  from GitHub, one change at a time, and `depends_on:` is written only from a number `groups` read
  back from a created folder. No local fallback under `ids_from: github` (`new` already refuses).
- **Mechanism vs. judgment.** Parsing, checking, ordering and finding created changes are the
  script's; drafting, slugs and tiers the skill's. No loop in a bash block: the skill runs `new`
  once per change, as plain commands.
- **Narrow `allowed-tools`.** One new rule, for a read-only command.
- **The register.** Written as a single run writes it, in each change's own worktree only: never
  committed on `main`, never by `inbox-commit`.
- **Nothing public names the agent.** The issues carry each intent's title and body, as today.
- **O5, light footprint.** A single run reads none of `batch.md`.

## Alternatives rejected

- **A factory skill (`/sdlc-factory:intent`).** It would restate intent's rules (tiers, push-backs,
  `serves:`, seed tagging) where they'd drift, and batching needs nothing from the factory: a host
  without sdlc-factory would go without it.
- **A question per change, in dialogs of four.** Ten changes are three dialogs; `leave one out` and
  `edit one` give the same control in one question, as land does.
- **A brief file per batch.** It means writing a file before the WAIT; the inline command is what
  the model writes for the person to paste.
- **Making intent model-invocable.** It breaks `disable-model-invocation: true` on a skill that
  writes, which the skill tests require and the WAIT depends on.
- **The script creating the whole batch in one call.** It puts the loop and the drafting's output
  through the script; one `new` per change keeps each step the single run's own.
- **The skill proposing the grouping from bare ids.** Several ids already mean one change; the
  grouping is proposed by the model when it writes the command.

## Verification

- `uv run --group dev pytest tests/test_groups.py -q`: the parse, every refusal of R4, the
  order of R5, `depends_on` before and after creation (R6), and the rerun of R11.
- `uv run --group dev pytest tests/test_skills.py -q`: `batch.md` named and holding no gate, the new
  rule used and covering its command, the batch question in a dialog with 4 answers, one WAIT.
- `./check.sh` green, the intent case's fixture still passing `check --strict`.
- Live, after 096 lands: this batch's own command (096's intent, Outcome) shows ten drafts and one
  question, creates them in order with wave 2's `depends_on:` set to landing-fixes' number, and the
  same command run again creates nothing twice.
