---
id: 189
slug: retro-insights
kind: spec
created: 2026-11-20
updated: 2026-11-20
---

# 189 — The retrospective's report answers its own questions: the Insights section · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Nits taken in: 2026-11-19-65, 2026-11-19-66

Assumptions, each checked in the code: the questions are the seven in `docs/RETRO-SCORECARD.md`,
*Insights: the synthesis questions*. Core never runs `claude`, because `factory.py agent` is the one
place anything does. So the sub-agents run in the skill, through the `Agent` tool, as ship's pass
agents do (`skills/ship/SKILL.md` lists `Agent`). `retro-commit` writes the report itself and
nobody edits it by hand (`cmd_retro_commit()`, SKILL.md Step 6). `indicators.number()` writes a
float as `str(value)`, which reads back exactly through `report_rows()`.

1. **R1. The guide.** `guide/insights.md` holds `# Insights`, a `>` note, and one `##` section
   for each of Value, Speed, Quality, Autonomy, Cost, Simplicity and Tradeoffs, in that order.
   Each section's text is that pillar's question from RETRO-SCORECARD.md. It passes every rule in
   `tests/test_defaults.py`, which already globs `guide/*.md`. Its note says nothing
   `HOST_COPY_RE` matches, and no line starts with `<`.
   `test_the_insights_guide_asks_one_question_per_pillar` fails if a pillar is missing or out of
   order.
2. **R2. A host's extension.** `[docs] insights` defaults to `.sdlc/INSIGHTS.md` and is off while
   the file doesn't exist. `config` reports it with `layout: answers` and `guide` pointing at
   `guide/insights.md`. `insight_questions()` reads both docs through `doc_units()`:
   - a host `## <Pillar>` block with text replaces the guide's question;
   - a heading with nothing under it only places what follows, so the guide's question stays;
   - a host `### <Title>` under a pillar's `##` adds a question on that pillar's figures;
   - a host `## <Title>` that isn't a pillar adds a question on the Tradeoffs figures.

   Two questions with one title is a problem in `retro --insights`' `problems`, and the second is
   dropped. `test_a_host_insights_doc_replaces_adds_and_places` covers all four rules and the
   duplicate, and fails if any one of them breaks.
3. **R3. Each question's figures, and nothing else.** `sdlc.py retro --insights` prints JSON:
   `questions`, each with `title`, `pillar`, `question` and `data`, plus `problems`. `data` holds
   only the `retro()` output paths that `INSIGHT_DATA` names for that pillar (Design), plus
   `process.window` and `process.underneath`. `test_each_insight_gets_only_its_pillars_figures`
   fails if Speed's `data` holds `cost`, or Cost's holds `process.cycle`.
4. **R4. Never a host command's output.** `retro --insights` writes nothing and runs no host
   command. No bundle holds `product.evidence`, `architecture.host` or `tests`, so it never runs
   `retro.evidence`, `retro.indicators` or `retro.test_times`.
   `test_retro_insights_runs_no_host_command` sets all three to commands that touch a marker
   file, and fails if the marker appears or `git status` changes.
5. **R5. One answer shape, fixed by the script.**
   - Fields: `INSIGHT_FIELDS = ("Headline", "Evidence", "Recommendation", "Disposition")`.
   - Disposition kinds: `seed <entry id>`, `intent: <title>`, `dropped: <reason>`, or
     `none: <why>` ("nothing to act on this window" is a valid `none`).
   - The new core agent `agents/insight.md` (`sdlc:insight`) returns exactly that shape. Its tools
     are `Read, Grep, Glob`, its description is over 80 characters and says `Not for`, and it says
     it never writes, runs or commits anything.
   - `test_the_insight_agent_reads_and_returns_the_shape` fails if a field or kind in the agent
     differs from the script's constants, or if its tools differ.
   - `test_sdlc_loads_nothing_from_plugins`' set of agents gains `insight`.
