---
id: 190
slug: retro-rating
kind: spec
created: 2026-11-20
updated: 2026-11-20
---

# 190 — The retrospective asks how working with the process felt · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Nits taken in: 2026-11-19-18

Assumptions checked in the code, before the list:

- 189 (retro-insights) has landed on this branch. `retro-commit` already reads a draft the skill writes after its yes (`insights_rel()`, `.sdlc/retros/<date>.insights.md`). It renders the draft into the report, never commits it, and removes it once the commit is made (`cmd_retro_commit()`). The rating uses the same path.
- The last retrospective's report is read back from its own commit by `_last_rows()`, through `indicators.report_rows()`, keyed by a table's exact header line. A new table with a header of its own is read back the same way.
- Metrics reads a dialog's answer as `_reply(chosen[0])`, the first non-empty value in the result's `toolUseResult.answers` (`metrics._answers()`, `metrics.py` around line 946). Line 430 accepts `any(... == "approve")`. A two-question dialog therefore keeps the approval readable only when the approval is the first question asked.
- `AskUserQuestion` takes 2–4 options per question. `test_every_gate_offers_two_to_four_answers` checks every backticked question in the WAIT section, so the rating scale has at most four points.
- `{{insights}}` is not in `TEMPLATE_READS` (`test_insights_is_not_a_template_read`), so a host override without it isn't `breaking`. The new placeholder follows that precedent.
- `templates/retro.md` is hashed in `.sdlc/setup.json` (`"retro.md": "sha256:…"`), so this change also runs `scripts/sdlc.py record`.

1. **R1. The WAIT asks the rating in its own dialog call, after the approval.** Step 5's `AskUserQuestion` call asks two questions. The approval comes first, its literal unchanged. The rating comes second, literally `How did working with the process feel since the last retrospective? Pick one, or type its number and a line in Other (4 smooth / 3 fine / 2 rough / 1 in the way)`. The skill keeps exactly one `WAIT` heading. The text fallback asks both questions in the same order. `test_the_retro_wait_asks_the_rating_second_in_its_dialog` (`tests/test_skills.py`) checks four things in Step 5: the rating literal, that both are asked "in one `AskUserQuestion` call", "the approval first", and that the rating "never approves". It fails if any of these is missing. The existing `test_writing_skills_carry_exactly_one_wait_gate`, `test_every_wait_asks_in_a_dialog` and `test_every_gate_offers_two_to_four_answers` still pass.
2. **R2. A missing rating is no rating, and the rating never decides the approval.** Step 5 says that only the approval's answer approves. A yes with the rating dismissed, empty or refused still approves, and no rating is recorded: never a default value. On `revise` or `no`, the rating is discarded and asked again with the next draft. The same skills test asserts the phrase "a dismissed or empty rating is no rating, never a default".
3. **R3. The skill writes the person's answer verbatim, only after the yes.** If the rating question got an answer, Step 6 `Write`s `.sdlc/retros/<today>.experience.md`, holding one line, `Answer: <the rating's answer exactly as chosen or typed>`. With no answer, it writes no file. The skill never parses or rewords the answer. `test_the_retro_wait_asks_the_rating_second_in_its_dialog` asserts that Step 6 names `.sdlc/retros/<today>.experience.md` and `Answer:`.
4. **R4. The script reads the rating and the line, and nothing else does.** `retro.experience_answer(text)` is pure and returns `(rating, line)`. Its rules:
   - A leading digit 1–4, not followed by another digit, is the rating.
   - The rest is the line, with leading spaces and `—`, `-`, `:`, `,` and `.` stripped. When the rest is only that number's option label (case-insensitive), there is no line.
   - Anything else gives no rating, and its whole text is the line.
   - Empty gives `(None, None)`.

   `test_an_experience_answer_reads_its_rating_and_line` (`tests/test_retro.py`, parametrized) covers these cases:

   | Answer | Result |
   |---|---|
   | `3 fine` | `(3, None)` |
   | `2 the reviews dragged` | `(2, "the reviews dragged")` |
   | `4 — quick this time` | `(4, "quick this time")` |
   | `5 great` | `(None, "5 great")` |
   | `12 things` | `(None, "12 things")` |
   | `the builds were slow` | `(None, "the builds were slow")` |
   | empty | `(None, None)` |
5. **R5. The committed report records both, under `## Experience`.** `retro-commit` reads the day's experience draft (`experience_rel()`) and renders it into `{{experience}}`. The section holds three things:
   - A table with header exactly `| Figure | Value | Last retrospective | Trend |` (`EXPERIENCE_HEAD`).
   - One row, `How working with the process felt (1 to 4)`, with the rating (or `—`), the last retrospective's rating (or `—`) and the trend.
   - Then `Their line: <line>`, or `No line given.`

   The commit's `paths` are still only the report, the direction doc, the register and the product doc. They never include the draft, which is removed once the commit is made. `test_retro_commit_renders_the_rating_and_removes_its_draft` fails if any of these happens: the row or line is missing, the draft is in `git show --name-only HEAD`, the draft is still on disk, or `git status --porcelain` isn't empty.
