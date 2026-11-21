---
id: 210
slug: wait-previews
kind: spec
created: 2026-11-21
updated: 2026-11-21
---

# 210 — Each WAIT shows its draft in the dialog's preview · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Nits taken in: none.

"The gated skills" means the 20 in `tests/test_skills.py`'s `GATED`: the intent's 19, plus
`sdlc:update`, which the intent's list left out but which has a WAIT all the same.

1. **R1. Every WAIT says what its preview holds.** In each gated skill's WAIT step, the shared
   `Ask it with AskUserQuestion` paragraph goes on to say ``…, `header` the skill's name, and
   <what this yes writes> as the `preview` of each yes option``. `<what>` is specific to the skill
   (R9 lists each one). `test_every_wait_asks_in_a_dialog` asserts that the sentence is there and
   that `<what>` is not empty. If a WAIT lacks the sentence, or names nothing in it, the test fails
   with that WAIT's name.
2. **R2. The text fallback keeps the draft above the question.** The fallback sentence in every
   WAIT reads `If the tool is unavailable or refused, ask the same text, answers in parentheses,
   right after what the preview holds, and stop.` `test_every_wait_asks_in_a_dialog` asserts
   `right after what the preview holds`. Land's current `right after `shown`` becomes this
   sentence too.
3. **R3. A long preview is cut to the part that decides the yes.** Every WAIT's paragraph also
   says: `A preview past 40 lines keeps its approving part and ends "… <k> more lines in <path>",
   or "… <k> more lines, shown above" when no file holds them yet.`
   `test_every_wait_asks_in_a_dialog` asserts the phrase `keeps its approving part`.
4. **R4. One cut rule in each script.** `sdlc.py` and `factory.py` each get
   `PREVIEW_LINES = 40` and a `_preview_cut(text, path)` that keeps the first `PREVIEW_LINES`
   lines and adds the closing line R3 names. `factory.py` does not import `sdlc.py`, so it holds a
   copy, and a test in `tests/test_modules.py` pins the two copies equal. A test feeds each copy 41
   lines and fails unless it gets 40 lines plus `… 1 more lines in <path>` (or
   `… 1 more line in <path>` if the plan settles the singular). A test feeds each 40 lines and
   fails if anything is added.
5. **R5. The factory's spec draft carries its own preview.** When `factory.py agent --task spec`
   (and `--recheck`, `--revise`) files the spec-writer's reply, its JSON gains `preview`: the
   draft's `## Requirements` section, taken from `runs/spec-draft.md` and cut by R4 against that
   path. A test in `tests/test_factory_agent.py` fails if `preview` is missing, holds anything
   outside the Requirements section, or misses the cut on a draft whose Requirements run longer
   than 40 lines.
6. **R6. `start --for build` renders the run it approves.** Its JSON gains `preview`, set only when
   `question` is set:
   - the gate command, or `no gate configured`
   - each role with its model at each depth (`models_at`)
   - the rounds at each depth, and `max_runs`
   - with `restart`: the archive the old decision goes to, and the round the run restarts from
   - with `upgraded`: the Requirements of the `spec.md` that `upgrade` wrote

   `start --for spec` gets `preview: null`, because the draft doesn't exist yet when Step 0 runs.
   Tests in `tests/test_factory_gate.py` (or wherever `start`'s tests live, which the plan names)
   fail if any of these is missing, and fail if a refused `start` gives a preview.
7. **R7. `preflight <NNN> --preview` renders ship's half.** It takes the same clause flags as
   `--question`. It prints plain text:
   - each finding in `findings.md` with its id, rank and disposition
   - the paths the change's diff touches against its merge base with `git.base`
   - the line `.sdlc/work/NNN-<slug>/ stamped shipped`, with the path built from `work_rel()`

   It cuts by R4, writes nothing, and exits 1 with the same refusal `--question` gives on a bad
   `findings.md`. `--question`'s output stays the same byte for byte: the existing ship-question
   tests stay green unchanged. A new test fails if `--preview` leaves out a finding or a path, or
   if `git status` differs after it runs.
8. **R8. The skills ask the script's preview as printed.**
   - Ship's preview is the commit message exactly as it will be committed, then
     `preflight --preview`'s output as printed.
   - The factory's spec skill uses `agent`'s `preview`.
   - The factory's build skill uses `agent`'s `preview`, then `start`'s, when there is a spec
     draft, and `start`'s alone otherwise.
   - Land keeps `land-check`'s `shown`.

   A test fails if any of these four skills' WAIT doesn't name its script's output (`` preflight
   <NNN> --preview ``, `` `agent`'s `preview` ``, `` `start`'s `preview` ``, `` `land-check`'s
   `shown` ``) as what the preview holds.