6. **R6. retro-commit renders the answers.** The skill writes its answers to
   `.sdlc/retros/<date>.insights.md` (`insights_rel()`), in the draft shape in Design.
   - **What it checks.** Every question that `insight_questions()` gives is answered exactly once,
     no title is unknown, every field is non-empty, every Disposition is a known kind, and a
     `seed` id names an entry in the register's working text.
   - **Refusals.** Each problem is a refusal, naming the question and the field, and it is found
     before anything is written.
   - **On success.** The answers go into `{{insights}}`, and the commit holds the report, never the
     draft. The draft is removed only after the commit succeeds. A failed `git` step leaves it, so
     a rerun finds it.
   - **Tests.** `test_retro_commit_refuses_an_insight_missing_a_field`,
     `test_retro_commit_refuses_a_seed_the_register_lacks` and
     `test_retro_commit_renders_the_insights_and_removes_the_draft` fail on each case. The last
     also fails if the draft is in the commit's `paths` or still on disk.
7. **R7. No answers is a sentence, never an empty section.** With no draft, `{{insights}}`
   renders `Not answered: this report was written without the retrospective's insights.` This
   applies to `retro-commit` and to `retro --report`. `retro --report` renders a draft that is
   present, so the person can preview it, and still writes nothing.
   `test_the_insights_say_not_answered_without_a_draft` fails if the section is empty or missing.
8. **R8. The template.** `templates/retro.md` gains `## Insights` and `{{insights}}` straight
   after `## Scorecard`, and its note mentions them. `TEMPLATE_READS["retro.md"]` doesn't change,
   so an override without the placeholder isn't breaking and still renders.
   `test_an_override_without_insights_still_renders` fails if it raises, refuses or loses a
   section. A check on `TEMPLATE_READS` fails if `{{insights}}` is added there.
9. **R9. The skill.** `skills/retro/SKILL.md` lists `Agent` and names a new side file,
   `skills/retro/insights.md`. That file holds no frontmatter, WAIT or commit. It:
   - runs `retro --insights`;
   - spawns `subagent_type: "sdlc:insight"` once per question, all in one message, each given only
     its question, its `data` and the answer shape, and nothing of the session's reasoning;
   - never drops an answer: an agent that fails is recorded as `none: not answered, <why>`;
   - folds each Disposition into Step 3, so a pass's finding and an insight's are one seed.

   Step 4 shows the answers. The WAIT adds `with the report at <report> and its <Q> insights`.
   Step 6 writes the draft after the yes, with the seed ids filled in.
   `test_the_retro_insights_file_spawns_its_agent` fails if the spawn, "Never drop one" or the
   not-answered rule is missing. The existing WAIT, rule and side-file tests still pass.
10. **R10. `render_report()` takes the figures whole (2026-11-19-63).** Its signature becomes
    `render_report(template, figures, *, indicators=None, insights=None)`. `figures` is
    `report_figures()`'s dict and must hold `process`; any other key that's missing reads as None.
    `retro_report()` passes `f` whole.
    - `test_render_report_takes_the_figures_whole` checks the parameters through `inspect` and
      fails on any other parameter.
    - Every existing `render_report(template, process)` call becomes
      `render_report(template, {"process": process})`, and still passes.
11. **R11. Every null row names its real reason (2026-11-19-64).** `missing_because` is added to
    four blocks: the response medians by tier, `autonomy.asked`, the three workaround counts, and
    the escape rate by way.
    - The response medians are counted by `_minutes_why()` over that tier's changes.
    - `autonomy.asked` with `n` 0 gives `built by hand` for each hand-built change.
    - `outside` and `hand_record` give `no commit on the base branch in the window`.
    - `restored` gives `no register entry added in the window`.
    - The escape rate by way gives `no <way> change in the window`.

    A row's note is `none in the window` only when the window closed no change.
    `test_every_null_scorecard_row_names_its_reason` builds a window with closed changes, none
    measured and none built by the factory. It fails if any null row's note is `NONE_NOTE`.