6. **R6. With no draft, the report says no rating was given.** The row's Value is `—`, its Trend is `unknown`, and the line reads `NOT_RATED` (`Not rated: the person gave no rating at this retrospective's question.`), never an empty section. `test_the_experience_says_not_rated_without_a_draft` asserts this for `retro-commit` and for `retro --report`.
7. **R7. A malformed draft is refused before anything is written.** A draft with no `Answer:` line is a refusal, `experience: <path> has no Answer: line`, raised beside the other refusals. Nothing is written or committed and the tree is left as it was. `test_retro_commit_refuses_an_experience_draft_without_an_answer` asserts the refusal and `_state(root) == before`.
8. **R8. A failed commit leaves the draft for a rerun.** A `git commit` refused by a hook leaves the draft in place, removes the report, and leaves HEAD unmoved. The rerun then commits and removes the draft. `test_a_failed_commit_leaves_the_experience_draft_for_a_rerun`.
9. **R9. The next retrospective reads the last rating back as a trend.** `_last_rows()` also returns `experience`: the last report's rating and its line, read from that report at its own commit. The rating comes from the `EXPERIENCE_HEAD` table by `report_rows()`, and the line from `## Experience`'s `Their line: ` line. `retro` prints this as `experience: {last: {date, rating, line}}`. `last` is null when there was no earlier retrospective, or when its report has no such table. A rating of `—` is `rating: null`. The report's Trend is computed from this rating against `last.rating`: `up`, `down`, `flat`, or `unknown` when either is missing. Unlike `_trend()`, there's no minimum count, because the figure is one person's single answer. `test_the_next_retro_reads_the_last_rating_back` commits two retrospectives, the first rated 2 and the second 3. It asserts the second report's row reads `2 | up`, and that `retro`'s `experience.last` is the second's rating and line.
10. **R10. The template gains the section, and an older override still renders.** `templates/retro.md` gains `## Experience` / `{{experience}}` after `## Insights`, and its `>` note says the section exists and is read back. `{{experience}}` is not added to `TEMPLATE_READS`. The tests:
    - `test_experience_is_not_a_template_read` fails if `{{experience}}` is added there.
    - `test_an_override_without_experience_still_renders` renders the 189 template (no `## Experience`) and `retro-commit` takes a draft all the same.
    - `test_an_override_without_insights_still_renders`' `SECTIONS` gains `Experience`.