9. **R9. Each skill-worded preview names what that yes writes.** These skills word their own
   preview from what their Show step already drafted:

   | Skill | What its preview holds |
   |---|---|
   | idea, bug | the entry exactly as it will be appended. For an edit, the entry as it becomes; for a retirement, the entry and its reason; for a retag, the heading and lines as they become; for `--themes`, the table. A plugin bug's preview stays the rendered body, as 209 made it. |
   | triage | the entries, then each `Issue:` and `closes:` line, then each needs-info question, as it will be posted |
   | intent | the frontmatter lines shown, then `## Problem` and `## Outcome` |
   | spec (core) | `## Requirements` |
   | close | the commit `main` moves to, then the paths `deletes` lists, the commits the push sends, and the `cleanup` command, each when present |
   | drop | the `## Dropped` section and the paths committed |
   | setup | each path, and for an edit its diff |
   | release | the notes exactly as they will read, the files, the tag |
   | publish | the commits in `unpushed.ahead`, the tag, and the command as it will run |
   | retro | the status changes, then each new seed's heading line |
   | uninstall | every path in `remove` and every edit in `edit` |
   | update | the `claude plugin` commands, numbered, with `cwd` |
   | factory eval | the bugs, by id and title, with the reviewers |
   | factory review | the paths with `why` |
   | factory decide | each answer as Step 2 shows it |

   `tests/test_skills.py` pins this table: for each skill, a key word from its row (`entry`,
   `Requirements`, `notes`, and so on) has to appear in the sentence R1 checks. The test fails if a
   row's key word is missing.
10. **R10. Retro's rating has no preview.** Retro asks two questions in one call. Its WAIT says the
    preview goes on the approval's `yes` only, and that the rating question carries none. A test
    fails if the WAIT doesn't say `The rating has no preview`.
11. **R11. No question or answer changes.** Every literal question the WAITs ask (each backticked
    `…? (…)` in `GATE_QUESTION_RE`'s sense) is the same before and after the change. The
    Verification diff below shows it. The existing tests that read the questions and answers stay
    green without being edited: `test_every_gate_offers_two_to_four_answers`,
    `test_publish_offers_no_first`, `test_bug_shows_the_upstream_body_before_its_wait`, and
    `tests/test_metrics.py`.
12. **R12. Nothing is written before the yes.** No skill writes a file to build its preview, and
    neither `--preview` nor the new JSON keys write anything. The R7 and R5 tests check
    `git status --porcelain` before and after. Beyond what `agent --task spec` already writes, any
    difference fails them.
13. **R13. The docs say it.** These docs say the yes options carry the draft as their `preview`,
    cut by R3:
    - `AGENTS.md`'s *Skills* invariant bullet (this widens a policy invariant; see Contracts
      touched)
    - `docs/CONTRIBUTING.md`'s **One approval per writing skill** paragraph

    The `test_every_wait_asks_in_a_dialog` docstring says the same. The review's *A doc's claim
    the change made false* check covers these, and Verification greps each one.

## Design

**Assumptions checked in the code.**
- `GATED` lists 20 skills, `sdlc:update` included.
- Every WAIT has the same `Ask it with AskUserQuestion: …` paragraph, which
  `test_every_wait_asks_in_a_dialog` reads through `_wait_section()`.
- Two WAITs already set a preview:
  - land: `land-check`'s `shown`, from `land_shown()` in `landing.py`
  - bug: the upstream body, from 209
- `preflight --question` prints plain text. The skill asks exactly what it prints, and
  `_own_script()`'s passthrough sends its `ran` line to stderr for any `preflight` call
  (`sdlc.py` around line 5392), so a new non-JSON `--preview` takes the same path unchanged.
- Ship's `allowed-tools` has `preflight *`, and the factory's build and spec skills have
  `start *` and `agent *`, so no new `Bash(...)` rule is needed.
- `start --for spec` and `--for build` run in Step 0, before the spec-writer drafts. The draft's
  text first exists when `agent --task spec` files it (`factory.py` around line 4631, which writes
  `runs/spec-draft.md` and `runs/spec-questions.md`).