12. **R12. A trend compares what the table shows (nit 2026-11-19-65).** `_trend()` compares the
    value as the table writes it: `_num(value)`, parsed back the way `report_rows()` reads a cell.
    `test_a_trend_reads_flat_against_its_own_written_value` writes 1/3, 0.174 and 1.4 through the
    scorecard table and reads each back through `_last_rows()`'s reader. It fails unless each
    trend is `flat`. It also fails unless 0.174 against a written 0.17 is `up`, since those are
    two different numbers the person sees.
13. **R13. Minutes keep a decimal (nit 2026-11-19-66).** `_minutes()` rounds to one decimal place,
    so a median response of 1.44 minutes is written `1.4` and reads back the same.
    `test_minutes_keep_one_decimal` fails on `1`. REFERENCE.md's *Retrospectives* says minutes are
    to one decimal, and that the first retrospective after this change compares against
    whole-minute values.
14. **R14. The docs tell the truth.**
    - REFERENCE.md's *Retrospectives* gains Insights, the guide and `[docs] insights`, the draft
      and the answer shape, and `retro --insights`. It no longer says the whole report comes from
      history alone.
    - AGENTS.md's *Retrospectives* paragraph says `retro-commit` reads and removes the insights
      draft and still commits only its four files.
    - `docs/FEATURES.md` and `docs/PROCESS.md` map the new key, agent and flag.
      `tests/test_feature_map.py` passes.
    - `sdlc.py drift` reports nothing in this repo after `sdlc.py record`.

## Design

**The questions.** `guide/insights.md` is read in place, like the other guides.
- `GUIDES` gains `"insights": "insights.md"`, so `doc_path()` gives `config` the guide pointer.
- `CONFIG_KEYS["docs"]` gains `"insights": ".sdlc/INSIGHTS.md"`.
- `HOST_DOCS` doesn't change. Setup neither copies nor records the doc, and `drift` never looks at
  it. `GUIDES`' other readers are `_copy_source()`, `cmd_record()` and `drift()`, which only reach
  `HOST_DOCS` keys, and line 1763, which reads only `process`. None of them changes behaviour.
- `insight_questions(home, cfg)` in `retro.py` cuts both docs with `doc_units()` and merges them by
  key, using the rules in R2. A question's text is its block plus the bullet blocks under it.