11. **R11. The approval is still read from the two-answer dialog.** `test_a_two_question_gate_reads_its_approval_from_the_first_answer` (`tests/test_metrics.py`) builds a transcript `AskUserQuestion` result whose `toolUseResult.answers` holds the approval `yes` followed by the rating `3 fine`. It asserts one `answer` event whose reply is `approve`. A second case, answers `revise` then `4 smooth`, gives `revise`. No metrics code changes.
12. **R12. The skill reads the last rating where the direction is set.** The changes to the skill:
    - Step 0 names `experience` (the last retrospective's rating and line, null with none).
    - Step 2's Direction pass weighs it beside the figures, as a hint from one person, never a finding on its own.
    - Step 7 says whether a rating was recorded.

    `test_the_retro_skill_reads_the_last_rating` asserts `` `experience` `` in Step 0, `` `experience` `` in Step 2's Direction pass, and a rating mention in Step 7.
13. **R13. The docs say it.** These docs change:
    - `docs/REFERENCE.md` *Retrospectives* names `experience`, the scale (1 to 4), `.sdlc/retros/<date>.experience.md` and that it is never committed.
    - The *Retrospectives* note on what `retro-commit` holds still names four files.
    - `docs/PROCESS.md`'s retro `writes:` node names the experience draft beside the insights draft.

    `test_reference_names_the_rating_and_its_draft` asserts each phrase in *Retrospectives*. `tests/test_feature_map.py` still passes.
14. **R14 (nit 2026-11-19-18). The aim keys are pinned in the docs.** `test_reference_and_step_0_name_the_aim_keys` (`tests/test_retro.py`) asserts that `` `work_mix` ``, `` `time_to_users` `` and `` `follow_through` `` appear in `docs/REFERENCE.md`'s *Retrospectives* section and in `skills/retro/SKILL.md`'s Step 0. It is modelled on `test_reference_names_test_times_and_its_format`, and fails if either doc drops one of them.
15. **R15. Setup's record matches what ships.** `scripts/sdlc.py record` is run from this change's checkout after the template edit, so `sdlc.py drift` reports nothing here. If it doesn't, `./check.sh` fails.

## Design

**The dialog (`skills/retro/SKILL.md`, Step 5).** One `AskUserQuestion` call holds two questions. The approval's question and options are unchanged and come first. The rating question comes second, `header` `retro`, options `4 smooth`, `3 fine`, `2 rough`, `1 in the way`, in that order. A person who wants to say more types in Other, as the question tells them: "3, the reviews waited on me". Putting the approval first is what keeps `metrics._answers()[0]` the approval (R11). The skill's text says "the approval first" so a later edit can't reorder them silently. The fallback with no dialog asks both texts, approval first, and stops. That is already how the WAIT behaves, so a fallback session records no rating unless the person types one with their yes. In that case the skill writes what they typed after `yes` as the answer.

**The draft (Step 6).** After the yes, the skill writes `Answer: <verbatim>` to `.sdlc/retros/<today>.experience.md`, alongside the insights draft. It writes this before `retro-commit`, and only when the rating question got an answer. The skill does no parsing: reading a number out of free text is mechanical, so it lives in the script (`experience_answer()`, R4).

**The script (`scripts/retro.py`)**, next to the insights code:

- `experience_rel(today)`, beside `insights_rel()`.
- `EXPERIENCE_HEAD`, `EXPERIENCE_FIGURE`, `EXPERIENCE_LABELS = {4: "smooth", 3: "fine", 2: "rough", 1: "in the way"}` and `NOT_RATED`.
- `experience_answer(text)`, which is pure (R4).
- `_draft_experience(home, day)`, which returns `(answer | None, problems)`. The answer is None with no file. The problems are R7's.
- `_experience_text(answer, last)`, which renders the section (R5, R6). The line is shown with its whitespace collapsed, outside the table, so a `|` in it can't break the read-back.
- `_experience_trend(rating, last_rating)` (R9).
- `_last_rows()` gains the `experience` key. It reads the table with `indicators.report_rows(text, EXPERIENCE_HEAD, (0,), 1)`, and reads the line by its `Their line: ` prefix inside `## Experience`.
- `render_report()` takes `experience=` beside `insights=` and fills `{{experience}}`. A template without the placeholder renders as before.
- `retro_report()` passes `experience` through.
- `cmd_retro()` with `--report` previews a draft that's there, as it does for insights.
- `cmd_retro_commit()` handles the draft as it handles the insights one:
  - It drops the draft from `changed` before the `stray` check.
  - It adds the draft's problems to `refusals`.
  - It renders the draft into the report.
  - It unlinks the draft only after `commit` succeeds, and appends `"experience draft removed"` to `done`.
- `retro()`'s output gains `experience: {"last": …}`, from the `_last_rows()` call `report_figures()` already makes, so the history isn't read twice.

**Edge cases.**

- A rating with no line: `Their line:` reads `No line given.`
- A line with no rating: the row shows `—` and the line is kept. The person said something but gave no number, and none is assumed.
- The last report predates this change: `last` is null and the trend is `unknown`.
- A host override without the section: nothing is shown, and the next retrospective reads `last: null`.
- The draft is left over from an earlier day: it isn't today's path, so it isn't read. It shows up as a stray file and is refused, as a stale insights draft is today.

**Not changed:** the scorecard and its pillar rows, the insight bundles, `metrics.py`, and any `allowed-tools` (Step 6 already has `Write`).

## Contracts touched

- **Exactly one WAIT heading, asked in a dialog, 2–4 answers, only a chosen yes approves** (`tests/test_skills.py`). There is still one heading. Both questions sit in the one dialog the WAIT already asks, and each offers four answers or fewer. The rating's options contain no `yes`, and the skill says the rating never approves (R1, R2).
- **"Metrics read a dialog's answer in the WAIT's span as the approval."** The design relies on `toolUseResult.answers` keeping the order the questions were asked in, so `chosen[0]` is the approval. JSON objects keep insertion order in Python's reader, and the harness builds the dict from the questions list. But REVIEW.md's *A transcript's shape assumed, not read* applies here. R11's test is built from the shape `_answers()` reads, and no recorded two-question transcript exists in the tests yet. **Before ship, someone should look at one real retro transcript with a two-question dialog and confirm the order.** If the harness doesn't keep the order, the fix is a metrics change (pick the answer that reads as a reply), which has its own review weight.
- **`retro-commit` holds the direction doc, the register, the product doc and the report, nothing else** (AGENTS.md, *Retrospectives*; the intent's constraint). The experience draft is read and never committed, exactly as the insights draft is (R5).
- **`retro` is read-only but for its report.** `experience` is read from history through `_last_rows()`. `retro --report` previews and writes nothing (R6).
- **`breaking` is only what the plugin would now misread; `TEMPLATE_READS` gets an entry for a new read heading.** The script tolerates a template without `{{experience}}`, so it gets no entry and no `RETIRED_KEYS` or `deprecations.toml` entry (R10). Reading the rating back needs the table only in reports this plugin wrote.
- **A change that edits what setup hashes runs `sdlc.py record`** (R15).
- **Windows.** The script writes no new file but the report, which already passes `newline="\n"`, and paths are built with `as_posix()`-safe string joins, as `insights_rel()` builds them.
- **Logic a permission rule must cover goes in the script.** The skill only writes the answer verbatim. Parsing it is `experience_answer()`'s job.
- **A doc's claim the change made false** (REVIEW.md). REFERENCE.md *Retrospectives*, PROCESS.md's retro node and the template's note are updated (R13, R10). AGENTS.md's *Retrospectives* paragraph says `retro-commit` holds four files and reads "the day's insights draft". It should also name the experience draft in the same sentence. That is a one-clause doc edit, not a policy change.

No invariant needs to move.

## Alternatives rejected

- **A dialog of its own before the WAIT.** This adds a stop and a question that metrics counts outside the gate. It also asks for a rating of a retrospective the person may then send back to revise.
- **A dialog after the yes.** Same cost: metrics would count it as a question after the gate. It also sits outside the WAIT's span, where the intent puts the rating.
- **A 1–5 or 0–10 scale.** `AskUserQuestion` offers at most four options, and `test_every_gate_offers_two_to_four_answers` enforces this. A typed-only scale would make every answer go through Other. Four points also has no neutral middle to settle on.
- **Words only (smooth / rough), no number.** The intent asks for a trend, which needs an order. The numbers carry it, and the words give each one a meaning.
- **A third dialog question for the line.** Every question needs 2–4 options, so a free-text-only question doesn't fit. Typing the number and a line in Other keeps it to one question.
- **Passing the rating as `retro-commit --rating 3 --line "…"`.** The person's free text would go through a shell command line, with its quoting and `$(…)` hazards. A file the skill `Write`s carries it untouched.
- **A `## Experience` block in the insights draft.** `insight_answers()` refuses any title that isn't a question. A rating can also exist without insights, and the reverse.
- **A row in the scorecard.** The scorecard is computed in Step 0, before the person answers. Adding the row would make the JSON and the report disagree, against `report_figures()`'s "the two never disagree".
- **Giving `experience` to an `sdlc:insight` agent.** One person's line isn't a figure for an agent to synthesize. The direction pass reads it as a hint (R12). This can be a later seed if it proves worth it.
- **The skill parsing "3, the reviews dragged" itself.** Parsing is deterministic, so it goes in the script, where a test pins it.

## Verification

```bash
uv run --group dev pytest -q tests/test_retro.py tests/test_skills.py tests/test_metrics.py tests/test_feature_map.py tests/test_defaults.py
uv run --quiet --script scripts/sdlc.py drift      # healthy: reports nothing for this repo
./check.sh                                          # healthy: ruff clean, format clean, all tests pass, plugin validate --strict OK
```

What healthy output looks like:

- The new tests pass: R1–R14's named tests, plus the updated `SECTIONS`.
- `test_writing_skills_carry_exactly_one_wait_gate[sdlc:retro]`, `test_every_wait_asks_in_a_dialog[sdlc:retro]` and `test_every_gate_offers_two_to_four_answers[sdlc:retro]` still pass.
- In a scratch repo with two retrospectives (as in R9's test), `uv run --quiet --script scripts/sdlc.py retro --report` shows `## Experience` with the row and `Their line:`.
- `sdlc.py retro | jq .experience` shows `last` with the previous rating and line.

By hand, before ship: run `/sdlc:retro` once in a scratch host, or read a recorded transcript. Answer `yes` with the rating `3 fine`, and confirm two things. First, the session's `Close`-style metrics read that dialog's answer as `approve`. Second, `toolUseResult.answers` lists the approval first (see *Contracts touched*).

Boundaries:

- **Always:** only the approval approves; the answer is recorded verbatim and parsed by the script; the draft is never committed.
- **Ask first:** any change to the four files `retro-commit` commits, or to how metrics reads a dialog.
- **Never:** a default rating, a rating that changes the approval, a second WAIT heading, or a template read that makes old overrides `breaking`.