- Ship's commit message exists only in the session until `git commit -m`. It is never on disk.

**The pieces.**

1. **The shared paragraph** (R1–R3). Each WAIT's existing paragraph gains three things: the
   `and <what> as the preview of each yes option` clause, the cut sentence, and `right after what
   the preview holds` in the fallback. Only `<what>` differs between skills (R9's table). Every
   other word is the same in all 20, so one test can read it, as it reads the rest of the
   paragraph today. Each skill's WAIT stays in its `SKILL.md`. Setup's drafting lives in
   `drafts.md`, but its WAIT, and so the sentence, is in `SKILL.md`.
2. **Where each preview's text comes from.**
   - Prose the model drafts (an entry, an intent, a spec, a commit message, a `## Dropped`
     section, setup's files): the skill puts the same text it showed in the message into the
     preview. Nothing new is rendered, because `sdlc.py` never writes artifact prose (AGENTS.md,
     *Mechanism vs. judgment*).
   - Facts a script already holds: the script renders them (R5–R7), and the skill asks them as
     printed.
   - Ship mixes both: the message (the model's) comes first, then `preflight --preview` (the
     script's).
3. **`factory.py`'s renderers.**
   - `_spec_preview(folder)` reads `runs/spec-draft.md`, takes the text from `## Requirements` to
     the next `## `, and cuts it with `_preview_cut()`. The reply-filing step adds it to its JSON
     as `preview`.
   - `build_preview(out, check)` sits beside `build_question()`. It builds from the same `out`
     (`models_at`, `rounds`, `light`, `max_runs`, `restart`, `upgraded`) and from the same
     base-branch check that `_base_check()` gives the question, so the question and the preview
     can't disagree.
   - `cmd_start` sets `out["preview"]` next to `out["question"]`.
4. **`sdlc.py`'s renderer.** `cli_preflight` gets `--preview`. It shares `cmd_ship_question()`'s
   loading (findings, refusals on `problems`) and prints:
   - one line per finding, `F<n> <rank> → <disposition>`, from `findings_entries()`
   - the diff's paths, from the path list `_risk_report()` already computes against the merge
     base, so no second `git diff` call reads the paths a different way
   - the stamp line

   Using `--question` and `--preview` together is refused, with a message, as the clause flags are
   refused without `--question` today.
5. **The cut.** Both scripts get `_preview_cut(text, path)`. A skill-worded preview follows the
   same rule in prose (R3). In "the approving part", *approving* means the part a no would change:
   for a spec, the requirements; for an intent, Problem and Outcome. R9's table names it for each
   skill, so the model doesn't have to judge it.

**Edge cases.**
- If `findings.md` doesn't parse, `--preview` refuses as `--question` does.
- A clear factory batch approves itself (`by auto`) and asks nothing, so it gets no preview.
- A refused `start` has `question: null` and `preview: null`.
- A `--recheck` or `--revise` draft gives a fresh `preview` from the new draft.
- A 209 upstream bug's preview is still the rendered body (the upstream form is unchanged).
- Retro's rating carries none (R10).

**Boundaries.**
- *Always:* the preview holds what the yes writes, the literal question is unchanged, and the
  scripts that render a preview write nothing.
- *Ask first:* the 40-line limit (left open below), and widening the AGENTS.md invariant (approved
  with this spec).
- *Never:* a new write before a WAIT, a draft saved to a file only so the preview can name it, a
  changed question or answer, a preview on a `no` option, or a new renderer for a skill whose
  question no script words today.

## Contracts touched

- **Skills: one WAIT heading, 2–4 answers, publish's `no` first, only a chosen yes approves**
  (`tests/test_skills.py`). The design adds no heading or option, and approval works as before.
  The preview is a field on options that already exist.
- **Metrics read a dialog's answer in the WAIT's span as the approval.** The question text and
  option labels stay the same (R11). `metrics.py` reads `question` and the answer, never
  `preview`, so nothing it counts moves.
- **⚠ The *Skills* invariant in AGENTS.md is widened.** Today it says a WAIT "asks its literal
  question in an `AskUserQuestion` dialog". After this change, the yes options also carry the draft
  as their preview, and the test enforces it. This is a policy edit (R13), and approving this spec
  approves it. It is not a side effect.
- **Narrow `allowed-tools`.** No new command shape. `preflight <NNN> --preview` matches
  `preflight *`, and `agent` and `start` are already listed. Bash blocks stay plain.
- **Mechanism vs. judgment** (`sdlc.py` never writes artifact prose). The scripts render only
  facts they already hold. The commit message, the entries and the drafts stay the model's.
- **`factory.py` never imports `sdlc.py`.** `PREVIEW_LINES` and `_preview_cut()` are copied into
  the factory, and the copies are pinned in `tests/test_modules.py`, as the factory's other copies
  are.
- **Writes before a WAIT (the six).** None is added. `agent --task spec` writes the draft files it
  already writes. `--preview` and the new JSON keys write nothing (R12).
- **`_own_script()` passthrough.** The `ran` line goes to stderr for every `preflight` call, so
  `--preview`'s output stays clean to paste.
- **The scripts run on Windows.** There is no new subprocess. Any path printed is `as_posix()`
  (the paths come from `_risk_report()`, which is already POSIX), and nothing is written.
- **`defaults/` and `templates/` untouched**, so there is no `sdlc.py record` and no `drift`.
- **The skills' cases (`evals/`).** The cases check that a skill wrote nothing before it asked
  and ended at its own question. The question doesn't change, so no fixture or grader should move.
  `tests/test_evals.py` (`vet --strict` on each fixture) stays green.
- **Nothing about a project.** Test data uses neutral entries and changes (`reopen-drafts`).

## Alternatives rejected

- **The script renders every preview.** The intent, the entries and the commit message are prose
  the model drafts, and `sdlc.py` never writes artifact prose. The script could only see them if
  they were written to disk before the yes, which would be a seventh write before a WAIT.
- **Write each draft to a file before the WAIT, so the preview can just name it.** This breaks
  "nothing is written before the yes", and a preview that names a file still leaves the text
  unseen.
- **Put the preview into `preflight --question`'s output.** The skill asks exactly what it prints,
  and the passthrough assumes nothing comes after it. Mixing the two would make the skill split
  them, which is how a question gets reworded. A separate `--preview` keeps both outputs whole.
- **Put the draft in the question text.** That changes the literal question metrics read, makes
  the dialog's question unreadable, and still has no place for a long draft.
- **A preview on every option, `no` included.** `no` writes nothing, so it has nothing to show.
  Land already shows its preview on the yes options alone.
- **Exempt WAITs that have "nothing to preview".** Every one of the 20 writes or runs something
  nameable: a retirement writes an entry's removal and its reason, and publish pushes named
  commits. An exemption would be the gap this change closes.
- **A test that the preview was actually shown at runtime.** The gate is offline. Only a
  transcript shows what the dialog held, which makes it an eval case (a paid run). The suite could
  add one later; this change doesn't.
- **Render the spec draft's preview in `start --for spec`.** `start` runs before the draft exists.
  The command that files the draft is the first place its text is on disk.

## Verification

```bash
./check.sh
```

Healthy output: ruff clean, `ruff format --check` clean, every pytest passing, and
`claude plugin validate --strict` OK.

```bash
uv run --group dev pytest -q tests/test_skills.py -k "wait or gate or preview or publish or bug_shows"
uv run --group dev pytest -q tests/test_modules.py tests/test_factory_agent.py tests/test_factory_gate.py
uv run --group dev pytest -q -k "ship_question or preflight"
```

Healthy output: all pass, and the new tests are listed under their requirement's name, for example
`test_every_wait_names_its_preview`, `test_preview_cut_keeps_forty_lines`,
`test_spec_agent_reply_previews_requirements`, `test_start_build_previews_the_run` and
`test_preflight_preview_writes_nothing`.

R11, no question changed:

```bash
git diff "$(git merge-base HEAD main)" -- skills plugins/factory/skills | grep -E '^[-+]> `'
```

Healthy output: nothing. No quoted question line was added or removed. (`main` here is this
repo's `git.base`.)

R13, the docs:

```bash
grep -n "preview" AGENTS.md docs/CONTRIBUTING.md
```

Healthy output: the *Skills* invariant bullet and **One approval per writing skill** each name the
yes options' `preview`.

Behaviour, by hand, in a session with `--plugin-dir <path-to-clone>`:
- Run `/sdlc:idea` on a neutral idea, and say no. The dialog's `yes` option shows the entry's
  `## [<id>] [idea] …` block in its preview, and nothing is written.
- Run `/sdlc:ship` on a scratch change up to its WAIT. The `yes` preview opens with the commit
  message, then the findings, paths and stamp line from `preflight --preview`.