- Each question carries `title` (the `##` text, or the host's `###` text), `pillar` (the `##`
  pillar, or `Tradeoffs` for a host `##` that isn't one) and `question`.

**The figures for each pillar.** `INSIGHT_DATA` maps each pillar to paths in `retro()`'s output.
Every bundle also gets that pillar's `scorecard.rows`, `process.window` and `process.underneath`.
- **Value:** `work_mix`, `time_to_users`, `follow_through`, `direction.milestones`.
- **Speed:** `process.cycle`, `lead`, `throughput`, `time`, `wip`, `capacity`, `by_way`, and
  `pipeline.gates` and `pipeline.landing`.
- **Quality:** `process.escapes`, `process.rework`, `rework_questions`, `bugs`, and
  `pipeline.red_gate`, `depth` and `unreviewed`. It also gets `architecture` without `host`, and
  `nits`.
- **Autonomy:** `autonomy`, and `metrics.extra` and `metrics.prompts`.
- **Cost:** `cost`, `spend`, and the token figures in `metrics`.
- **Simplicity:** `simplicity.workarounds`, `surface` (the plugin's own repo only), `prose`.
- **Tradeoffs:** all of `scorecard.rows`, and the Value band.

The plan settles the exact key names against `retro()`'s return.

To keep R4, `cmd_retro(..., insights=True)` builds the figures with every host command list
empty. `_evidence()` is still the only place host commands run. The bundles exclude their output
anyway, so this is no loss to them. It also keeps a host's user data out of an agent's context and
out of the committed report, which SKILL.md's *Out of scope* asks for.

**The agent.** `agents/insight.md` (`sdlc:insight`) has tools `Read, Grep, Glob` and judges only
the figures in its prompt.
- Every claim cites a number from `data`, with its `n`.
- A figure from a greyed block is a hint, never a finding.
- A version that moved in `underneath` is ruled out before any trend is read.
- "Nothing to act on this window" is a valid answer.

It returns:

```
Headline: <one sentence>
Evidence: <the figures, each with its n>
Recommendation: <one thing to do, or nothing>
Disposition: seed | intent: <title> | dropped: <reason> | none: <why>
```

The skill adds the id to a `seed` once `next-entry` has given one.

**The draft and the report.** After the yes, the skill writes `.sdlc/retros/<date>.insights.md`,
one block per question:

```
## Speed

Headline: …
Evidence: …
Recommendation: …
Disposition: seed 2026-11-21-3
```

A field runs to the next field line. `insight_answers(text, questions, register)` parses the
draft and returns answers and problems. `cmd_retro_commit()`:
- reads the draft, and adds its problems to the refusals before anything is written;
- passes the answers to `retro_report(..., insights=answers)`;
- leaves the draft out of `changed`, and removes it after the commit succeeds;
- allows the draft's path as uncommitted, like the report's.

`render_report()` renders each answer as `### <title>: <headline>`, the question in italics, then
the Evidence, Recommendation and Disposition as bullets, each passed through `indicators.cell()`
only where it goes into a table (it doesn't here). `retro --report` reads the draft if there is
one. It is read-only either way.

**`render_report()`.** It reads `figures["process"]`, `.get("spend")`, `"value"`, `"metrics"`,
`"cost"`, `"by_way"`, `"autonomy"`, `"pipeline"`, `"workarounds"`, `"surface"` and `"scorecard"`.
The body doesn't change beyond the renames. Only `{{insights}}` is new.

**The null reasons.** These are set where each block is built:
- `process_views()` gives `time.tiers[t]` a `missing_because` from `_coverage(tier changes,
  _minutes_measured, _minutes_why)`.
- `_autonomy()` gives `asked` one.
- `_workarounds()` and `_restored()` give their counts one, with a count of 0 for the
  commit-based reasons.
- `by_way()`'s escapes give theirs.

`scorecard()` passes each block to `add()`, and `_row_note()` doesn't change.

**Edge cases.**
- A host doc that only places headings changes nothing.
- A repo outside the plugin has no `surface` in Simplicity's bundle.
- A retrospective whose person skips the insights writes no draft, and its report says
  `Not answered`.
- A draft for a question the host has since removed is refused as an unknown title.

## Contracts touched

- **Retrospectives (AGENTS.md).** `retro` stays read-only, and `retro --insights` and
  `retro --report` write nothing.
  - **This moves the policy text, so it needs your decision.** `retro-commit` now reads an
    untracked draft and deletes it. It still commits only the direction doc, the register, the
    product doc and the report.
  - The report is no longer "from history alone": its Insights are the agents' answers, approved
    at the WAIT.
  - AGENTS.md and REFERENCE.md say both (R14). It is a policy edit made in this change, not a side
    effect.
- **Every core agent has Read, Grep and Glob and nothing that writes.** `sdlc:insight` has exactly
  those (R5).
- **Core never runs `claude`.** The agents run in the skill through `Agent`, as ship's do.
  `sdlc.py` only parses what comes back.
- **Writing skills: one WAIT, nothing written before it.** The draft is written in Step 6, after
  the yes, and the WAIT names the insights. `insights.md` holds no WAIT (R9).
- **Narrow `allowed-tools`.** `Agent` is added. `retro --insights` is covered by the existing
  `retro *` rule, and there is no new bash construct.
- **One shape for the shipped docs.** `guide/insights.md` follows it (R1). The template's new
  section stays inside `##` (R8).
- **This repo's process docs hold only its answers.** This repo adds no `.sdlc/INSIGHTS.md`.
- **Template override contract (`TEMPLATE_READS`, `drift`).** `{{insights}}` is optional. An
  override without it isn't breaking and renders (R8).
  - `templates/retro.md` is irreversible, so ship reviews it at full depth.
  - The template's hash in `.sdlc/setup.json` changes, so `sdlc.py record` runs in this change.
- **Config keys.** `docs.insights` is a new key, not a rename, so it isn't breaking. It grows the
  surface the Simplicity pillar counts (it appears as `unmeasured` until a record shows it).
- **Windows.** The draft is read with `encoding="utf-8"` and removed with
  `unlink(missing_ok=True)`, and the report is written with `newline="\n"`.
- **Modules loaded by path.** The new code lives in `retro.py` and reaches `sdlc.doc_units` and
  `sdlc.GUIDE_DIR` through its binding.
- **Nothing about a project.** Test data uses neutral examples.

## Alternatives rejected

- **The script runs the agents** (a `retro` subcommand calling `claude`). Core never runs
  `claude`; only `factory.py agent` does. This would also put a paid call behind a read-only name.
- **Inlining each bundle in `retro`'s default JSON.** The skill reads that output whole, so every
  selected block would be in its context twice. A second read-only call costs time, not tokens.
- **Giving each agent all of `retro`'s output.** This breaks "on its pillar's figures alone". The
  contexts would grow large, and the answers would stop being independent.
- **The skill writing the Insights into the report.** The report is the script's to write, and
  "never write or edit the report by hand" stays true.
- **Committing the answers as a separate file.** `retro-commit`'s commit holds exactly four kinds
  of file. The answers belong in the report, where the person reads them.
- **The answer shape in the guide.** `retro-commit` parses it, and a host that could reword it
  could break its own retrospective. The guide holds questions; the script holds the shape.
- **A host's questions as a section of its process doc.** The process doc answers
  `guide/process.md`. A guide of its own with its own docs key is the pattern every other guide
  uses, and RETRO-SCORECARD.md's *Hosts* names it.
- **`{{insights}}` in `TEMPLATE_READS`.** That would make every existing override breaking, which
  the intent's constraint rules out.
- **Keeping `render_report()`'s keyword blocks.** That is what 2026-11-19-63 asks to undo. The
  test churn is mechanical.
- **Rounding `_trend()`'s value to two places.** `number()` writes full precision, so rounding would
  hide real moves the table shows.
- **Answering nit 66 with a note alone.** Whole minutes flatten every short response to `1`, and
  the trend on those rows can then never move.
- **Reading the last retrospective's Insights back.** Nobody asked for it. Follow-through already
  reads the last retrospective's seeds.

## Verification

```bash
./check.sh
uv run --group dev pytest -q tests/test_retro.py tests/test_skills.py tests/test_defaults.py tests/test_feature_map.py -n auto
uv run --quiet --script scripts/sdlc.py retro --insights | head -40
uv run --quiet --script scripts/sdlc.py retro --report | sed -n '/^## Insights/,/^## Speed/p'
uv run --quiet --script scripts/sdlc.py drift
git status --porcelain
```

Healthy output:
- `check.sh` ends green: ruff clean, pytest all passed, and `claude plugin validate --strict` OK.
- `retro --insights` prints seven questions, Value to Tradeoffs, each with a `data` naming only
  its pillar's keys, and `problems: []`.
- `retro --report`'s Insights section is the `Not answered` sentence.
- `drift` reports nothing.
- `git status --porcelain` is empty after both `retro` calls.

Behaviour check, behind the person's prompt, in a scratch repo set up by `tests/test_adoption.py`'s
fixture:
- Write a draft with one field missing: `retro-commit` refuses, names the question and field, and
  writes nothing.
- Fill the field: it commits, the report shows `### Speed: …`, and the draft is gone.

## Boundaries

- **Always:** answer every question or say `Not answered`; cite figures with their `n`; refuse a
  bad draft before writing anything.
- **Ask first:** the policy edit to AGENTS.md's *Retrospectives* paragraph (Contracts touched),
  approved with this spec.
- **Never:** run a host command for the insights, give an agent a host command's output, add a
  tool that writes to an agent, commit the draft, or let a host change the answer shape.

